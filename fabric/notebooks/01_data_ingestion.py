# Databricks notebook source
# MAGIC %md
# MAGIC # Power Outage Data Ingestion
# MAGIC 
# MAGIC This notebook ingests power outage data from multiple sources:
# MAGIC - PowerOutage.us API
# MAGIC - Individual utility APIs (PG&E, Con Edison, Eversource)
# MAGIC - NOAA Weather API for correlation
# MAGIC 
# MAGIC **Schedule**: Run every 5 minutes via Data Factory pipeline

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Imports

# COMMAND ----------

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

# For geospatial calculations
from math import radians, cos, sin, asin, sqrt

# Fabric SDK (if available)
try:
    import notebookutils
    FABRIC_ENV = True
except ImportError:
    FABRIC_ENV = False
    print("Not running in Fabric environment - using local mode")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# API Configuration
# Using PRESTO (Power Reliability Event Simulation Tool) instead of live APIs
# PRESTO generates realistic power outages without needing external API access
NOAA_API_URL = "https://api.weather.gov"
USER_AGENT = "ParametricInsuranceDemo/1.0 (your-email@example.com)"

# Lakehouse tables
LAKEHOUSE_NAME = "parametric_insurance_lakehouse"
TABLE_OUTAGE_EVENTS = "outage_events"
TABLE_WEATHER_DATA = "weather_data"
TABLE_OUTAGE_RAW = "outage_raw"

# Utility-specific APIs (optional - some require API keys)
UTILITY_APIS = {
    "pge": {
        "url": "https://apim.pge.com/cocoutage/outages/getOutagesRegions",
        "enabled": False  # Set to True if you have API access
    },
    "coned": {
        "url": "https://www.coned.com/sitecore/api/ssc/ConEdWeb/OutageMap/AnonymousGetOutageMapData",
        "enabled": False
    }
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper Functions

# COMMAND ----------

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    
    Returns distance in miles
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in miles
    r = 3959
    
    return c * r


def get_zip_from_coordinates(lat: float, lon: float) -> Optional[str]:
    """
    Get ZIP code from coordinates using Census Bureau API
    Note: This is a simplified version - production should use a proper geocoding service
    """
    try:
        url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
        params = {
            "x": lon,
            "y": lat,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json"
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data.get("result", {}).get("geographies", {}).get("ZIP Code Tabulation Areas"):
            return data["result"]["geographies"]["ZIP Code Tabulation Areas"][0]["GEOID"]
        
        return None
    except Exception as e:
        print(f"Error geocoding: {e}")
        return None


def parse_presto_data(presto_events: List[Dict]) -> pd.DataFrame:
    """
    Parse PRESTO simulation data into structured DataFrame
    """
    records = []
    
    for outage in presto_events:
        record = {
            "event_id": outage.get("event_id"),
            "utility_name": outage.get("utility_name"),
            "state": outage["location"].get("state"),
            "affected_customers": outage.get("affected_customers", 0),
            "latitude": outage.get("latitude"),
            "longitude": outage.get("longitude"),
            "zip_code": outage.get("zip_code"),
            "city": outage.get("city"),
            "outage_start": outage.get("outage_start"),
            "outage_end": outage.get("outage_end"),
            "duration_minutes": outage.get("duration_minutes"),
            "cause": outage.get("cause"),
            "reported_cause": outage.get("reported_cause"),
            "status": outage.get("status"),
            "data_source": "PRESTO",
            "last_updated": datetime.utcnow(),
            "raw_json": json.dumps(outage, default=str)
        }
        
        records.append(record)
    
    return pd.DataFrame(records)


def fetch_noaa_weather(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Fetch current weather conditions from NOAA API
    """
    try:
        # Get grid point
        point_url = f"{NOAA_API_URL}/points/{lat},{lon}"
        headers = {"User-Agent": USER_AGENT}
        
        point_response = requests.get(point_url, headers=headers, timeout=10)
        point_data = point_response.json()
        
        if "properties" not in point_data:
            return None
        
        # Get forecast
        forecast_url = point_data["properties"]["forecast"]
        forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
        forecast_data = forecast_response.json()
        
        # Get observation station
        stations_url = point_data["properties"]["observationStations"]
        stations_response = requests.get(stations_url, headers=headers, timeout=10)
        stations_data = stations_response.json()
        
        if not stations_data.get("features"):
            return None
        
        station_url = stations_data["features"][0]["id"]
        obs_url = f"{station_url}/observations/latest"
        obs_response = requests.get(obs_url, headers=headers, timeout=10)
        obs_data = obs_response.json()
        
        properties = obs_data.get("properties", {})
        
        # Extract weather data
        weather = {
            "temperature_f": properties.get("temperature", {}).get("value"),
            "wind_speed_mph": properties.get("windSpeed", {}).get("value"),
            "wind_gust_mph": properties.get("windGust", {}).get("value"),
            "humidity_percent": properties.get("relativeHumidity", {}).get("value"),
            "conditions": properties.get("textDescription"),
            "timestamp": properties.get("timestamp")
        }
        
        # Convert metric to imperial if needed
        if weather["temperature_f"] is not None:
            weather["temperature_f"] = (weather["temperature_f"] * 9/5) + 32
        
        # Check for alerts
        alerts_url = f"{NOAA_API_URL}/alerts/active?point={lat},{lon}"
        alerts_response = requests.get(alerts_url, headers=headers, timeout=10)
        alerts_data = alerts_response.json()
        
        weather["severe_weather_alert"] = len(alerts_data.get("features", [])) > 0
        weather["alert_type"] = None
        
        if weather["severe_weather_alert"]:
            weather["alert_type"] = alerts_data["features"][0]["properties"].get("event")
        
        return weather
        
    except Exception as e:
        print(f"Error fetching NOAA weather: {e}")
        return None

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Ingestion - PRESTO Simulation

# COMMAND ----------

# Import PRESTO simulation tool
import sys
sys.path.append('/lakehouse/default/Files/shared')
from presto import PRESTO, generate_scenario

print(f"Starting power outage data simulation at {datetime.utcnow()}")

try:
    # Initialize PRESTO
    print("Initializing PRESTO (Power Reliability Event Simulation Tool)...")
    presto = PRESTO()
    
    # Generate realistic outage scenario
    # Options: "normal_day", "severe_weather", "heat_wave", "winter_storm"
    scenario_type = "normal_day"  # Change this for different scenarios
    print(f"Generating {scenario_type} scenario...")
    
    raw_data = presto.generate_outage_scenario(scenario_type)
    print(f"Generated {len(raw_data)} realistic outage events")
    
    # Parse PRESTO simulated data into DataFrame
    outage_df = parse_presto_data(raw_data)
    print(f"Parsed {len(outage_df)} outage events")
    
    # Filter for events with significant customer impact (>1000 customers)
    outage_df = outage_df[outage_df['affected_customers'] >= 1000]
    print(f"Filtered to {len(outage_df)} significant outages (>1000 customers)")
    
    # Save raw data to lakehouse
    if FABRIC_ENV:
        # Using Fabric API
        spark_df = spark.createDataFrame(outage_df)
        spark_df.write.format("delta").mode("append").saveAsTable(f"{LAKEHOUSE_NAME}.{TABLE_OUTAGE_RAW}")
    else:
        # Local testing
        outage_df.to_csv(f"{TABLE_OUTAGE_RAW}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    
    print(f"✓ Saved {len(outage_df)} records to {TABLE_OUTAGE_RAW}")
    
except Exception as e:
    print(f"✗ Error ingesting PowerOutage.us data: {e}")
    outage_df = pd.DataFrame()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Enrich with Weather Data

# COMMAND ----------

if not outage_df.empty:
    print("\nEnriching outage data with weather information...")
    
    weather_records = []
    
    for idx, row in outage_df.iterrows():
        if row['latitude'] and row['longitude']:
            print(f"Fetching weather for {row['utility_name']} at ({row['latitude']}, {row['longitude']})...")
            
            weather = fetch_noaa_weather(row['latitude'], row['longitude'])
            
            if weather:
                weather_record = {
                    "event_id": row['event_id'],
                    "zip_code": row['zip_code'],
                    "latitude": row['latitude'],
                    "longitude": row['longitude'],
                    **weather,
                    "ingestion_timestamp": datetime.utcnow()
                }
                weather_records.append(weather_record)
                
            # Rate limiting - NOAA allows reasonable use
            time.sleep(0.5)
    
    if weather_records:
        weather_df = pd.DataFrame(weather_records)
        
        # Save to lakehouse
        if FABRIC_ENV:
            spark_weather = spark.createDataFrame(weather_df)
            spark_weather.write.format("delta").mode("append").saveAsTable(f"{LAKEHOUSE_NAME}.{TABLE_WEATHER_DATA}")
        else:
            weather_df.to_csv(f"{TABLE_WEATHER_DATA}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
        
        print(f"✓ Saved {len(weather_df)} weather records to {TABLE_WEATHER_DATA}")
    else:
        print("✗ No weather data retrieved")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Process and Save Final Outage Events

# COMMAND ----------

if not outage_df.empty:
    print("\nProcessing outage events for final table...")
    
    # Determine outage status and metadata
    outage_df['status'] = 'active'
    outage_df['outage_start'] = datetime.utcnow() - timedelta(minutes=30)  # Estimate
    outage_df['outage_end'] = None
    outage_df['duration_minutes'] = None
    outage_df['cause'] = None
    outage_df['reported_cause'] = 'storm_damage'  # Default assumption
    
    # Select final columns
    final_columns = [
        'event_id', 'utility_name', 'zip_code', 'latitude', 'longitude',
        'affected_customers', 'outage_start', 'outage_end', 'duration_minutes',
        'status', 'cause', 'reported_cause', 'data_source', 'last_updated'
    ]
    
    outage_final = outage_df[final_columns]
    
    # Save to lakehouse
    if FABRIC_ENV:
        spark_final = spark.createDataFrame(outage_final)
        spark_final.write.format("delta").mode("append").saveAsTable(f"{LAKEHOUSE_NAME}.{TABLE_OUTAGE_EVENTS}")
    else:
        outage_final.to_csv(f"{TABLE_OUTAGE_EVENTS}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    
    print(f"✓ Saved {len(outage_final)} events to {TABLE_OUTAGE_EVENTS}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary Statistics

# COMMAND ----------

if not outage_df.empty:
    print("\n" + "="*60)
    print("INGESTION SUMMARY")
    print("="*60)
    print(f"Timestamp: {datetime.utcnow()}")
    print(f"Total outage events: {len(outage_df)}")
    print(f"Total affected customers: {outage_df['affected_customers'].sum():,.0f}")
    print(f"States affected: {outage_df['state'].nunique()}")
    print(f"Utilities affected: {outage_df['utility_name'].nunique()}")
    print("\nTop 5 Utilities by Customer Impact:")
    print(outage_df.groupby('utility_name')['affected_customers'].sum().nlargest(5))
    print("="*60)
else:
    print("\n✗ No outage events processed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Checks

# COMMAND ----------

if not outage_df.empty:
    print("\nDATA QUALITY CHECKS")
    print("-" * 60)
    
    # Check for missing coordinates
    missing_coords = outage_df[outage_df['latitude'].isna() | outage_df['longitude'].isna()]
    print(f"Events with missing coordinates: {len(missing_coords)}")
    
    # Check for missing ZIP codes
    missing_zip = outage_df[outage_df['zip_code'].isna()]
    print(f"Events with missing ZIP codes: {len(missing_zip)}")
    
    # Check for zero customer impact
    zero_impact = outage_df[outage_df['affected_customers'] == 0]
    print(f"Events with zero customer impact: {len(zero_impact)}")
    
    # Data freshness
    data_age_minutes = (datetime.utcnow() - outage_df['last_updated'].max()).total_seconds() / 60
    print(f"Data age (minutes): {data_age_minutes:.1f}")
    
    if data_age_minutes > 10:
        print("⚠️  WARNING: Data may be stale (>10 minutes old)")
    else:
        print("✓ Data is fresh")
    
    print("-" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cleanup and Return

# COMMAND ----------

# Return results for pipeline orchestration
if FABRIC_ENV:
    notebookutils.notebook.exit({
        "status": "success",
        "events_ingested": len(outage_df) if not outage_df.empty else 0,
        "timestamp": datetime.utcnow().isoformat(),
        "weather_records": len(weather_records) if 'weather_records' in locals() else 0
    })
else:
    print("\nIngestion complete!")
    print(f"Events ingested: {len(outage_df) if not outage_df.empty else 0}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optional: Trigger Event Grid Event
# MAGIC 
# MAGIC Uncomment this section to trigger Azure Function via Event Grid after ingestion

# COMMAND ----------

# from azure.eventgrid import EventGridPublisherClient, EventGridEvent
# from azure.core.credentials import AzureKeyCredential
# from datetime import datetime
# import uuid
# 
# # Event Grid configuration (from notebook parameters or key vault)
# EVENTGRID_ENDPOINT = dbutils.widgets.get("eventgrid_endpoint")
# EVENTGRID_KEY = dbutils.widgets.get("eventgrid_key")
# 
# if EVENTGRID_ENDPOINT and EVENTGRID_KEY and not outage_df.empty:
#     try:
#         credential = AzureKeyCredential(EVENTGRID_KEY)
#         client = EventGridPublisherClient(EVENTGRID_ENDPOINT, credential)
#         
#         event = EventGridEvent(
#             event_type="fabric.ingestion.completed",
#             subject="outage_ingestion",
#             data={
#                 "events_count": len(outage_df),
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "table": TABLE_OUTAGE_EVENTS
#             },
#             data_version="1.0",
#             event_time=datetime.utcnow(),
#             id=str(uuid.uuid4())
#         )
#         
#         client.send([event])
#         print("✓ Event Grid notification sent")
#         
#     except Exception as e:
#         print(f"✗ Error sending Event Grid notification: {e}")
