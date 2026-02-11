# Quick Start — 10 Minutes to Running Demo

## What You Need

- A Microsoft Fabric workspace (free 60-day trial at [fabric.microsoft.com](https://app.fabric.microsoft.com/))
- That's it. Everything else is embedded in the notebook.

## Step 1: Create a Lakehouse (2 min)

1. Open your Fabric workspace
2. Click **New** → **Lakehouse**
3. Name it `parametric_insurance_lakehouse`
4. Wait for provisioning (~30 seconds)

## Step 2: Import the Notebook (2 min)

1. In the workspace, click **Import** → **Notebook**
2. Upload: `fabric/notebooks/parametric_insurance_unified_demo.py`
3. Open the notebook
4. Click the **Lakehouse** icon in the left panel → attach to `parametric_insurance_lakehouse`

## Step 3: Run It (5 min)

Click **Run All** and watch the pipeline execute:

| Cell | What Happens |
|------|-------------|
| Step 0 | Loads configuration, detects Fabric environment |
| Step 1 | Creates 7 Delta tables in your Lakehouse |
| Step 2 | Loads 11 sample insurance policies across 5 US cities |
| Step 3 | PRESTO generates realistic power outage events |
| Step 4 | NOAA Weather API enriches each outage with live weather |
| Step 5 | Matches outages to policies, publishes `outage.detected` events |
| Step 6 | AI validates each claim, publishes `claim.approved`/`claim.denied` |
| Step 7 | Processes payouts, publishes `payout.processed` |
| Step 8 | Displays analytics dashboard + event audit log |

## Step 4: See the Results

The final cells display:

- **Execution Summary** — counts of outages, claims, payouts, total disbursed
- **Claims Breakdown** — each claim with business name, decision, payout, AI confidence
- **Payout Summary by City** — aggregated payouts per metro area
- **Event Audit Log** — every Event Grid event (or local log) with status

## Changing the Scenario

Edit `config.scenario_type` in Step 0 and re-run:

```python
config.scenario_type = "winter_storm"   # More outages, higher payouts
config.scenario_type = "normal_day"     # Fewer outages, may have zero claims
config.scenario_type = "heat_wave"      # Moderate outages
config.scenario_type = "severe_weather" # Default — good for demos
```

## Adding Event Grid (Optional, +5 min)

If you have an Azure subscription and want events published to Event Grid:

1. Run the setup script to create an Event Grid Topic:
   ```bash
   cd setup && ./azure-setup.sh
   ```
2. Copy the **endpoint** and **key** from the script output
3. Set them in the notebook's `DemoConfig`:
   ```python
   eventgrid_topic_endpoint = "https://your-topic.eventgrid.azure.net/api/events"
   eventgrid_topic_key = "your-key"
   ```
4. Re-run — events will publish to Azure and appear in the audit log as `published`

## Adding AI Validation (Optional)

To use Azure OpenAI instead of the built-in rule engine:

1. Set in the notebook's `DemoConfig`:
   ```python
   foundry_endpoint = "https://your-openai.openai.azure.com/"
   foundry_api_key = "your-key"
   ```
2. Re-run — claims will be validated by GPT-4 with natural language reasoning

Without these values, the rule-based engine produces identical output schema (confidence scores, severity assessment, fraud detection) — just deterministic instead of LLM-driven.

## Troubleshooting

**"No policy matches found"** — The `normal_day` scenario generates short outages that may not exceed any policy threshold. Switch to `severe_weather` or `winter_storm`.

**NOAA weather returns errors** — The NOAA API occasionally rate-limits or has downtime. The notebook handles this gracefully; claims will still process using default weather factors.

**Event Grid shows "failed"** — Check that your endpoint URL ends with `/api/events` and that the SAS key is correct. The notebook falls back to local-only mode automatically.

## Next Steps

- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Wire up Azure Functions and Logic Apps
- [docs/EVENTGRID_GUIDE.md](docs/EVENTGRID_GUIDE.md) — Event Grid subscription setup
- [powerbi/POWERBI_SETUP.md](powerbi/POWERBI_SETUP.md) — Build a real-time dashboard
- [docs/PRESTO_GUIDE.md](docs/PRESTO_GUIDE.md) — Customize simulation parameters
