# Deployment Guide

Complete step-by-step guide to deploy the parametric insurance demo with all optional integrations.

## Table of Contents

1. [Fabric-Only Deployment (15 min)](#1-fabric-only-deployment)
2. [Add Event Grid (10 min)](#2-add-event-grid)
3. [Add Azure Functions (15 min)](#3-add-azure-functions)
4. [Add Foundry AI Agent (5 min)](#4-add-foundry-ai-agent)
5. [Add Power BI Dashboard (20 min)](#5-add-power-bi-dashboard)
6. [Schedule the Pipeline (5 min)](#6-schedule-the-pipeline)
7. [Cost Management](#7-cost-management)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Fabric-Only Deployment

This is the minimum viable demo — no Azure subscription required.

### Prerequisites

- Microsoft Fabric workspace (free 60-day trial at [fabric.microsoft.com](https://app.fabric.microsoft.com/))

### 1.1 Create Workspace

1. Go to [Microsoft Fabric](https://app.fabric.microsoft.com/)
2. Click **Workspaces** → **New Workspace**
3. Name: `ParametricInsurance`
4. Select license tier (F2+ recommended, or free trial)

### 1.2 Create Lakehouse

1. In workspace, click **New** → **Lakehouse**
2. Name: `parametric_insurance_lakehouse`
3. Wait ~30 seconds for provisioning

### 1.3 Import the Notebooks

1. Click **Import** → **Notebook**
2. Upload all four notebooks from `fabric/notebooks/`:

| Notebook | Purpose | Run Order |
|----------|---------|-----------|
| `schema_load_with_policies.ipynb` | Creates Delta tables and loads 250 sample policies across 40 US cities | **1st** (run once) |
| `parametric_insurance_unified_demo_new.ipynb` | Full claims pipeline: outage simulation, weather enrichment, AI validation, payouts | **2nd** |
| `weather_alert_policy_impact.ipynb` | Real-time weather alert monitoring with policy geo-matching | **3rd** (can run on a schedule) |
| `weather_impact_email_notifier.ipynb` | AI-generated email notifications to impacted policyholders | **4th** (after weather impacts are detected) |

3. Open each notebook and click **Lakehouse** in the left panel → attach to `parametric_insurance_lakehouse`

### 1.4 Run the Notebooks

Run the notebooks **in order**. Each builds on the data produced by the previous one.

#### Notebook 1 — Schema & Policies

Run `schema_load_with_policies.ipynb` first. Click **Run All**. This notebook:

- Drops and recreates all non-policy tables (outage_events, weather_data, claims, payouts, outage_raw, event_audit_log)
- Creates the `policies` table (if it doesn't already exist)
- Loads 250 sample policies across 40 US cities with deduplication
- Displays a verification summary

This notebook is safe to re-run — it preserves existing policies and resets processing tables.

#### Notebook 2 — Claims Pipeline

Run `parametric_insurance_unified_demo_new.ipynb`. Click **Run All**. This notebook:

- Simulates power outages using the embedded PRESTO engine
- Fetches live weather from NOAA (free, no API key)
- Matches outages to policies using Spark SQL
- Validates claims via Foundry AI Agent (New Foundry experience with Responses API) or rule-based fallback
- Processes payouts for approved claims
- Publishes events to Event Grid at every stage (or logs locally)
- Displays a full analytics dashboard and event audit log

At this point Event Grid events are logged locally (status: `local_only`) if Event Grid is not configured. The demo is fully functional without Azure.

#### Notebook 3 — Weather Alert Monitor

Run `weather_alert_policy_impact.ipynb`. Click **Run All**. This notebook:

- Polls NOAA for active severe weather alerts across the US
- Geo-matches alerts to policyholder locations using the Haversine formula (default 50 km radius)
- Computes a risk score per match (45% severity + 35% urgency + 20% proximity)
- Deduplicates against recent matches (6-hour window) to avoid re-triggering
- Publishes `policy.weather.impact` events to Event Grid
- Persists impact records to the `weather_impact_events` Delta table

This notebook is designed for scheduled execution (e.g., every 15 minutes).

#### Notebook 4 — Email Notifier

Run `weather_impact_email_notifier.ipynb`. Click **Run All**. This notebook:

- Reads unnotified impact events from `weather_impact_events` (filtered by status and minimum risk score)
- Enriches each impact with policy details via Spark SQL
- Calls a Foundry Orchestrator Agent (LLM-only, using the Responses API) to compose professional emails, or falls back to a built-in template
- Persists email records to the `email_notifications` Delta table
- Optionally dispatches emails via a webhook (Logic App / Power Automate)
- Marks source impact records as notified

---

## 2. Add Event Grid

Event Grid allows the notebooks to publish events that trigger downstream Azure Functions, Logic Apps, or webhooks.

### Prerequisites

- Azure subscription (Owner or Contributor role)
- Azure CLI v2.50+ installed

### 2.1 Run Setup Script

```bash
# Login to Azure
az login
az account set --subscription "<your-subscription-id>"

# Create Event Grid Topic + supporting resources
cd setup
./azure-setup.sh      # Linux/Mac
# or
.\azure-setup.ps1     # Windows PowerShell
```

The script creates:
- Resource Group: `parametric-insurance-rg`
- Event Grid Topic: `parametric-insurance-events`
- Storage Account, Application Insights, Function App

It outputs the **endpoint** and **key** and writes them to `.env`.

### 2.2 Configure the Notebooks

Set these values in the config class (Step 0) of each notebook that publishes events:

**In `parametric_insurance_unified_demo_new.ipynb` (`DemoConfig`):**
```python
eventgrid_topic_endpoint = "https://<topic-name>.<region>.eventgrid.azure.net/api/events"
eventgrid_topic_key = "<your-key-from-setup-output>"
```

**In `weather_alert_policy_impact.ipynb` (`AlertMonitorConfig`):**
```python
eventgrid_topic_endpoint = "https://<topic-name>.<region>.eventgrid.azure.net/api/events"
eventgrid_topic_key = "<your-key-from-setup-output>"
```

Or set as environment variables:
```bash
export EVENTGRID_TOPIC_ENDPOINT="https://..."
export EVENTGRID_KEY="..."
```

Or pass as Fabric pipeline parameters (the notebooks read them via `mssparkutils.widgets`).

### 2.3 Verify

Re-run the claims pipeline notebook. Step 0b will publish a test event and confirm:
```
Event Grid connection verified — test event published successfully!
```

Events in the audit log will now show status `published` instead of `local_only`.

---

## 3. Add Azure Functions

The original v1 implementation includes 4 Azure Functions that subscribe to Event Grid events. These are optional — the notebooks handle all logic internally — but they demonstrate a production event-driven architecture.

### 3.1 Deploy Functions

The function source code is in `archive/v1/functions/`.

```bash
cd archive/v1/functions

# Get function app name from .env
FUNCTION_APP=$(grep FUNCTION_APP_NAME ../../.env | cut -d '=' -f2)

# Deploy
func azure functionapp publish $FUNCTION_APP
```

### 3.2 Create Event Grid Subscriptions

The setup script (`azure-setup.sh`) creates these automatically, but you can also create them manually:

```bash
TOPIC_ID="/subscriptions/<sub-id>/resourceGroups/parametric-insurance-rg/providers/Microsoft.EventGrid/topics/parametric-insurance-events"
FUNC_ID=$(az functionapp show --name $FUNCTION_APP --resource-group parametric-insurance-rg --query id -o tsv)

# ThresholdEvaluator listens to outage.detected
az eventgrid event-subscription create \
  --name threshold-evaluator \
  --source-resource-id $TOPIC_ID \
  --endpoint "$FUNC_ID/functions/ThresholdEvaluator" \
  --endpoint-type azurefunction \
  --included-event-types "outage.detected"

# PayoutProcessor listens to claim.approved
az eventgrid event-subscription create \
  --name payout-processor \
  --source-resource-id $TOPIC_ID \
  --endpoint "$FUNC_ID/functions/PayoutProcessor" \
  --endpoint-type azurefunction \
  --included-event-types "claim.approved"
```

### 3.3 Architecture with Functions

When Functions are deployed, the flow becomes:

```
Notebook publishes outage.detected
       │
       ▼
ThresholdEvaluator (Azure Function)
  → Re-validates threshold
  → Calls Foundry AI Agent
  → Publishes claim.approved
       │
       ▼
PayoutProcessor (Azure Function)
  → Processes payment
  → Publishes payout.processed
```

The notebooks still run the full pipeline internally (for demo visibility), and the Functions run in parallel for event-driven production processing.

---

## 4. Add Foundry AI Agent

The demo uses two types of Foundry Agents:

### 4a. Claims Validator Agent (for the claims pipeline notebook)

1. Go to [Microsoft Foundry](https://foundry.microsoft.com/)
2. Create an agent named `ClaimsValidator`
3. Upload `archive/v1/foundry/agents/claims_validator_agent.py` as reference
4. Configure the agent with the validation prompt
5. Set `foundry_endpoint` and `foundry_agent` in `parametric_insurance_unified_demo_new.ipynb`

**Note:** This notebook uses the **New Foundry Agent experience** (Responses API). Ensure you create the agent with the New experience, not the Classic (Threads-based) experience.

### 4b. Orchestrator Agent (for the email notifier notebook)

1. In Microsoft Foundry, create an LLM-only agent (no tools/actions)
2. Name it according to your `orchestrator_agent` config value
3. Set `foundry_endpoint` and `orchestrator_agent` in `weather_impact_email_notifier.ipynb`

### 4c. Rule-Based Fallback (Default)

Leave Foundry fields blank in any notebook. Each notebook automatically falls back to a built-in deterministic engine:
- The claims pipeline uses a rule-based validator (confidence scores, severity assessment, weather factors, fraud detection)
- The email notifier uses a professional template engine

---

## 5. Add Power BI Dashboard

See [powerbi/POWERBI_SETUP.md](../powerbi/POWERBI_SETUP.md) for the complete guide.

Quick version:
1. Open Power BI Desktop
2. **Get Data** → connect to your Fabric Lakehouse
3. Import tables: policies, claims, payouts, outage_events, weather_data, event_audit_log, weather_impact_events, email_notifications
4. Create relationships and DAX measures
5. Build 5 dashboard pages (Overview, Claims, Outages, Policies, AI Insights)

---

## 6. Schedule the Pipeline

To run the notebooks on a recurring schedule:

### Option A: Data Pipeline (Sequential)

1. In your Fabric workspace, click **New** → **Data pipeline**
2. Name: `Parametric Insurance Pipeline`
3. Add notebook activities in sequence:
   - **Activity 1**: `schema_load_with_policies` (only needed on first run or data reset)
   - **Activity 2**: `parametric_insurance_unified_demo_new`
   - **Activity 3**: `weather_alert_policy_impact`
   - **Activity 4**: `weather_impact_email_notifier`
4. Set parameters (optional):
   - `eventgrid_endpoint`: your Event Grid endpoint
   - `eventgrid_key`: your Event Grid key
5. Add a **Schedule** trigger → as desired (e.g., daily)
6. Publish

### Option B: Separate Schedules

- **Claims pipeline**: Schedule as needed for demo runs
- **Weather alert monitor**: Schedule every 15 minutes for continuous monitoring
- **Email notifier**: Schedule every 30 minutes (or trigger after weather monitor completes)

---

## 7. Cost Management

### Estimated Monthly Costs

| Component | Demo Usage | Production |
|-----------|-----------|------------|
| Fabric (trial) | $0 | $700/mo (F2) |
| Event Grid | $0.60 | $5 |
| Azure Functions | $0-$5 | $15 |
| Azure OpenAI | $5 | $50 |
| Application Insights | $2 | $10 |
| **Total** | **~$8** | **~$85** |

### Pause When Not Demoing

```bash
# Stop functions
az functionapp stop --name $FUNCTION_APP --resource-group parametric-insurance-rg

# Resume
az functionapp start --name $FUNCTION_APP --resource-group parametric-insurance-rg
```

### Delete Everything

```bash
az group delete --name parametric-insurance-rg --yes --no-wait
```

---

## 8. Troubleshooting

### No Policy Matches

The `normal_day` scenario generates short outages. Use `severe_weather` or `winter_storm` for longer durations that exceed policy thresholds.

### NOAA Weather Errors

NOAA occasionally rate-limits or has downtime. The notebooks catch all errors and continue. Claims still process with default weather factors (1.0x). Weather alerts continue with available data.

### Event Grid Connection Failed

- Verify the endpoint URL format: `https://<topic-name>.<region>.eventgrid.azure.net/api/events`
- Verify the SAS key is correct (use `key1` from `az eventgrid topic key list`)
- All notebooks auto-fall back to local-only mode

### Fabric Notebook Won't Attach Lakehouse

- Ensure the Lakehouse is in the same workspace as the notebook
- Try detaching and re-attaching via the Lakehouse icon in the left panel

### No Weather Alerts Found

The weather alert monitor depends on active NOAA alerts. If no severe alerts are active at the time of execution, the notebook will complete with zero impacts. Try lowering `min_severity` to `"Moderate"` for testing.

### Email Notifier Shows No Pending Impacts

The email notifier reads from `weather_impact_events` where `impact_status = 'pending_notification'`. Ensure `weather_alert_policy_impact.ipynb` has run first and produced matching results.

### Azure Functions Not Triggering

```bash
# Check function status
az functionapp show --name $FUNCTION_APP --resource-group parametric-insurance-rg --query state

# Check subscriptions
az eventgrid event-subscription list --source-resource-id $TOPIC_ID --output table

# Stream logs
az functionapp log tail --name $FUNCTION_APP --resource-group parametric-insurance-rg
```
