"""
Microsoft Fabric client for Lakehouse and Warehouse operations
"""
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
import struct
import pyodbc
from azure.identity import AzureCliCredential

from .config import fabric_config
from .models import OutageEvent, Policy, Claim, Payout, WeatherData


class FabricClient:
    """Client for Microsoft Fabric operations using SQLAlchemy"""
    
    def __init__(self, server: Optional[str] = None, database: Optional[str] = None):
        """
        Initialize Fabric client with Azure CLI credential
        
        Args:
            server: SQL server address (hostname)
            database: Database name
        """
        self.server = server or os.getenv('FABRIC_WAREHOUSE_SERVER', 
                                         'cbjhakaeu65uhjfcys3uzqf7qq-h3cujqwtlbkubdoirr43ycwuwa.datawarehouse.fabric.microsoft.com')
        self.database = database or os.getenv('FABRIC_DATABASE', 'parametric_insurance_warehouse')
        self.credential = AzureCliCredential()
        self.lakehouse_name = fabric_config.lakehouse_name
        self.warehouse_name = fabric_config.warehouse_name
        self._engine: Optional[Engine] = None
    
    def _get_token_struct(self) -> bytes:
        """Get access token in the format required by pyodbc"""
        token = self.credential.get_token("https://database.windows.net/.default")
        token_bytes = token.token.encode("UTF-16-LE")
        return struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    
    def _create_connection(self):
        """Create a pyodbc connection with token authentication"""
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:{self.server},1433;"
            f"Database={self.database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        # SQL_COPT_SS_ACCESS_TOKEN = 1256
        return pyodbc.connect(connection_string, attrs_before={1256: self._get_token_struct()})
    
    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine with Azure CLI credential authentication"""
        if self._engine is None:
            # Create engine with a creator function that handles token auth
            self._engine = create_engine(
                "mssql+pyodbc://",
                creator=self._create_connection,
                pool_pre_ping=True,
                pool_recycle=3600  # Refresh connections every hour
            )
        return self._engine
    
    def get_connection(self):
        """Get database connection from engine (for backwards compatibility)"""
        return self.get_engine().connect()
    
    # Outage Events Operations
    
    def insert_outage_event(self, event: OutageEvent) -> bool:
        """Insert outage event into lakehouse"""
        try:
            with self.get_engine().begin() as conn:
                query = text(f"""
                INSERT INTO {fabric_config.TABLE_OUTAGE_EVENTS} 
                (event_id, utility_name, zip_code, latitude, longitude, 
                 affected_customers, outage_start, outage_end, duration_minutes,
                 status, cause, reported_cause, data_source, last_updated)
                VALUES (:event_id, :utility_name, :zip_code, :latitude, :longitude,
                        :affected_customers, :outage_start, :outage_end, :duration_minutes,
                        :status, :cause, :reported_cause, :data_source, :last_updated)
                """)
                
                conn.execute(query, {
                    "event_id": event.event_id,
                    "utility_name": event.utility_name,
                    "zip_code": event.location.zip_code,
                    "latitude": event.location.latitude,
                    "longitude": event.location.longitude,
                    "affected_customers": event.affected_customers,
                    "outage_start": event.outage_start,
                    "outage_end": event.outage_end,
                    "duration_minutes": event.duration_minutes,
                    "status": event.status.value,
                    "cause": event.cause,
                    "reported_cause": event.reported_cause,
                    "data_source": event.data_source,
                    "last_updated": event.last_updated or datetime.utcnow()
                })
                return True
                
        except Exception as e:
            print(f"Error inserting outage event: {e}")
            return False
    
    def update_outage_event(self, event_id: str, **kwargs) -> bool:
        """Update outage event"""
        try:
            with self.get_engine().begin() as conn:
                set_clause = ", ".join([f"{k} = :{k}" for k in kwargs.keys()])
                query = text(f"""
                UPDATE {fabric_config.TABLE_OUTAGE_EVENTS}
                SET {set_clause}, last_updated = GETUTCDATE()
                WHERE event_id = :event_id
                """)
                
                params = {**kwargs, "event_id": event_id}
                conn.execute(query, params)
                return True
                
        except Exception as e:
            print(f"Error updating outage event: {e}")
            return False
    
    def get_outage_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get outage event by ID"""
        try:
            query = text(f"""
            SELECT * FROM {fabric_config.TABLE_OUTAGE_EVENTS}
            WHERE event_id = :event_id
            """)
            df = pd.read_sql(query, self.get_engine(), params={"event_id": event_id})
            
            if len(df) == 0:
                return None
            
            return df.iloc[0].to_dict()
                
        except Exception as e:
            print(f"Error getting outage event: {e}")
            return None
    
    def get_active_outages(self) -> List[Dict[str, Any]]:
        """Get all active outages"""
        try:
            query = text(f"""
            SELECT * FROM {fabric_config.TABLE_OUTAGE_EVENTS}
            WHERE status = 'active'
            ORDER BY outage_start DESC
            """)
            df = pd.read_sql(query, self.get_engine())
            return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting active outages: {e}")
            return []
    
    # Policy Operations
    
    def get_policies_in_zip(self, zip_code: str) -> List[Dict[str, Any]]:
        """Get all active policies in a ZIP code"""
        try:
            query = text(f"""
            SELECT * FROM {fabric_config.TABLE_POLICIES}
            WHERE zip_code = :zip_code AND status = 'active'
            """)
            df = pd.read_sql(query, self.get_engine(), params={"zip_code": zip_code})
            return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting policies: {e}")
            return []
    
    def get_policies_near_location(
        self, 
        latitude: float, 
        longitude: float, 
        radius_miles: float = 10
    ) -> List[Dict[str, Any]]:
        """Get policies within radius of location"""
        try:
            # Using Haversine formula
            query = text(f"""
            SELECT *,
                (3959 * acos(
                    cos(radians(:lat1)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(:lon)) + 
                    sin(radians(:lat2)) * sin(radians(latitude))
                )) AS distance_miles
            FROM {fabric_config.TABLE_POLICIES}
            WHERE status = 'active'
            HAVING distance_miles <= :radius
            ORDER BY distance_miles
            """)
            
            df = pd.read_sql(
                query, 
                self.get_engine(), 
                params={"lat1": latitude, "lon": longitude, "lat2": latitude, "radius": radius_miles}
            )
            return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting nearby policies: {e}")
            return []
    
    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Get policy by ID"""
        try:
            query = text(f"""
            SELECT * FROM {fabric_config.TABLE_POLICIES}
            WHERE policy_id = :policy_id
            """)
            df = pd.read_sql(query, self.get_engine(), params={"policy_id": policy_id})
            
            if len(df) == 0:
                return None
            
            return df.iloc[0].to_dict()
                
        except Exception as e:
            print(f"Error getting policy: {e}")
            return None
    
    # Claim Operations
    
    def insert_claim(self, claim: Claim) -> bool:
        """Insert new claim"""
        try:
            with self.get_engine().begin() as conn:
                query = text(f"""
                INSERT INTO {fabric_config.TABLE_CLAIMS}
                (claim_id, policy_id, outage_event_id, status, filed_at,
                 payout_amount, ai_confidence_score, ai_reasoning, fraud_flags)
                VALUES (:claim_id, :policy_id, :outage_event_id, :status, :filed_at,
                        :payout_amount, :ai_confidence_score, :ai_reasoning, :fraud_flags)
                """)
                
                conn.execute(query, {
                    "claim_id": claim.claim_id,
                    "policy_id": claim.policy_id,
                    "outage_event_id": claim.outage_event_id,
                    "status": claim.status.value,
                    "filed_at": claim.filed_at,
                    "payout_amount": claim.payout_amount,
                    "ai_confidence_score": claim.ai_confidence_score,
                    "ai_reasoning": claim.ai_reasoning,
                    "fraud_flags": json.dumps(claim.fraud_flags) if claim.fraud_flags else None
                })
                return True
                
        except Exception as e:
            print(f"Error inserting claim: {e}")
            return False
    
    def update_claim(self, claim_id: str, **kwargs) -> bool:
        """Update claim"""
        try:
            with self.get_engine().begin() as conn:
                set_clause = ", ".join([f"{k} = :{k}" for k in kwargs.keys()])
                query = text(f"""
                UPDATE {fabric_config.TABLE_CLAIMS}
                SET {set_clause}
                WHERE claim_id = :claim_id
                """)
                
                params = {**kwargs, "claim_id": claim_id}
                conn.execute(query, params)
                return True
                
        except Exception as e:
            print(f"Error updating claim: {e}")
            return False
    
    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim by ID"""
        try:
            query = text(f"""
            SELECT * FROM {fabric_config.TABLE_CLAIMS}
            WHERE claim_id = :claim_id
            """)
            df = pd.read_sql(query, self.get_engine(), params={"claim_id": claim_id})
            
            if len(df) == 0:
                return None
            
            return df.iloc[0].to_dict()
                
        except Exception as e:
            print(f"Error getting claim: {e}")
            return None
    
    def get_policy_claims(
        self, 
        policy_id: str, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get recent claims for a policy"""
        try:
            query = text(f"""
            SELECT * FROM {fabric_config.TABLE_CLAIMS}
            WHERE policy_id = :policy_id
            AND filed_at >= DATEADD(day, -:days, GETUTCDATE())
            ORDER BY filed_at DESC
            """)
            
            df = pd.read_sql(query, self.get_engine(), params={"policy_id": policy_id, "days": days})
            return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting policy claims: {e}")
            return []
    
    # Payout Operations
    
    def insert_payout(self, payout: Payout) -> bool:
        """Insert payout record"""
        try:
            with self.get_engine().begin() as conn:
                query = text(f"""
                INSERT INTO {fabric_config.TABLE_PAYOUTS}
                (payout_id, claim_id, policy_id, amount, status, 
                 initiated_at, payment_method)
                VALUES (:payout_id, :claim_id, :policy_id, :amount, :status,
                        :initiated_at, :payment_method)
                """)
                
                conn.execute(query, {
                    "payout_id": payout.payout_id,
                    "claim_id": payout.claim_id,
                    "policy_id": payout.policy_id,
                    "amount": payout.amount,
                    "status": payout.status.value,
                    "initiated_at": payout.initiated_at,
                    "payment_method": payout.payment_method
                })
                return True
                
        except Exception as e:
            print(f"Error inserting payout: {e}")
            return False
    
    def update_payout(self, payout_id: str, **kwargs) -> bool:
        """Update payout record"""
        try:
            with self.get_engine().begin() as conn:
                set_clause = ", ".join([f"{k} = :{k}" for k in kwargs.keys()])
                query = text(f"""
                UPDATE {fabric_config.TABLE_PAYOUTS}
                SET {set_clause}
                WHERE payout_id = :payout_id
                """)
                
                params = {**kwargs, "payout_id": payout_id}
                conn.execute(query, params)
                return True
                
        except Exception as e:
            print(f"Error updating payout: {e}")
            return False
    
    # Weather Operations
    
    def insert_weather_data(self, weather: WeatherData) -> bool:
        """Insert weather data"""
        try:
            with self.get_engine().begin() as conn:
                query = text(f"""
                INSERT INTO {fabric_config.TABLE_WEATHER_DATA}
                (zip_code, latitude, longitude, timestamp, temperature_f,
                 wind_speed_mph, wind_gust_mph, precipitation_inches,
                 humidity_percent, conditions, severe_weather_alert,
                 alert_type, lightning_strikes)
                VALUES (:zip_code, :latitude, :longitude, :timestamp, :temperature_f,
                        :wind_speed_mph, :wind_gust_mph, :precipitation_inches,
                        :humidity_percent, :conditions, :severe_weather_alert,
                        :alert_type, :lightning_strikes)
                """)
                
                conn.execute(query, {
                    "zip_code": weather.location.zip_code,
                    "latitude": weather.location.latitude,
                    "longitude": weather.location.longitude,
                    "timestamp": weather.timestamp,
                    "temperature_f": weather.temperature_f,
                    "wind_speed_mph": weather.wind_speed_mph,
                    "wind_gust_mph": weather.wind_gust_mph,
                    "precipitation_inches": weather.precipitation_inches,
                    "humidity_percent": weather.humidity_percent,
                    "conditions": weather.conditions,
                    "severe_weather_alert": weather.severe_weather_alert,
                    "alert_type": weather.alert_type,
                    "lightning_strikes": weather.lightning_strikes
                })
                return True
                
        except Exception as e:
            print(f"Error inserting weather data: {e}")
            return False
    
    def get_recent_weather(
        self, 
        zip_code: str, 
        hours: int = 6
    ) -> List[Dict[str, Any]]:
        """Get recent weather data for a location"""
        try:
            query = text(f"""
            SELECT * FROM {fabric_config.TABLE_WEATHER_DATA}
            WHERE zip_code = :zip_code
            AND timestamp >= DATEADD(hour, -:hours, GETUTCDATE())
            ORDER BY timestamp DESC
            """)
            
            df = pd.read_sql(query, self.get_engine(), params={"zip_code": zip_code, "hours": hours})
            return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting weather data: {e}")
            return []
    
    # Analytics queries
    
    def get_claim_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get claim statistics for the past N days"""
        try:
            query = text(f"""
            SELECT 
                COUNT(*) as total_claims,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_claims,
                SUM(CASE WHEN status = 'denied' THEN 1 ELSE 0 END) as denied_claims,
                AVG(CASE WHEN payout_amount IS NOT NULL THEN payout_amount END) as avg_payout,
                SUM(CASE WHEN payout_amount IS NOT NULL THEN payout_amount ELSE 0 END) as total_payout
            FROM {fabric_config.TABLE_CLAIMS}
            WHERE filed_at >= DATEADD(day, -:days, GETUTCDATE())
            """)
            
            df = pd.read_sql(query, self.get_engine(), params={"days": days})
            return df.iloc[0].to_dict()
                
        except Exception as e:
            print(f"Error getting claim statistics: {e}")
            return {}

