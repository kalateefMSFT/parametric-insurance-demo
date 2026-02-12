# Deployment Guide

Complete step-by-step guide to deploy the parametric insurance demo with all optional integrations.

## Table of Contents

1. [Fabric-Only Deployment (10 min)](#1-fabric-only-deployment)
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

### 1.3 Import the Notebook

1. Click **Import** → **Notebook**
2. You have options for the notebook: 
    - `fabric/notebooks/parametric_insurance_unified_demo.ipynb` targets the Classic Microsoft Foundry Agents that uses Threads
    - `fabric/notebooks/parametric_insurance_unified_demo_new.ipynb` targets the New Microsoft Foundry Agents that uses Responses

3. Upload: Chosen notebook to the `ParametricInsurance` workspace
4. Open the notebook
5. Click **Lakehouse** in the left panel → attach to `parametric_insurance_lakehouse`

### 1.4 Run the Demo

Click **Run All**. The notebook creates all tables, loads policies, simulates outages, fetches weather, validates claims, and processes payouts.

At this point Event Grid events are logged locally (status: `local_only`). The demo is fully functional without Azure.

---

## 2. Add Event Grid

Event Grid allows the notebook to publish events that trigger downstream Azure Functions, Logic Apps, or webhooks.

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

### 2.2 Configure the Notebook

Set these values in the `DemoConfig` class (Step 0 of the notebook):

```python
eventgrid_topic_endpoint = "https://<topic-name>.<region>.eventgrid.azure.net/api/events"
eventgrid_topic_key = "<your-key-from-setup-output>"
```

Or set as environment variables:
```bash
export EVENTGRID_TOPIC_ENDPOINT="https://..."
export EVENTGRID_KEY="..."
```

Or pass as Fabric pipeline parameters (the notebook reads them via `mssparkutils.widgets`).

### 2.3 Verify

Re-run the notebook. Step 0b will publish a test event and confirm:
```
✅ Event Grid connection verified — test event published successfully!
```

Events in the audit log will now show status `published` instead of `local_only`.

---

## 3. Add Azure Functions

The original v1 implementation includes 4 Azure Functions that subscribe to Event Grid events. These are optional — the notebook handles all logic internally — but they demonstrate a production event-driven architecture.

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

The notebook still runs the full pipeline internally (for demo visibility), and the Functions run in parallel for event-driven production processing.

---

## 4. Add Foundry AI Agent

### Option A: Microsoft Foundry Portal

1. Go to [Microsoft Foundry](https://foundry.microsoft.com/)
2. Create an agent named `ClaimsValidator`
3. Upload `archive/v1/foundry/agents/claims_validator_agent.py` as reference
4. Configure the agent with the validation prompt
5. Use the agent's endpoint and key in the notebook config

### Option C: Rule-Based Fallback (Default)

Leave `foundry_endpoint` and `foundry_agent` blank. The notebook automatically uses a deterministic rule-based engine that produces the same output schema (confidence scores, severity assessment, weather factors, fraud detection).

---

## 5. Add Power BI Dashboard

See [powerbi/POWERBI_SETUP.md](../powerbi/POWERBI_SETUP.md) for the complete guide.

Quick version:
1. Open Power BI Desktop
2. **Get Data** → connect to your Fabric Lakehouse
3. Import tables: policies, claims, payouts, outage_events, weather_data, event_audit_log
4. Create relationships and DAX measures
5. Build 5 dashboard pages (Overview, Claims, Outages, Policies, AI Insights)

---

## 6. Schedule the Pipeline

To run the notebook on a recurring schedule:

1. In your Fabric workspace, click **New** → **Data pipeline**
2. Name: `Parametric Insurance Pipeline`
3. Add a **Notebook** activity → select the unified demo notebook
4. Set parameters (optional):
   - `eventgrid_endpoint`: your Event Grid endpoint
   - `eventgrid_key`: your Event Grid key
5. Add a **Schedule** trigger → every 5 minutes (or as desired)
6. Publish

---

## 7. Cost Management

### Estimated Monthly Costs

| Component | Demo Usage | Production |
|-----------|-----------|------------|
| Fabric (trial) | $0 | $700/mo (F2) |
| Event Grid | $0.60 | $5 |
| Azure Functions | $0–$5 | $15 |
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

NOAA occasionally rate-limits or has downtime. The notebook catches all errors and continues. Claims still process with default weather factors (1.0x).

### Event Grid Connection Failed

- Verify the endpoint URL format: `https://<topic-name>.<region>.eventgrid.azure.net/api/events`
- Verify the SAS key is correct (use `key1` from `az eventgrid topic key list`)
- The notebook auto-falls back to local-only mode

### Fabric Notebook Won't Attach Lakehouse

- Ensure the Lakehouse is in the same workspace as the notebook
- Try detaching and re-attaching via the Lakehouse icon in the left panel

### Azure Functions Not Triggering

```bash
# Check function status
az functionapp show --name $FUNCTION_APP --resource-group parametric-insurance-rg --query state

# Check subscriptions
az eventgrid event-subscription list --source-resource-id $TOPIC_ID --output table

# Stream logs
az functionapp log tail --name $FUNCTION_APP --resource-group parametric-insurance-rg
```
