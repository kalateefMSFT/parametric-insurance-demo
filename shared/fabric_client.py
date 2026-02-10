"""
Microsoft Fabric client for Lakehouse and Warehouse operations
"""
import pyodbc
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .config import fabric_config
from .models import OutageEvent, Policy, Claim, Payout, WeatherData


class FabricClient:
    """Client for Microsoft Fabric operations"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize Fabric client
        
        Args:
            connection_string: SQL connection string for Warehouse
        """
        self.connection_string = connection_string or fabric_config.warehouse_connection
        self.lakehouse_name = fabric_config.lakehouse_name
        self.warehouse_name = fabric_config.warehouse_name
    
    def get_connection(self):
        """Get database connection"""
        return pyodbc.connect(self.connection_string)
    
    # Outage Events Operations
    
    def insert_outage_event(self, event: OutageEvent) -> bool:
        """Insert outage event into lakehouse"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f"""
                INSERT INTO {fabric_config.TABLE_OUTAGE_EVENTS} 
                (event_id, utility_name, zip_code, latitude, longitude, 
                 affected_customers, outage_start, outage_end, duration_minutes,
                 status, cause, reported_cause, data_source, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(query, (
                    event.event_id,
                    event.utility_name,
                    event.location.zip_code,
                    event.location.latitude,
                    event.location.longitude,
                    event.affected_customers,
                    event.outage_start,
                    event.outage_end,
                    event.duration_minutes,
                    event.status.value,
                    event.cause,
                    event.reported_cause,
                    event.data_source,
                    event.last_updated or datetime.utcnow()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error inserting outage event: {e}")
            return False
    
    def update_outage_event(self, event_id: str, **kwargs) -> bool:
        """Update outage event"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
                values = list(kwargs.values()) + [event_id]
                
                query = f"""
                UPDATE {fabric_config.TABLE_OUTAGE_EVENTS}
                SET {set_clause}, last_updated = GETUTCDATE()
                WHERE event_id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating outage event: {e}")
            return False
    
    def get_outage_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get outage event by ID"""
        try:
            with self.get_connection() as conn:
                query = f"""
                SELECT * FROM {fabric_config.TABLE_OUTAGE_EVENTS}
                WHERE event_id = ?
                """
                df = pd.read_sql(query, conn, params=[event_id])
                
                if len(df) == 0:
                    return None
                
                return df.iloc[0].to_dict()
                
        except Exception as e:
            print(f"Error getting outage event: {e}")
            return None
    
    def get_active_outages(self) -> List[Dict[str, Any]]:
        """Get all active outages"""
        try:
            with self.get_connection() as conn:
                query = f"""
                SELECT * FROM {fabric_config.TABLE_OUTAGE_EVENTS}
                WHERE status = 'active'
                ORDER BY outage_start DESC
                """
                df = pd.read_sql(query, conn)
                return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting active outages: {e}")
            return []
    
    # Policy Operations
    
    def get_policies_in_zip(self, zip_code: str) -> List[Dict[str, Any]]:
        """Get all active policies in a ZIP code"""
        try:
            with self.get_connection() as conn:
                query = f"""
                SELECT * FROM {fabric_config.TABLE_POLICIES}
                WHERE zip_code = ? AND status = 'active'
                """
                df = pd.read_sql(query, conn, params=[zip_code])
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
            with self.get_connection() as conn:
                # Using Haversine formula
                query = f"""
                SELECT *,
                    (3959 * acos(
                        cos(radians(?)) * cos(radians(latitude)) * 
                        cos(radians(longitude) - radians(?)) + 
                        sin(radians(?)) * sin(radians(latitude))
                    )) AS distance_miles
                FROM {fabric_config.TABLE_POLICIES}
                WHERE status = 'active'
                HAVING distance_miles <= ?
                ORDER BY distance_miles
                """
                
                df = pd.read_sql(
                    query, 
                    conn, 
                    params=[latitude, longitude, latitude, radius_miles]
                )
                return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting nearby policies: {e}")
            return []
    
    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Get policy by ID"""
        try:
            with self.get_connection() as conn:
                query = f"""
                SELECT * FROM {fabric_config.TABLE_POLICIES}
                WHERE policy_id = ?
                """
                df = pd.read_sql(query, conn, params=[policy_id])
                
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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f"""
                INSERT INTO {fabric_config.TABLE_CLAIMS}
                (claim_id, policy_id, outage_event_id, status, filed_at,
                 payout_amount, ai_confidence_score, ai_reasoning, fraud_flags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(query, (
                    claim.claim_id,
                    claim.policy_id,
                    claim.outage_event_id,
                    claim.status.value,
                    claim.filed_at,
                    claim.payout_amount,
                    claim.ai_confidence_score,
                    claim.ai_reasoning,
                    json.dumps(claim.fraud_flags) if claim.fraud_flags else None
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error inserting claim: {e}")
            return False
    
    def update_claim(self, claim_id: str, **kwargs) -> bool:
        """Update claim"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
                values = list(kwargs.values()) + [claim_id]
                
                query = f"""
                UPDATE {fabric_config.TABLE_CLAIMS}
                SET {set_clause}
                WHERE claim_id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating claim: {e}")
            return False
    
    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim by ID"""
        try:
            with self.get_connection() as conn:
                query = f"""
                SELECT * FROM {fabric_config.TABLE_CLAIMS}
                WHERE claim_id = ?
                """
                df = pd.read_sql(query, conn, params=[claim_id])
                
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
            with self.get_connection() as conn:
                query = f"""
                SELECT * FROM {fabric_config.TABLE_CLAIMS}
                WHERE policy_id = ?
                AND filed_at >= DATEADD(day, -?, GETUTCDATE())
                ORDER BY filed_at DESC
                """
                
                df = pd.read_sql(query, conn, params=[policy_id, days])
                return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting policy claims: {e}")
            return []
    
    # Payout Operations
    
    def insert_payout(self, payout: Payout) -> bool:
        """Insert payout record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f"""
                INSERT INTO {fabric_config.TABLE_PAYOUTS}
                (payout_id, claim_id, policy_id, amount, status, 
                 initiated_at, payment_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(query, (
                    payout.payout_id,
                    payout.claim_id,
                    payout.policy_id,
                    payout.amount,
                    payout.status.value,
                    payout.initiated_at,
                    payout.payment_method
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error inserting payout: {e}")
            return False
    
    def update_payout(self, payout_id: str, **kwargs) -> bool:
        """Update payout record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
                values = list(kwargs.values()) + [payout_id]
                
                query = f"""
                UPDATE {fabric_config.TABLE_PAYOUTS}
                SET {set_clause}
                WHERE payout_id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating payout: {e}")
            return False
    
    # Weather Operations
    
    def insert_weather_data(self, weather: WeatherData) -> bool:
        """Insert weather data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f"""
                INSERT INTO {fabric_config.TABLE_WEATHER_DATA}
                (zip_code, latitude, longitude, timestamp, temperature_f,
                 wind_speed_mph, wind_gust_mph, precipitation_inches,
                 humidity_percent, conditions, severe_weather_alert,
                 alert_type, lightning_strikes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(query, (
                    weather.location.zip_code,
                    weather.location.latitude,
                    weather.location.longitude,
                    weather.timestamp,
                    weather.temperature_f,
                    weather.wind_speed_mph,
                    weather.wind_gust_mph,
                    weather.precipitation_inches,
                    weather.humidity_percent,
                    weather.conditions,
                    weather.severe_weather_alert,
                    weather.alert_type,
                    weather.lightning_strikes
                ))
                
                conn.commit()
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
            with self.get_connection() as conn:
                query = f"""
                SELECT * FROM {fabric_config.TABLE_WEATHER_DATA}
                WHERE zip_code = ?
                AND timestamp >= DATEADD(hour, -?, GETUTCDATE())
                ORDER BY timestamp DESC
                """
                
                df = pd.read_sql(query, conn, params=[zip_code, hours])
                return df.to_dict('records')
                
        except Exception as e:
            print(f"Error getting weather data: {e}")
            return []
    
    # Analytics queries
    
    def get_claim_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get claim statistics for the past N days"""
        try:
            with self.get_connection() as conn:
                query = f"""
                SELECT 
                    COUNT(*) as total_claims,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_claims,
                    SUM(CASE WHEN status = 'denied' THEN 1 ELSE 0 END) as denied_claims,
                    AVG(CASE WHEN payout_amount IS NOT NULL THEN payout_amount END) as avg_payout,
                    SUM(CASE WHEN payout_amount IS NOT NULL THEN payout_amount ELSE 0 END) as total_payout
                FROM {fabric_config.TABLE_CLAIMS}
                WHERE filed_at >= DATEADD(day, -?, GETUTCDATE())
                """
                
                df = pd.read_sql(query, conn, params=[days])
                return df.iloc[0].to_dict()
                
        except Exception as e:
            print(f"Error getting claim statistics: {e}")
            return {}
