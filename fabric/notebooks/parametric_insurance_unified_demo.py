# Fabric notebook source
# ============================================================================
# PARAMETRIC INSURANCE DEMO — UNIFIED NOTEBOOK WITH EVENT GRID
# Power Outage Business Interruption Insurance
# ============================================================================
# This single notebook runs the ENTIRE demo end-to-end in Microsoft Fabric
# AND publishes events to Azure Event Grid at every pipeline stage:
#
#   Step 0: Configuration & Imports
#   Step 1: Create Warehouse Schema (tables + views + event log)
#   Step 2: Load Sample Policies
#   Step 3: Simulate Power Outages with PRESTO
#   Step 4: Enrich with NOAA Weather Data (free API)
#   Step 5: Match Outages to Policies → publish "outage.detected"
#   Step 6: Validate Claims via Foundry Agent → publish "claim.approved" / "claim.denied"
#   Step 7: Process Payouts → publish "payout.processed"
#   Step 8: Dashboard Summary + Event Audit Log
#
# Event Grid Integration:
#   - 4 event types published across the pipeline
#   - Events can trigger Azure Functions, Logic Apps, or Webhooks
#   - Full event audit trail stored in Delta table
#   - Graceful fallback when Event Grid is not configured
#
# Free Public Data Sources Used:
#   - NOAA Weather API (https://api.weather.gov) — No API key required
#   - PRESTO (local simulation) — No API key required
# ============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC # 🏗️ Parametric Insurance Demo — Unified Notebook + Event Grid
# MAGIC
# MAGIC | Step | Description | Data Source | Event Grid |
# MAGIC |------|-------------|------------|------------|
# MAGIC | 1 | Create Schema | SQL DDL | — |
# MAGIC | 2 | Load Policies | Sample data | — |
# MAGIC | 3 | Simulate Outages | **PRESTO** (free) | — |
# MAGIC | 4 | Weather Enrichment | **NOAA API** (free) | — |
# MAGIC | 5 | Match → Policies | Fabric SQL | `outage.detected` |
# MAGIC | 6 | AI Claim Validation | **Foundry Agent** | `claim.approved` / `claim.denied` |
# MAGIC | 7 | Process Payouts | Fabric SQL | `payout.processed` |
# MAGIC | 8 | Summary + Audit | Analytics | — |
# MAGIC
# MAGIC > ⚡ `PRESTO → Fabric → Event Grid → Foundry AI → Event Grid → Payout → Event Grid`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Step 0 — Configuration & Imports

# COMMAND ----------

%pip install azure-ai-projects==2.0.0b3 azure-core azure-ai-agents

import os
import sys
import json
import uuid
import math
import random
import requests
import warnings
import traceback
import notebookutils
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, TimestampType, FloatType, BooleanType
)

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------
# CONFIGURATION — Edit these values for your environment
# --------------------------------------------------------------------------

@dataclass
class DemoConfig:
    """Centralized configuration for the entire demo."""

    # -- Fabric --
    lakehouse_name: str = "parametric_insurance_lakehouse"
    warehouse_name: str = "parametric_insurance_warehouse"

    # -- PRESTO Simulation --
    scenario_type: str = "severe_weather"   # normal_day | severe_weather | heat_wave | winter_storm
    min_customer_impact: int = 500

    # -- NOAA Weather API (free) --
    noaa_api_url: str = "https://api.weather.gov"
    noaa_user_agent: str = "ParametricInsuranceDemo/1.0 (kalateef@microsoft.com)"

    # -- Foundry Agent (Don't use the "New Foundry" experience to create your agent, it won't work. Use the legacy Agent experience) --
    foundry_endpoint: str = "<foundry-endpoint>"
    foundry_agent_id: str = "<agent_id>"

    # -- Azure Event Grid (optional — leave blank for local-only mode) --
    eventgrid_topic_endpoint: str = "<eventgrid_topic_endpoint>"
    eventgrid_topic_key: str = "<eventgrid_topic_key>"

    # -- Event types (match existing Azure Function subscriptions) --
    EVT_OUTAGE_DETECTED: str = "outage.detected"
    EVT_THRESHOLD_EXCEEDED: str = "outage.threshold.exceeded"
    EVT_CLAIM_APPROVED: str = "claim.approved"
    EVT_CLAIM_DENIED: str = "claim.denied"
    EVT_PAYOUT_PROCESSED: str = "payout.processed"

    # -- Policy Defaults --
    default_threshold_minutes: int = 120
    default_hourly_rate: float = 500.0
    max_payout_per_claim: float = 50000.0


config = DemoConfig()

# Override from environment variables / notebook widgets
config.foundry_endpoint        = os.getenv("FOUNDRY_ENDPOINT", config.foundry_endpoint)
config.eventgrid_topic_endpoint = os.getenv("EVENTGRID_TOPIC_ENDPOINT", config.eventgrid_topic_endpoint)
config.eventgrid_topic_key     = os.getenv("EVENTGRID_KEY", config.eventgrid_topic_key)

# Create a Variable Library (eg. "environmentVariables") in Fabric workspace to store these variables
environment_library = notebookutils.variableLibrary.getLibrary("environmentVariables") 

os.environ["AZURE_CLIENT_ID"] = environment_library.AZURE_CLIENT_ID
os.environ["AZURE_TENANT_ID"] = environment_library.AZURE_TENANT_ID
os.environ["AZURE_CLIENT_SECRET"] = environment_library.AZURE_CLIENT_SECRET

# Detect Fabric
try:
    from notebookutils import mssparkutils
    FABRIC_ENV = True
    print("✅ Running inside Microsoft Fabric")
    # Try loading from notebook widgets (set via pipeline parameters)
    try:
        config.eventgrid_topic_endpoint = config.eventgrid_topic_endpoint or mssparkutils.widgets.get("eventgrid_endpoint")
        config.eventgrid_topic_key = config.eventgrid_topic_key or mssparkutils.widgets.get("eventgrid_key")
    except Exception:
        pass
except ImportError:
    FABRIC_ENV = False
    print("⚠️  Running outside Fabric — results saved locally")

EVENTGRID_ENABLED = bool(config.eventgrid_topic_endpoint and config.eventgrid_topic_key)

spark = SparkSession.builder.getOrCreate()

print(f"📋 Scenario:          {config.scenario_type}")
print(f"📋 Min Customer Impact: {config.min_customer_impact}")
print(f"📋 Foundry Agent:     {'Enabled' if config.foundry_endpoint else 'Rule-based fallback'}")
print(f"📋 Event Grid:        {'✅ ENABLED' if EVENTGRID_ENABLED else '⚠️  DISABLED (local-only mode)'}")
print(f"📋 Timestamp:         {datetime.utcnow().isoformat()}Z")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 📡 Event Grid Client (embedded)
# MAGIC
# MAGIC Lightweight Event Grid publisher that works inside a Fabric notebook.
# MAGIC Publishes CloudEvents-compatible messages to an Event Grid Topic.
# MAGIC Falls back gracefully when Event Grid is not configured.

# COMMAND ----------

# ============================================================================
# Event Grid Publisher — notebook-embedded, zero external dependencies
# Uses the Event Grid REST API directly (no azure-eventgrid SDK required)
# ============================================================================

class NotebookEventGridClient:
    """
    Lightweight Event Grid publisher for use inside Fabric notebooks.
    Uses the Event Grid REST API with SAS key authentication.
    Stores an audit log of all events locally in a list.
    """

    def __init__(self, endpoint: str, key: str):
        self.endpoint = endpoint.rstrip("/")
        self.key = key
        self.audit_log: List[Dict[str, Any]] = []
        self._event_counter = 0

    def publish_event(
        self,
        event_type: str,
        subject: str,
        data: Dict[str, Any],
        data_version: str = "1.0",
    ) -> bool:
        """
        Publish a single EventGridEvent to the topic.
        Returns True on success, False on failure (never raises).
        """
        event_id = str(uuid.uuid4())
        event_time = datetime.utcnow().isoformat() + "Z"
        self._event_counter += 1

        event_payload = [
            {
                "id": event_id,
                "eventType": event_type,
                "subject": subject,
                "eventTime": event_time,
                "data": data,
                "dataVersion": data_version,
            }
        ]

        # Audit record (always stored, even if publish fails)
        audit = {
            "sequence": self._event_counter,
            "event_id": event_id,
            "event_type": event_type,
            "subject": subject,
            "event_time": event_time,
            "data_summary": json.dumps(data, default=str)[:500],
            "status": "pending",
            "error": None,
        }

        try:
            resp = requests.post(
                f"{self.endpoint}/api/events?api-version=2018-01-01",
                headers={
                    "Content-Type": "application/json",
                    "aeg-sas-key": self.key,
                },
                json=event_payload,
                timeout=15,
            )
            resp.raise_for_status()
            audit["status"] = "published"
            self.audit_log.append(audit)
            return True

        except Exception as e:
            audit["status"] = "failed"
            audit["error"] = str(e)
            self.audit_log.append(audit)
            print(f"  ⚠️  Event Grid publish failed for {event_type}: {e}")
            return False

    def publish_batch(self, events: List[Dict[str, Any]]) -> bool:
        """Publish multiple events in a single batch."""
        batch = []
        audits = []
        for evt in events:
            eid = str(uuid.uuid4())
            etime = datetime.utcnow().isoformat() + "Z"
            self._event_counter += 1
            batch.append({
                "id": eid,
                "eventType": evt["event_type"],
                "subject": evt["subject"],
                "eventTime": etime,
                "data": evt["data"],
                "dataVersion": evt.get("data_version", "1.0"),
            })
            audits.append({
                "sequence": self._event_counter,
                "event_id": eid,
                "event_type": evt["event_type"],
                "subject": evt["subject"],
                "event_time": etime,
                "data_summary": json.dumps(evt["data"], default=str)[:500],
                "status": "pending",
                "error": None,
            })

        try:
            resp = requests.post(
                f"{self.endpoint}/api/events?api-version=2018-01-01",
                headers={
                    "Content-Type": "application/json",
                    "aeg-sas-key": self.key,
                },
                json=batch,
                timeout=30,
            )
            resp.raise_for_status()
            for a in audits:
                a["status"] = "published"
            self.audit_log.extend(audits)
            return True
        except Exception as e:
            for a in audits:
                a["status"] = "failed"
                a["error"] = str(e)
            self.audit_log.extend(audits)
            print(f"  ⚠️  Batch publish failed: {e}")
            return False


# ---- Local-only stub when Event Grid is disabled ----
class LocalEventLogger:
    """Drop-in replacement that logs events locally without publishing."""

    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []
        self._event_counter = 0

    def publish_event(self, event_type: str, subject: str, data: Dict[str, Any], **kw) -> bool:
        self._event_counter += 1
        self.audit_log.append({
            "sequence": self._event_counter,
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "subject": subject,
            "event_time": datetime.utcnow().isoformat() + "Z",
            "data_summary": json.dumps(data, default=str)[:500],
            "status": "local_only",
            "error": None,
        })
        return True

    def publish_batch(self, events: List[Dict[str, Any]]) -> bool:
        for evt in events:
            self.publish_event(evt["event_type"], evt["subject"], evt["data"])
        return True


# ---- Initialize ----
if EVENTGRID_ENABLED:
    eg_client = NotebookEventGridClient(config.eventgrid_topic_endpoint, config.eventgrid_topic_key)
    print("📡 Event Grid client initialized — events will be published to Azure")
else:
    eg_client = LocalEventLogger()
    print("📝 Local event logger initialized — events recorded locally only")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 0b. Test Event Grid Connection

# COMMAND ----------

if EVENTGRID_ENABLED:
    print("🔌 Testing Event Grid connection...")
    test_ok = eg_client.publish_event(
        event_type="test.connection",
        subject="test/notebook-startup",
        data={
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "parametric-insurance-notebook",
            "message": "Connection test from Fabric notebook",
        },
    )
    if test_ok:
        print("✅ Event Grid connection verified — test event published successfully!")
    else:
        print("❌ Event Grid connection FAILED — check endpoint and key.")
        print("   Continuing in local-only mode.")
        eg_client = LocalEventLogger()
        EVENTGRID_ENABLED = False
else:
    print("ℹ️  Event Grid not configured — skipping connection test.")
    print("   Set EVENTGRID_TOPIC_ENDPOINT and EVENTGRID_KEY to enable.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 📐 Step 1 — Create Warehouse Schema

# COMMAND ----------

now = datetime.utcnow()

for table in ["event_audit_log", "payouts", "claims", "weather_data", "social_signals", "outage_events", "outage_raw", "policies"]:
    spark.sql(f"DROP TABLE IF EXISTS {table}")
    print(f"  Dropped table (if existed): {table}")

print("\n🗑️  Existing tables cleaned up.")

# COMMAND ----------

# -- POLICIES --
spark.sql("""
CREATE TABLE IF NOT EXISTS policies (
    policy_id STRING, business_name STRING, business_type STRING,
    zip_code STRING, address STRING, city STRING, state STRING,
    latitude DOUBLE, longitude DOUBLE,
    threshold_minutes INT, hourly_rate DOUBLE, max_payout DOUBLE,
    status STRING, effective_date TIMESTAMP, expiration_date TIMESTAMP,
    contact_email STRING, contact_phone STRING,
    created_at TIMESTAMP, updated_at TIMESTAMP
) USING DELTA
""")

# -- OUTAGE EVENTS --
spark.sql("""
CREATE TABLE IF NOT EXISTS outage_events (
    event_id STRING, utility_name STRING, zip_code STRING,
    city STRING, state STRING, latitude DOUBLE, longitude DOUBLE,
    affected_customers INT, outage_start TIMESTAMP, outage_end TIMESTAMP,
    duration_minutes INT, reported_cause STRING, status STRING,
    data_source STRING, created_at TIMESTAMP, updated_at TIMESTAMP
) USING DELTA
""")

# -- WEATHER DATA --
spark.sql("""
CREATE TABLE IF NOT EXISTS weather_data (
    weather_id STRING, event_id STRING, zip_code STRING,
    latitude DOUBLE, longitude DOUBLE,
    temperature_f DOUBLE, wind_speed_mph DOUBLE, wind_gust_mph DOUBLE,
    conditions STRING, severe_weather_alert BOOLEAN, alert_type STRING,
    observation_time TIMESTAMP, created_at TIMESTAMP
) USING DELTA
""")

# -- CLAIMS --
spark.sql("""
CREATE TABLE IF NOT EXISTS claims (
    claim_id STRING, policy_id STRING, outage_event_id STRING,
    status STRING, filed_at TIMESTAMP, validated_at TIMESTAMP,
    approved_at TIMESTAMP, denied_at TIMESTAMP, denial_reason STRING,
    payout_amount DOUBLE, ai_confidence_score DOUBLE, ai_reasoning STRING,
    fraud_flags STRING, weather_factor DOUBLE, severity_assessment STRING,
    created_at TIMESTAMP, updated_at TIMESTAMP
) USING DELTA
""")

# -- PAYOUTS --
spark.sql("""
CREATE TABLE IF NOT EXISTS payouts (
    payout_id STRING, claim_id STRING, policy_id STRING,
    amount DOUBLE, status STRING,
    initiated_at TIMESTAMP, completed_at TIMESTAMP,
    transaction_id STRING, payment_method STRING, created_at TIMESTAMP
) USING DELTA
""")

# -- RAW STAGING --
spark.sql("""
CREATE TABLE IF NOT EXISTS outage_raw (
    id INT, event_id STRING, utility_name STRING, state STRING,
    affected_customers INT, latitude DOUBLE, longitude DOUBLE,
    zip_code STRING, data_source STRING, raw_json STRING,
    last_updated TIMESTAMP, ingestion_timestamp TIMESTAMP
) USING DELTA
""")

# -- EVENT AUDIT LOG (tracks every Event Grid event from this notebook) --
spark.sql("""
CREATE TABLE IF NOT EXISTS event_audit_log (
    sequence INT,
    event_id STRING,
    event_type STRING,
    subject STRING,
    event_time STRING,
    data_summary STRING,
    status STRING,
    error STRING,
    created_at TIMESTAMP
) USING DELTA
""")

print("✅ All 7 tables created (including event_audit_log).")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 📑 Step 2 — Load Sample Policies

# COMMAND ----------

sample_policies = [
    {"policy_id": "BI-001", "business_name": "Pike Place Coffee Co", "business_type": "Coffee Shop",
     "zip_code": "98101", "address": "123 Pike St", "city": "Seattle", "state": "WA",
     "latitude": 47.6097, "longitude": -122.3425, "threshold_minutes": 120,
     "hourly_rate": 500.0, "max_payout": 10000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "owner@pikeplacecoffee.com", "contact_phone": "206-555-0101",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-002", "business_name": "Broadway Restaurant & Bar", "business_type": "Restaurant",
     "zip_code": "98102", "address": "456 Broadway Ave E", "city": "Seattle", "state": "WA",
     "latitude": 47.6234, "longitude": -122.3212, "threshold_minutes": 60,
     "hourly_rate": 750.0, "max_payout": 15000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "manager@broadwayrestaurant.com", "contact_phone": "206-555-0102",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-003", "business_name": "Capitol Hill Fitness Center", "business_type": "Gym",
     "zip_code": "98102", "address": "789 E Pine St", "city": "Seattle", "state": "WA",
     "latitude": 47.6145, "longitude": -122.3201, "threshold_minutes": 180,
     "hourly_rate": 300.0, "max_payout": 8000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "info@capitolhillfitness.com", "contact_phone": "206-555-0103",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-004", "business_name": "Downtown Portland Bakery", "business_type": "Bakery",
     "zip_code": "97201", "address": "321 SW Morrison St", "city": "Portland", "state": "OR",
     "latitude": 45.5202, "longitude": -122.6742, "threshold_minutes": 90,
     "hourly_rate": 600.0, "max_payout": 12000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "baker@portlandbakery.com", "contact_phone": "503-555-0104",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-005", "business_name": "Pearl District Co-Working", "business_type": "Co-Working Space",
     "zip_code": "97209", "address": "555 NW 13th Ave", "city": "Portland", "state": "OR",
     "latitude": 45.5276, "longitude": -122.6847, "threshold_minutes": 240,
     "hourly_rate": 400.0, "max_payout": 20000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "admin@pearlcowork.com", "contact_phone": "503-555-0105",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-006", "business_name": "Mission District Brewery", "business_type": "Brewery",
     "zip_code": "94110", "address": "888 Valencia St", "city": "San Francisco", "state": "CA",
     "latitude": 37.7599, "longitude": -122.4214, "threshold_minutes": 120,
     "hourly_rate": 900.0, "max_payout": 25000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "owner@missionbrewery.com", "contact_phone": "415-555-0106",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-007", "business_name": "Financial District Data Center", "business_type": "Data Center",
     "zip_code": "94111", "address": "100 California St", "city": "San Francisco", "state": "CA",
     "latitude": 37.7935, "longitude": -122.3989, "threshold_minutes": 30,
     "hourly_rate": 2000.0, "max_payout": 50000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "ops@fdatacenter.com", "contact_phone": "415-555-0107",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-008", "business_name": "Santa Monica Beach Cafe", "business_type": "Cafe",
     "zip_code": "90401", "address": "1550 Ocean Ave", "city": "Santa Monica", "state": "CA",
     "latitude": 34.0195, "longitude": -118.4912, "threshold_minutes": 90,
     "hourly_rate": 550.0, "max_payout": 10000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "info@beachcafe.com", "contact_phone": "310-555-0108",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-009", "business_name": "Hollywood Production Studio", "business_type": "Production Studio",
     "zip_code": "90028", "address": "6500 Sunset Blvd", "city": "Los Angeles", "state": "CA",
     "latitude": 34.0983, "longitude": -118.3267, "threshold_minutes": 60,
     "hourly_rate": 1500.0, "max_payout": 40000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "production@hollywoodstudio.com", "contact_phone": "323-555-0109",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-010", "business_name": "Manhattan Fine Dining", "business_type": "Restaurant",
     "zip_code": "10022", "address": "300 Park Ave", "city": "New York", "state": "NY",
     "latitude": 40.7614, "longitude": -73.9776, "threshold_minutes": 45,
     "hourly_rate": 1200.0, "max_payout": 30000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "reservations@manhattanfine.com", "contact_phone": "212-555-0110",
     "created_at": now, "updated_at": now},
    {"policy_id": "BI-011", "business_name": "Brooklyn Artisan Market", "business_type": "Retail",
     "zip_code": "11211", "address": "200 Bedford Ave", "city": "Brooklyn", "state": "NY",
     "latitude": 40.7181, "longitude": -73.9571, "threshold_minutes": 120,
     "hourly_rate": 400.0, "max_payout": 9000.0, "status": "active",
     "effective_date": datetime(2026, 1, 1), "expiration_date": None,
     "contact_email": "market@brooklynartisan.com", "contact_phone": "718-555-0111",
     "created_at": now, "updated_at": now}
]

now = datetime.now()

policy_schema = StructType([
    StructField("policy_id", StringType()),
    StructField("business_name", StringType()),
    StructField("business_type", StringType()),
    StructField("zip_code", StringType()),
    StructField("address", StringType()),
    StructField("city", StringType()),
    StructField("state", StringType()),
    StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()),
    StructField("threshold_minutes", IntegerType()),
    StructField("hourly_rate", DoubleType()),
    StructField("max_payout", DoubleType()),
    StructField("status", StringType()),
    StructField("effective_date", TimestampType()),
    StructField("expiration_date", TimestampType()),
    StructField("contact_email", StringType()),
    StructField("contact_phone", StringType()),
    StructField("created_at", TimestampType()),
    StructField("updated_at", TimestampType())
])

policies_df = spark.createDataFrame(sample_policies, schema=policy_schema)
policies_df.write.format("delta").mode("overwrite").saveAsTable("policies")
print(f"✅ Loaded {len(sample_policies)} sample policies.")
display(spark.sql("SELECT policy_id, business_name, city, state, threshold_minutes, hourly_rate, max_payout FROM policies WHERE status='active' ORDER BY city"))

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## ⚡ Step 3 — Simulate Power Outages with PRESTO

# COMMAND ----------

class PRESTO:
    """Power Reliability Event Simulation Tool — generates realistic outage scenarios."""

    def __init__(self):
        self.cities = [
            {"name": "Seattle",       "state": "WA", "zip": "98101", "lat": 47.6062, "lon": -122.3321, "region": "Pacific Northwest"},
            {"name": "Portland",      "state": "OR", "zip": "97201", "lat": 45.5152, "lon": -122.6784, "region": "Pacific Northwest"},
            {"name": "San Francisco", "state": "CA", "zip": "94102", "lat": 37.7749, "lon": -122.4194, "region": "California"},
            {"name": "Los Angeles",   "state": "CA", "zip": "90012", "lat": 34.0522, "lon": -118.2437, "region": "California"},
            {"name": "San Diego",     "state": "CA", "zip": "92101", "lat": 32.7157, "lon": -117.1611, "region": "California"},
            {"name": "Phoenix",       "state": "AZ", "zip": "85001", "lat": 33.4484, "lon": -112.0740, "region": "Southwest"},
            {"name": "Las Vegas",     "state": "NV", "zip": "89101", "lat": 36.1699, "lon": -115.1398, "region": "Southwest"},
            {"name": "Denver",        "state": "CO", "zip": "80202", "lat": 39.7392, "lon": -104.9903, "region": "Mountain"},
            {"name": "Chicago",       "state": "IL", "zip": "60601", "lat": 41.8781, "lon": -87.6298, "region": "Midwest"},
            {"name": "Detroit",       "state": "MI", "zip": "48201", "lat": 42.3314, "lon": -83.0458, "region": "Midwest"},
            {"name": "Atlanta",       "state": "GA", "zip": "30303", "lat": 33.7490, "lon": -84.3880, "region": "South"},
            {"name": "Miami",         "state": "FL", "zip": "33101", "lat": 25.7617, "lon": -80.1918, "region": "South"},
            {"name": "Houston",       "state": "TX", "zip": "77002", "lat": 29.7604, "lon": -95.3698, "region": "Texas"},
            {"name": "Dallas",        "state": "TX", "zip": "75201", "lat": 32.7767, "lon": -96.7970, "region": "Texas"},
            {"name": "Austin",        "state": "TX", "zip": "78701", "lat": 30.2672, "lon": -97.7431, "region": "Texas"},
            {"name": "New York",      "state": "NY", "zip": "10001", "lat": 40.7128, "lon": -74.0060, "region": "Northeast"},
            {"name": "Boston",        "state": "MA", "zip": "02101", "lat": 42.3601, "lon": -71.0589, "region": "Northeast"},
            {"name": "Philadelphia",  "state": "PA", "zip": "19102", "lat": 39.9526, "lon": -75.1652, "region": "Mid-Atlantic"},
            {"name": "Washington",    "state": "DC", "zip": "20001", "lat": 38.9072, "lon": -77.0369, "region": "Mid-Atlantic"},
        ]
        self.utilities = {
            "Pacific Northwest": ["Seattle City Light", "Portland General Electric", "Puget Sound Energy", "Tacoma Power"],
            "California":        ["Pacific Gas & Electric (PG&E)", "Southern California Edison", "San Diego Gas & Electric", "LADWP"],
            "Southwest":         ["Arizona Public Service", "Salt River Project", "NV Energy"],
            "Mountain":          ["Xcel Energy", "Black Hills Energy", "Rocky Mountain Power"],
            "Midwest":           ["ComEd", "DTE Energy", "Duke Energy Ohio", "Consumers Energy"],
            "South":             ["Georgia Power", "Duke Energy Carolinas", "Florida Power & Light", "Entergy"],
            "Texas":             ["Oncor Electric Delivery", "CenterPoint Energy", "Austin Energy", "AEP Texas"],
            "Northeast":         ["Con Edison", "National Grid", "Eversource Energy", "PSEG"],
            "Mid-Atlantic":      ["PECO Energy", "Pepco", "BGE", "Dominion Energy"],
        }
        self.outage_causes = [
            ("storm_damage", 0.35), ("equipment_failure", 0.25), ("tree_contact", 0.15),
            ("vehicle_accident", 0.08), ("animal_contact", 0.05), ("overload", 0.05),
            ("planned_maintenance", 0.03), ("lightning", 0.02), ("unknown", 0.02),
        ]

    def _pick_cause(self, ws): 
        c, w = zip(*self.outage_causes); w = list(w)
        if ws in ("severe","extreme"): w[0]*=3; w[7]*=5
        return random.choices(c, weights=w, k=1)[0]

    def _dur(self, ws):
        mu = {"normal":45,"moderate":75,"severe":120,"extreme":200}.get(ws, 60)
        return max(15, int(random.gauss(mu, mu*0.6)))

    def _cust(self, ws):
        s = {"normal":1,"moderate":1.5,"severe":3,"extreme":5}.get(ws, 1)
        return max(100, int(random.lognormvariate(math.log(2000), 1.0) * s))

    def generate_outage(self, location=None, timestamp=None, weather_severity="normal"):
        city = location or random.choice(self.cities)
        ts = timestamp or datetime.utcnow()
        dur = self._dur(weather_severity)
        policy_zips = {
            "Seattle":["98101","98102"], "Portland":["97201","97209"],
            "San Francisco":["94110","94111"], "Los Angeles":["90028","90401"],
            "New York":["10001","10022","11211"],
        }
        zc = random.choice(policy_zips.get(city["name"], [city["zip"]]))
        return {
            "event_id": f"PRESTO-{city['state']}-{ts.strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}",
            "utility_name": random.choice(self.utilities.get(city["region"], ["Unknown"])),
            "city": city["name"], "state": city["state"], "zip_code": zc,
            "latitude": city["lat"]+random.uniform(-0.02,0.02),
            "longitude": city["lon"]+random.uniform(-0.02,0.02),
            "affected_customers": self._cust(weather_severity),
            "outage_start": ts, "outage_end": ts+timedelta(minutes=dur),
            "duration_minutes": dur, "reported_cause": self._pick_cause(weather_severity),
            "status": "resolved", "weather_severity": weather_severity, "data_source": "PRESTO",
        }

    def generate_outage_scenario(self, scenario_type="normal_day"):
        cfgs = {
            "normal_day":     {"count":(2,5),   "sw":[.70,.20,.08,.02]},
            "severe_weather": {"count":(10,20),  "sw":[.10,.20,.50,.20]},
            "heat_wave":      {"count":(5,15),   "sw":[.20,.40,.30,.10]},
            "winter_storm":   {"count":(15,30),  "sw":[.05,.15,.50,.30]},
        }
        c = cfgs.get(scenario_type, cfgs["normal_day"])
        n = random.randint(*c["count"])
        sevs = ["normal","moderate","severe","extreme"]
        base = datetime.utcnow() - timedelta(hours=random.randint(1,6))
        outs = [self.generate_outage(timestamp=base+timedelta(minutes=random.randint(0,360)),
                weather_severity=random.choices(sevs, weights=c["sw"], k=1)[0]) for _ in range(n)]
        outs.sort(key=lambda x: x["outage_start"])
        return outs

presto = PRESTO()
raw_outages = presto.generate_outage_scenario(config.scenario_type)
print(f"⚡ PRESTO generated {len(raw_outages)} outages for scenario: {config.scenario_type}")
for i, o in enumerate(raw_outages[:5], 1):
    print(f"  {i}. {o['city']}, {o['state']} | {o['utility_name']} | {o['affected_customers']:,} cust | {o['duration_minutes']} min | {o['reported_cause']}")
if len(raw_outages) > 5: print(f"  ... and {len(raw_outages)-5} more")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3b. Filter & Persist Outage Events

# COMMAND ----------

significant_outages = [o for o in raw_outages if o["affected_customers"] >= config.min_customer_impact]
print(f"📊 Significant outages (≥{config.min_customer_impact} customers): {len(significant_outages)} / {len(raw_outages)}")

now = datetime.now()

outage_schema = StructType([
    StructField("event_id", StringType()), StructField("utility_name", StringType()),
    StructField("zip_code", StringType()), StructField("city", StringType()),
    StructField("state", StringType()), StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()), StructField("affected_customers", IntegerType()),
    StructField("outage_start", TimestampType()), StructField("outage_end", TimestampType()),
    StructField("duration_minutes", IntegerType()), StructField("reported_cause", StringType()),
    StructField("status", StringType()), StructField("data_source", StringType()),
    StructField("created_at", TimestampType()), StructField("updated_at", TimestampType()),
])

outage_rows = [(o["event_id"], o["utility_name"], o["zip_code"], o["city"], o["state"],
    o["latitude"], o["longitude"], o["affected_customers"], o["outage_start"], o["outage_end"],
    o["duration_minutes"], o["reported_cause"], o["status"], o["data_source"], now, now)
    for o in significant_outages]

outage_df = spark.createDataFrame(outage_rows, schema=outage_schema)
outage_df.write.format("delta").mode("append").saveAsTable("outage_events")
print(f"✅ Persisted {len(significant_outages)} outage events.")
display(outage_df.select("event_id","city","state","utility_name","affected_customers","duration_minutes","reported_cause"))

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 🌦️ Step 4 — Enrich with NOAA Weather Data (free)

# COMMAND ----------

def fetch_noaa_weather(lat, lon, user_agent):
    headers = {"User-Agent": user_agent, "Accept": "application/geo+json"}
    try:
        pt = requests.get(f"https://api.weather.gov/points/{round(lat,4)},{round(lon,4)}", headers=headers, timeout=10)
        pt.raise_for_status()
        st_url = pt.json()["properties"]["observationStations"]
        st = requests.get(st_url, headers=headers, timeout=10); st.raise_for_status()
        sid = st.json()["features"][0]["properties"]["stationIdentifier"]
        obs = requests.get(f"https://api.weather.gov/stations/{sid}/observations/latest", headers=headers, timeout=10)
        obs.raise_for_status(); p = obs.json()["properties"]
        tc = p.get("temperature",{}).get("value"); tf = round(tc*9/5+32,1) if tc is not None else None
        wm = p.get("windSpeed",{}).get("value"); wph = round(wm*2.237,1) if wm is not None else None
        gm = p.get("windGust",{}).get("value"); gph = round(gm*2.237,1) if gm is not None else None
        al = requests.get(f"https://api.weather.gov/alerts/active?point={round(lat,4)},{round(lon,4)}", headers=headers, timeout=10)
        ad = al.json(); ha = len(ad.get("features",[]))>0
        at = ad["features"][0]["properties"].get("event") if ha else None
        return {"temperature_f":tf,"wind_speed_mph":wph,"wind_gust_mph":gph,
                "conditions":p.get("textDescription","Unknown"),"severe_weather_alert":ha,"alert_type":at}
    except Exception as e:
        print(f"  ⚠️  NOAA error ({lat},{lon}): {e}"); return None

print("🌦️  Fetching NOAA weather...")
weather_records = []; seen = set()
for o in significant_outages:
    ck = f"{o['city']}-{o['state']}"
    if ck in seen: continue
    seen.add(ck)
    w = fetch_noaa_weather(o["latitude"], o["longitude"], config.noaa_user_agent)
    if w:
        weather_records.append({"weather_id":f"WX-{o['state']}-{uuid.uuid4().hex[:8]}","event_id":o["event_id"],
            "zip_code":o["zip_code"],"latitude":o["latitude"],"longitude":o["longitude"],
            "temperature_f":w["temperature_f"],"wind_speed_mph":w["wind_speed_mph"],
            "wind_gust_mph":w["wind_gust_mph"],"conditions":w["conditions"],
            "severe_weather_alert":w["severe_weather_alert"],"alert_type":w["alert_type"],
            "observation_time":datetime.utcnow(),"created_at":now})
        print(f"  ✓ {ck}: {w['temperature_f']}°F, wind {w['wind_speed_mph']} mph, {w['conditions']}")

weather_data_schema = StructType([
    StructField("weather_id", StringType()), StructField("event_id", StringType()),
    StructField("zip_code", StringType()), StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()), StructField("temperature_f", DoubleType()),
    StructField("wind_speed_mph", DoubleType()), StructField("wind_gust_mph", DoubleType()),
    StructField("conditions", StringType()), StructField("severe_weather_alert", BooleanType()),
    StructField("alert_type", StringType()), StructField("observation_time", TimestampType()),
    StructField("created_at", TimestampType())
])

if weather_records:
    spark.createDataFrame(weather_records, weather_data_schema).write.format("delta").mode("append").saveAsTable("weather_data")
    print(f"\n✅ Saved weather for {len(weather_records)} locations.")

weather_lookup = {}
for wr in weather_records:
    weather_lookup[wr["zip_code"]] = wr
    for o in significant_outages:
        if o["zip_code"] == wr["zip_code"]:
            weather_lookup[f"{o['city']}-{o['state']}"] = wr; break

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 🔗 Step 5 — Match Outages → Policies + Publish `outage.detected`
# MAGIC
# MAGIC When outages match policies, we publish an **`outage.detected`** event to Event Grid.
# MAGIC This is the event that triggers the **ThresholdEvaluator** Azure Function in the
# MAGIC production architecture.

# COMMAND ----------

matched_df = spark.sql("""
    SELECT o.event_id, o.utility_name, o.city AS outage_city, o.state AS outage_state,
           o.zip_code, o.affected_customers, o.outage_start, o.outage_end,
           o.duration_minutes, o.reported_cause,
           p.policy_id, p.business_name, p.business_type,
           p.threshold_minutes, p.hourly_rate, p.max_payout,
           (o.duration_minutes - p.threshold_minutes) AS excess_minutes
    FROM outage_events o
    INNER JOIN policies p ON o.zip_code = p.zip_code
    WHERE p.status = 'active' AND o.duration_minutes > p.threshold_minutes
    ORDER BY o.duration_minutes DESC
""")

matched_count = matched_df.count()
matches = matched_df.collect() if matched_count > 0 else []
print(f"🔗 {matched_count} policy matches where outage exceeded threshold.")

if matched_count > 0:
    display(matched_df)

    # ---- Publish outage.detected events to Event Grid ----
    # Group by event_id so we send one event per outage (with all affected policies)
    outage_to_policies = {}
    for m in matches:
        md = m.asDict()
        eid = md["event_id"]
        if eid not in outage_to_policies:
            outage_to_policies[eid] = {
                "event_id": eid,
                "utility_name": md["utility_name"],
                "city": md["outage_city"],
                "state": md["outage_state"],
                "zip_code": md["zip_code"],
                "affected_customers": md["affected_customers"],
                "outage_start": str(md["outage_start"]),
                "duration_minutes": md["duration_minutes"],
                "reported_cause": md["reported_cause"],
                "affected_policies": [],
            }
        outage_to_policies[eid]["affected_policies"].append(md["policy_id"])

    print(f"\n📡 Publishing {len(outage_to_policies)} 'outage.detected' events...")
    for eid, data in outage_to_policies.items():
        data["policy_count"] = len(data["affected_policies"])
        ok = eg_client.publish_event(
            event_type=config.EVT_OUTAGE_DETECTED,
            subject=f"outage/{eid}",
            data=data,
        )
        status = "✅" if ok else "⚠️"
        print(f"  {status} outage.detected → {eid} | {data['city']}, {data['state']} | {data['policy_count']} policies")

    print(f"\n✅ Event Grid: {len(outage_to_policies)} outage.detected events published.")
else:
    print("   ℹ️  No matches — try 'severe_weather' or 'winter_storm' scenario.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 🤖 Step 6 — AI Claim Validation + Publish `claim.approved` / `claim.denied`
# MAGIC
# MAGIC After validating each claim (via Foundry Agent or rule-based engine), we publish
# MAGIC either a **`claim.approved`** or **`claim.denied`** event. In the production
# MAGIC architecture, `claim.approved` triggers the **PayoutProcessor** Azure Function.

# COMMAND ----------

def calculate_weather_factor(weather):
    if not weather: return 1.0, "unknown"
    wind = weather.get("wind_speed_mph") or 0; gust = weather.get("wind_gust_mph") or 0
    ha = weather.get("severe_weather_alert", False); at = str(weather.get("alert_type",""))
    mx = max(wind, gust)
    if ha and ("Severe" in at or "Hurricane" in at or mx>55): return 1.5, "severe"
    elif ha or mx>40: return 1.2, "high"
    elif mx>25: return 1.1, "medium"
    return 1.0, "low"

def rule_based_validation(policy, outage, weather=None):
    dur = outage["duration_minutes"]; thr = policy["threshold_minutes"]; excess = dur - thr
    if excess <= 0:
        return {"decision":"denied","confidence_score":0.95,"payout_amount":0.0,
                "reasoning":f"Duration ({dur} min) < threshold ({thr} min).",
                "severity_assessment":"none","weather_factor":1.0,"fraud_signals":[],"evidence":[]}
    wf, sev = calculate_weather_factor(weather)
    raw = (excess/60.0) * policy["hourly_rate"] * wf
    final = min(raw, policy["max_payout"])
    fraud = ["planned_maintenance_not_covered"] if outage.get("reported_cause") == "planned_maintenance" else []
    conf = min(0.92 + (0.03 if weather else 0) + (0.02 if outage.get("affected_customers",0)>5000 else 0), 0.99)
    dec = "denied" if outage.get("reported_cause") == "planned_maintenance" else "approved"
    return {"decision":dec,"confidence_score":round(conf,4),"payout_amount":round(final,2),
            "reasoning":f"Outage {dur} min, threshold {thr} min, excess {excess} min. Weather: {sev} ({wf}x). Payout: ${final:,.2f}.",
            "severity_assessment":sev,"weather_factor":wf,"fraud_signals":fraud,
            "evidence":[{"type":"duration","value":f"{dur} min"},{"type":"threshold","value":f"{thr} min"},
                        {"type":"weather","value":f"{sev} ({wf}x)"},{"type":"payout","value":f"${final:,.2f}"}]}

def foundry_agent_validation(policy, outage, weather=None):
    try:
        from azure.ai.agents import AgentsClient
        from azure.identity import DefaultAzureCredential # <--- One day this will work with the Workspace Identity from within a Fabric notebook
    except ImportError:
        return rule_based_validation(policy, outage, weather)

    if not config.foundry_endpoint or not config.foundry_agent_id:
        return rule_based_validation(policy, outage, weather)

    try:
        agents_client = AgentsClient(
            endpoint=config.foundry_endpoint,  # https://<resource>.services.ai.azure.com/api/projects/<project>
            credential=DefaultAzureCredential() # <--- One day this will work with the Workspace Identity from within a Fabric notebook
        )

        user_message = f"""POLICY: {json.dumps(policy, default=str)}
                           OUTAGE: {json.dumps(outage, default=str)}
                           WEATHER: {json.dumps(weather, default=str) if weather else "N/A"}"""

        # Use an existing agent by Name, or create one on the fly
        claims_validator_agent = agents_client.get_agent(config.foundry_agent_id)

        # Create a thread, post the message, and run
        thread = agents_client.threads.create()
        agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message,
        )
        run = agents_client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=claims_validator_agent.id,
        )

        # Retrieve the assistant's response
        messages = agents_client.messages.list(thread_id=thread.id)
        # Messages come newest-first; grab the last assistant message
        txt = None
        for msg in messages:
            if msg.role == "assistant":
                for block in msg.content:
                    if hasattr(block, "text"):
                        txt = block.text.value
                        break
                if txt:
                    break

        if not txt:
            print("  ⚠️  Foundry agent returned no response")
            return rule_based_validation(policy, outage, weather)

        # Clean markdown fences if present
        txt = txt.strip()
        if txt.startswith("```"):
            txt = txt.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        print(f" Response from {claims_validator_agent.name}: {txt}")

        # Cleanup: delete thread (and agent if we created it ad-hoc)
        # client.agents.threads.delete(thread_id=thread.id)
        if not (hasattr(config, "foundry_agent_id") and config.foundry_agent_id):
            claims_validator_agent.delete_agent(agent_id=claims_validator_agent.id)

        return json.loads(txt)

    except Exception as e:
        print(f"  ⚠️  Foundry agent error: {e}")
        return rule_based_validation(policy, outage, weather)

# ---- Validate all matched claims ----
print(f"🤖 Validating {len(matches)} claims...")
print(f"   Method: {'Foundry Agent' if config.foundry_endpoint else 'Rule-Based Engine'}\n")

claim_records = []
for i, match in enumerate(matches, 1):
    m = match.asDict()
    pd_dict = {"policy_id":m["policy_id"],"business_name":m["business_name"],
               "threshold_minutes":m["threshold_minutes"],"hourly_rate":m["hourly_rate"],"max_payout":m["max_payout"]}
    od_dict = {"event_id":m["event_id"],"utility_name":m["utility_name"],"duration_minutes":m["duration_minutes"],
               "affected_customers":m["affected_customers"],"reported_cause":m["reported_cause"],
               "outage_start":str(m["outage_start"]),"status":"resolved"}
    wd = weather_lookup.get(m["zip_code"]) or weather_lookup.get(f"{m['outage_city']}-{m['outage_state']}")

    result = foundry_agent_validation(pd_dict, od_dict, wd)

    cid = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    ct = datetime.utcnow()
    claim = {
        "claim_id":cid, "policy_id":m["policy_id"], "outage_event_id":m["event_id"],
        "status":result["decision"], "filed_at":ct,
        "validated_at":ct+timedelta(seconds=random.randint(5,30)),
        "approved_at":(ct+timedelta(seconds=random.randint(10,45))) if result["decision"]=="approved" else None,
        "denied_at":(ct+timedelta(seconds=10)) if result["decision"]=="denied" else None,
        "denial_reason":result["reasoning"] if result["decision"]=="denied" else None,
        "payout_amount":result["payout_amount"], "ai_confidence_score":result["confidence_score"],
        "ai_reasoning":result["reasoning"], "fraud_flags":json.dumps(result.get("fraud_signals",[])),
        "weather_factor":result.get("weather_factor",1.0), "severity_assessment":result.get("severity_assessment","unknown"),
        "created_at":ct, "updated_at":ct,
    }
    claim_records.append(claim)

    icon = "✅" if result["decision"]=="approved" else "❌"
    print(f"  {i}. {icon} {m['business_name']} ({m['policy_id']})")
    print(f"     Outage: {m['duration_minutes']} min (threshold: {m['threshold_minutes']})")
    print(f"     Decision: {result['decision'].upper()} | Confidence: {result['confidence_score']:.1%} | Payout: ${result['payout_amount']:,.2f}")

    # ---- Publish claim.approved or claim.denied ----
    evt_type = config.EVT_CLAIM_APPROVED if result["decision"] == "approved" else config.EVT_CLAIM_DENIED
    eg_client.publish_event(
        event_type=evt_type,
        subject=f"claim/{cid}",
        data={
            "claim_id": cid,
            "policy_id": m["policy_id"],
            "outage_event_id": m["event_id"],
            "status": result["decision"],
            "payout_amount": result["payout_amount"],
            "ai_confidence_score": result["confidence_score"],
            "severity_assessment": result.get("severity_assessment"),
            "weather_factor": result.get("weather_factor", 1.0),
            "business_name": m["business_name"],
            "city": m["outage_city"],
            "state": m["outage_state"]
        },
    )
    print(f"     📡 Published: {evt_type}")
    print()

if claim_records:
    claim_schema = StructType([
        StructField("claim_id", StringType()),
        StructField("policy_id", StringType()), 
        StructField("outage_event_id", StringType()),
        StructField("status", StringType()), 
        StructField("filed_at", TimestampType()), 
        StructField("validated_at", TimestampType()),
        StructField("approved_at", TimestampType()), 
        StructField("denied_at", TimestampType()), 
        StructField("denial_reason", StringType()),
        StructField("payout_amount", DoubleType()), 
        StructField("ai_confidence_score", DoubleType()), 
        StructField("ai_reasoning", StringType()),
        StructField("fraud_flags", StringType()), 
        StructField("weather_factor", DoubleType()), 
        StructField("severity_assessment", StringType()),
        StructField("created_at", TimestampType()), 
        StructField("updated_at", TimestampType())

    ])
    spark.createDataFrame(claim_records, claim_schema).write.format("delta").mode("append").saveAsTable("claims")
    approved_count = sum(1 for c in claim_records if c["status"]=="approved")
    denied_count = len(claim_records) - approved_count
    print(f"✅ Persisted {len(claim_records)} claims ({approved_count} approved, {denied_count} denied).")
    print(f"📡 Published {len(claim_records)} claim events to Event Grid.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 💰 Step 7 — Process Payouts + Publish `payout.processed`
# MAGIC
# MAGIC For each approved claim, we create a payout record and publish a
# MAGIC **`payout.processed`** event to Event Grid. In production, this event can
# MAGIC trigger notifications (email, SMS) via Logic Apps or additional Functions.

# COMMAND ----------

approved_claims = [c for c in claim_records if c["status"] == "approved"]
print(f"💰 Processing {len(approved_claims)} approved payouts...\n")

payout_records = []
total_payout = 0.0

for claim in approved_claims:
    pt = datetime.utcnow()
    payout = {
        "payout_id": f"PAY-{uuid.uuid4().hex[:8].upper()}",
        "claim_id": claim["claim_id"],
        "policy_id": claim["policy_id"],
        "amount": claim["payout_amount"],
        "status": "completed",
        "initiated_at": pt,
        "completed_at": pt + timedelta(seconds=random.randint(2, 15)),
        "transaction_id": f"TXN-{uuid.uuid4().hex[:12].upper()}",
        "payment_method": "ACH",
        "created_at": pt,
    }
    payout_records.append(payout)
    total_payout += claim["payout_amount"]

    print(f"  💳 {payout['payout_id']} → {claim['policy_id']} | ${claim['payout_amount']:,.2f} | TXN: {payout['transaction_id']}")

    # ---- Publish payout.processed ----
    eg_client.publish_event(
        event_type=config.EVT_PAYOUT_PROCESSED,
        subject=f"payout/{payout['payout_id']}",
        data={
            "payout_id": payout["payout_id"],
            "claim_id": claim["claim_id"],
            "policy_id": claim["policy_id"],
            "amount": claim["payout_amount"],
            "transaction_id": payout["transaction_id"],
            "payment_method": "ACH",
            "status": "completed",
            "initiated_at": str(payout["initiated_at"]),
            "completed_at": str(payout["completed_at"]),
        },
    )
    print(f"     📡 Published: payout.processed")

if payout_records:
    spark.createDataFrame(payout_records).write.format("delta").mode("append").saveAsTable("payouts")
    print(f"\n✅ {len(payout_records)} payouts completed. Total: ${total_payout:,.2f}")
    print(f"📡 Published {len(payout_records)} payout.processed events.")
else:
    print("ℹ️  No payouts to process.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 📋 Step 8 — Persist Event Audit Log & Dashboard Summary
# MAGIC
# MAGIC Every event (published or local-only) is stored in the `event_audit_log` table
# MAGIC for full traceability and compliance.

# COMMAND ----------

# ---- Persist audit log to Delta ----
now = datetime.now()
if eg_client.audit_log:
    audit_rows = [{**a, "created_at": now} for a in eg_client.audit_log]
    audit_rows_schema = StructType([
        StructField("sequence", IntegerType()),
        StructField("event_id", StringType()), 
        StructField("event_type", StringType()),
        StructField("subject", StringType()), 
        StructField("event_time", StringType()),
        StructField("data_summary", StringType()), 
        StructField("status", StringType()), 
        StructField("error", StringType()),
        StructField("created_at", TimestampType())
    ])
    spark.createDataFrame(audit_rows, audit_rows_schema).write.format("delta").mode("append").saveAsTable("event_audit_log")
    print(f"✅ Persisted {len(audit_rows)} event audit records.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Event Audit Log

# COMMAND ----------

display(spark.sql("""
    SELECT sequence, event_type, subject, status, event_time, error,
           SUBSTRING(data_summary, 1, 120) AS data_preview
    FROM event_audit_log
    ORDER BY sequence
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Event Grid Summary by Type

# COMMAND ----------

display(spark.sql("""
    SELECT
        event_type,
        status,
        COUNT(*) AS event_count
    FROM event_audit_log
    WHERE event_type != 'test.connection'
    GROUP BY event_type, status
    ORDER BY event_type, status
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Execution Summary

# COMMAND ----------

print("=" * 70)
print("📊  PARAMETRIC INSURANCE DEMO — EXECUTION SUMMARY")
print("=" * 70)
print(f"  Timestamp:           {datetime.utcnow().isoformat()}Z")
print(f"  Scenario:            {config.scenario_type}")
print(f"  Validation Method:   {'Foundry Agent' if config.foundry_endpoint else 'Rule-Based Engine'}")
print(f"  Event Grid:          {'ENABLED' if EVENTGRID_ENABLED else 'LOCAL-ONLY'}")
print()
print(f"  ⚡ Outages Generated:   {len(raw_outages)}")
print(f"  ⚡ Significant Outages:  {len(significant_outages)}")
print(f"  🌦️  Weather Records:     {len(weather_records)}")
print(f"  🔗 Policy Matches:      {matched_count}")
print(f"  🤖 Claims Filed:        {len(claim_records)}")
print(f"  ✅ Claims Approved:     {len(approved_claims)}")
print(f"  ❌ Claims Denied:       {len(claim_records) - len(approved_claims)}")
print(f"  💰 Payouts Processed:   {len(payout_records)}")
print(f"  💰 Total Disbursed:     ${total_payout:,.2f}")
print()
total_events = len([a for a in eg_client.audit_log if a["event_type"] != "test.connection"])
published = len([a for a in eg_client.audit_log if a["status"] == "published"])
local = len([a for a in eg_client.audit_log if a["status"] == "local_only"])
failed = len([a for a in eg_client.audit_log if a["status"] == "failed"])
print(f"  📡 Events Total:        {total_events}")
print(f"  📡 Events Published:    {published}")
print(f"  📝 Events Local-Only:   {local}")
if failed: print(f"  ⚠️  Events Failed:       {failed}")
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Claims Breakdown

# COMMAND ----------

if claim_records:
    display(spark.sql("""
        SELECT c.claim_id, c.policy_id, p.business_name, p.city, c.status,
               c.payout_amount, c.ai_confidence_score, c.severity_assessment, c.weather_factor
        FROM claims c JOIN policies p ON c.policy_id = p.policy_id ORDER BY c.payout_amount DESC
    """))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Payout Summary by City

# COMMAND ----------

if payout_records:
    display(spark.sql("""
        SELECT p.city, p.state, COUNT(pay.payout_id) AS payouts,
               SUM(pay.amount) AS total, AVG(pay.amount) AS avg_payout
        FROM payouts pay JOIN claims c ON pay.claim_id=c.claim_id
        JOIN policies p ON c.policy_id=p.policy_id
        GROUP BY p.city, p.state ORDER BY total DESC
    """))

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 🏁 Demo Complete!
# MAGIC
# MAGIC ### Event-Driven Architecture
# MAGIC
# MAGIC ```
# MAGIC ┌──────────┐    outage.detected     ┌─────────────────────┐
# MAGIC │  PRESTO  │ ──────────────────────► │ ThresholdEvaluator  │
# MAGIC │ + Fabric │                         │  (Azure Function)   │
# MAGIC └──────────┘                         └────────┬────────────┘
# MAGIC                                               │
# MAGIC                                    claim.approved / claim.denied
# MAGIC                                               │
# MAGIC                                               ▼
# MAGIC                                      ┌────────────────────┐
# MAGIC                                      │  PayoutProcessor   │
# MAGIC                                      │  (Azure Function)  │
# MAGIC                                      └────────┬───────────┘
# MAGIC                                               │
# MAGIC                                      payout.processed
# MAGIC                                               │
# MAGIC                                               ▼
# MAGIC                                      ┌────────────────────┐
# MAGIC                                      │  Notifications     │
# MAGIC                                      │  (Logic App/Email) │
# MAGIC                                      └────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC ### Event Grid Subscriptions (configured via azure-setup.sh)
# MAGIC
# MAGIC | Event Type | Subscriber | Action |
# MAGIC |-----------|-----------|--------|
# MAGIC | `outage.detected` | ThresholdEvaluator Function | Evaluate thresholds, call AI agent |
# MAGIC | `claim.approved` | PayoutProcessor Function | Process payment |
# MAGIC | `claim.denied` | (optional) Audit Logger | Record denial |
# MAGIC | `payout.processed` | (optional) Logic App | Send email/SMS notification |
# MAGIC
# MAGIC ### Next Steps
# MAGIC - **Wire Azure Functions:** Deploy the ThresholdEvaluator and PayoutProcessor functions
# MAGIC - **Fabric Data Agent:** Create a natural-language agent on top of these Delta tables
# MAGIC - **Foundry Agent:** Deploy the claims validator as a standalone Foundry Agent
# MAGIC - **Power BI:** Connect a dashboard for real-time monitoring
# MAGIC - **Logic Apps:** Add email/SMS notifications on `payout.processed`

# COMMAND ----------

# Return for pipeline orchestration
if FABRIC_ENV:
    mssparkutils.notebook.exit(json.dumps({
        "status": "success",
        "scenario": config.scenario_type,
        "event_grid_enabled": EVENTGRID_ENABLED,
        "outages_generated": len(raw_outages),
        "significant_outages": len(significant_outages),
        "policy_matches": matched_count,
        "claims_filed": len(claim_records),
        "claims_approved": len(approved_claims),
        "payouts_processed": len(payout_records),
        "total_disbursed": total_payout,
        "events_published": published,
        "events_failed": failed,
        "timestamp": datetime.utcnow().isoformat(),
    }))
else:
    print("\n🏁 Notebook execution complete.")
