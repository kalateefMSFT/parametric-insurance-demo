# Parametric Insurance Demo

> AI-powered automatic insurance claims processing for power outage business interruption — run entirely from a single Microsoft Fabric notebook.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Azure](https://img.shields.io/badge/Azure-0078D4?logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/)

## Overview

This demo runs an **end-to-end parametric insurance pipeline** inside a single Microsoft Fabric notebook. It simulates power outages, enriches them with live weather data, matches affected policies, validates claims with an AI agent, processes payouts, and publishes events to Azure Event Grid at every stage — all with zero paid API dependencies.

**⚡ <60 seconds** end-to-end processing &nbsp;|&nbsp; **🤖 94% accuracy** AI validation &nbsp;|&nbsp; **💰 $0 API cost** (PRESTO + NOAA)

## Architecture

```
PRESTO (simulation)
   │
   ▼
Fabric Lakehouse (Delta tables)
   │
   ├──► NOAA Weather API (free enrichment)
   │
   ▼
Policy Matching (Spark SQL)
   │
   ├──► Event Grid: outage.detected ──► ThresholdEvaluator Function (optional)
   │
   ▼
Foundry AI Agent / Rule-Based Validation
   │
   ├──► Event Grid: claim.approved / claim.denied ──► PayoutProcessor Function (optional)
   │
   ▼
Payout Processing
   │
   ├──► Event Grid: payout.processed ──► Logic App / Notifications (optional)
   │
   ▼
Dashboard Summary + Event Audit Log
```

## Quick Start (20 minutes)

### Prerequisites

- Microsoft Fabric workspace (free 60-day trial available)
- (Optional) Azure subscription for Event Grid integration
- (Optional) Azure OpenAI endpoint for Foundry Agent AI validation

### Step 1 — Create Fabric Resources

1. Go to [Microsoft Fabric](https://app.fabric.microsoft.com/)
2. Create a workspace named `ParametricInsurance`
3. Inside the workspace, create a **Lakehouse** named `parametric_insurance_lakehouse`

### Step 2 — Import the Notebook

1. Click **Import** → **Notebook**
2. You have options for the notebook: 
    - `fabric/notebooks/parametric_insurance_unified_demo.ipynb` targets the Classic Microsoft Foundry Agents that uses Threads
    - `fabric/notebooks/parametric_insurance_unified_demo_new.ipynb` targets the New Microsoft Foundry Agents that uses Responses

3. Upload: Chosen notebook to the `ParametricInsurance` workspace
4. Open the notebook
5. Click **Lakehouse** in the left panel → attach to `parametric_insurance_lakehouse`

### Step 3 — Configure (Optional)

Edit the `DemoConfig` class in Step 0 of the notebook:

```python
# Change the scenario (normal_day | severe_weather | heat_wave | winter_storm)
scenario_type: str = "severe_weather"

# Enable Event Grid (get values from azure-setup.sh output or Azure Portal)
eventgrid_topic_endpoint: str = "https://your-topic.westus-1.eventgrid.azure.net/api/events"
eventgrid_topic_key: str = "your-sas-key"

# Enable Foundry AI Agent (leave blank for rule-based fallback)
foundry_endpoint: str = "https://your-openai.openai.azure.com/"
foundry_api_key: str = "your-key"
```

### Step 4 — Run All Cells

Click **Run All**. The notebook will:

1. Create 7 Delta tables (policies, outage_events, weather_data, claims, payouts, outage_raw, event_audit_log)
2. Load 11 sample policies across 5 US cities
3. Simulate power outages with PRESTO
4. Fetch live weather from NOAA (free)
5. Match outages to policies and publish `outage.detected` events
6. Validate claims via Foundry Agent (or rule-based fallback) and publish `claim.approved`/`claim.denied`
7. Process payouts and publish `payout.processed`
8. Display a full analytics dashboard and event audit log

**Expected Result:** Multiple claims processed, payouts disbursed in under 60 seconds.

## Demo Scenarios

| Scenario | Outages | Typical Claims | Typical Payout | Config Value |
|----------|---------|---------------|---------------|-------------|
| 🌩️ Severe Weather | 10–20 | 3–8 | $2,000–$15,000 | `severe_weather` |
| ❄️ Winter Storm | 15–30 | 5–12 | $5,000–$25,000 | `winter_storm` |
| 🔥 Heat Wave | 5–15 | 2–6 | $1,000–$8,000 | `heat_wave` |
| ☀️ Normal Day | 2–5 | 0–2 | $0–$2,000 | `normal_day` |

## Project Structure

```
parametric-insurance-demo/
│
├── fabric/
│   └── notebooks/
│       └── parametric_insurance_unified_demo.py   ← The legacy notebook
│       └── parametric_insurance_unified_demo.ipynb   ← The notebook targeting the Classic Foundry Agents
│       └── parametric_insurance_unified_demo_new.ipynb   ← The notebook targeting the New Foundry Agent Experience
│   └── sql/
│       └── additional_sample_policies.sql   ← The notebook creates 11 policies, this is 40 more.
│
├── setup/
│   ├── azure-setup.sh          # Create Event Grid + Functions (optional)
│   ├── azure-setup.ps1         # PowerShell version
│   └── requirements.txt        # Python dependencies
│
├── docs/
│   ├── DEPLOYMENT.md           # Full deployment guide
│   ├── PRESTO_GUIDE.md         # PRESTO simulation reference
│   ├── EVENTGRID_GUIDE.md      # Event Grid wiring guide
│   └── POWERBI_SETUP.md        # Power BI dashboard setup
│
├── powerbi/
│   ├── POWERBI_SETUP.md        # Dashboard setup
│   ├── QUICK_REFERENCE.md      # Quick reference card
│   └── queries.sql             # Pre-built SQL queries
│
├── archive/
│   └── v1/                     # Original multi-file implementation
│       ├── shared/             #   Core libraries
│       ├── functions/          #   Azure Functions (4)
│       ├── foundry/            #   Standalone AI agent
│       ├── fabric/             #   Original notebooks & SQL
│       ├── demo/               #   CLI demo runner
│       └── tests/              #   Unit tests
│
├── README.md                   ← YOU ARE HERE
├── QUICKSTART.md               # 10-minute quick start
├── CHANGELOG.md                # Version history
├── .env.example                # Environment variable template
└── .gitignore
```

## What's Free

| Component | Source | Cost |
|-----------|--------|------|
| Power Outage Simulation | **PRESTO** (embedded in notebook) | Free |
| Weather Enrichment | **NOAA Weather API** (api.weather.gov) | Free — no API key |
| Data Platform | Microsoft Fabric | Free 60-day trial |
| AI Validation (fallback) | Rule-based engine (embedded) | Free |

## Optional Paid Components

| Component | Service | Purpose |
|-----------|---------|---------|
| Event Grid | Azure Event Grid | Event-driven integration with Functions/Logic Apps |
| AI Validation | Azure OpenAI / Foundry | LLM-powered claim validation |
| Notifications | Azure Logic Apps | Email/SMS on payout |
| Dashboard | Power BI Pro | Shared real-time dashboards |

## Event Grid Integration

The notebook publishes 4 event types to Azure Event Grid. These are compatible with the Azure Functions in `archive/v1/functions/` or any custom subscriber.

| Event Type | When Published | Suggested Subscriber |
|-----------|---------------|---------------------|
| `outage.detected` | Outage matches a policy | ThresholdEvaluator Function |
| `claim.approved` | AI validates and approves claim | PayoutProcessor Function |
| `claim.denied` | AI denies claim | Audit logger |
| `payout.processed` | Payment completed | Logic App (email/SMS) |

See [docs/EVENTGRID_GUIDE.md](docs/EVENTGRID_GUIDE.md) for wiring instructions.

## Documentation

| Guide | Description | Time |
|-------|-------------|------|
| [QUICKSTART.md](QUICKSTART.md) | Minimal steps to run the demo | 10 min |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Full deployment with Event Grid & Functions | 30 min |
| [docs/PRESTO_GUIDE.md](docs/PRESTO_GUIDE.md) | PRESTO simulation reference | Reference |
| [docs/EVENTGRID_GUIDE.md](docs/EVENTGRID_GUIDE.md) | Event Grid wiring & subscriptions | 15 min |
| [powerbi/POWERBI_SETUP.md](powerbi/POWERBI_SETUP.md) | Power BI dashboard | 20 min |

## Migrating from v1

The original multi-file implementation (Azure Functions + standalone scripts) is preserved in `archive/v1/`. The unified notebook consolidates all of that logic into a single runnable file. See [CHANGELOG.md](CHANGELOG.md) for details.

## Cost

- **Notebook-only demo:** Free (Fabric trial + PRESTO + NOAA)
- **With Event Grid:** ~$1/month
- **With Azure OpenAI:** ~$5/month (demo usage)
- **Full production:** ~$85/month (10K events)

## License

MIT — See [LICENSE](LICENSE)

---

[Report Bug](https://github.com/yourusername/parametric-insurance-demo/issues) · [Request Feature](https://github.com/yourusername/parametric-insurance-demo/issues)
