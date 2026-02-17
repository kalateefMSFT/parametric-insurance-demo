# Parametric Insurance Demo

> AI-powered automatic insurance claims processing for power outage business interruption — run entirely from Microsoft Fabric notebooks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Azure](https://img.shields.io/badge/Azure-0078D4?logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/)

## Overview

This demo runs an **end-to-end parametric insurance pipeline** across a set of Microsoft Fabric notebooks. It simulates power outages, enriches them with live weather data, matches affected policies, validates claims with an AI agent, processes payouts, publishes events to Azure Event Grid, monitors real-time weather alerts against policyholder locations, and sends AI-generated email notifications — all with zero paid API dependencies.

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │  1. schema_load_with_policies.ipynb  │
                        │     Create schema & load 250 policies│
                        └──────────────┬──────────────────────┘
                                       │
                                       ▼
          ┌────────────────────────────────────────────────────────┐
          │  2. parametric_insurance_unified_demo_new.ipynb         │
          │     PRESTO simulation → NOAA weather → policy matching │
          │     → Foundry AI claim validation → payout processing  │
          │     → Event Grid publishing → dashboard summary        │
          └──────────────┬─────────────────────────────────────────┘
                         │
                         ▼
          ┌────────────────────────────────────────────────────────┐
          │  3. weather_alert_policy_impact.ipynb                   │
          │     Poll NOAA alerts → geo-match to policies           │
          │     → risk scoring → publish policy.weather.impact     │
          └──────────────┬─────────────────────────────────────────┘
                         │
                         ▼
          ┌────────────────────────────────────────────────────────┐
          │  4. weather_impact_email_notifier.ipynb                 │
          │     Load unnotified impacts → Foundry Orchestrator     │
          │     Agent composes emails → persist & dispatch          │
          └────────────────────────────────────────────────────────┘
```

## Quick Start (20 minutes)

### Prerequisites

- Microsoft Fabric workspace (free 60-day trial available)
- (Optional) Azure subscription for Event Grid integration
- (Optional) Azure OpenAI / Foundry endpoint for AI validation and email generation

### Step 1 — Create Fabric Resources

1. Go to [Microsoft Fabric](https://app.fabric.microsoft.com/)
2. Create a workspace named `ParametricInsurance`
3. Inside the workspace, create a **Lakehouse** named `parametric_insurance_lakehouse`

### Step 2 — Import the Notebooks

1. In your workspace, click **Import** → **Notebook**
2. Upload all four notebooks from `fabric/notebooks/`:

| Notebook | Purpose | Run Order |
|----------|---------|-----------|
| `schema_load_with_policies.ipynb` | Creates Delta tables and loads 250 sample policies across 40 US cities | **1st** (run once) |
| `parametric_insurance_unified_demo_new.ipynb` | Runs the full claims pipeline: outage simulation, weather enrichment, AI validation, payouts | **2nd** |
| `weather_alert_policy_impact.ipynb` | Monitors live NOAA weather alerts and matches them to policyholder locations | **3rd** (can run on a schedule) |
| `weather_impact_email_notifier.ipynb` | Generates and dispatches AI-composed email notifications to impacted policyholders | **4th** (after weather impacts are detected) |

3. Open each notebook and click **Lakehouse** in the left panel → attach to `parametric_insurance_lakehouse`

### Step 3 — Configure (Optional)

Edit the config class in Step 0 of each notebook:

```python
# In parametric_insurance_unified_demo_new.ipynb — DemoConfig
scenario_type: str = "severe_weather"  # normal_day | severe_weather | heat_wave | winter_storm

# Event Grid (get values from azure-setup.sh output or Azure Portal)
eventgrid_topic_endpoint: str = "https://your-topic.westus-1.eventgrid.azure.net/api/events"
eventgrid_topic_key: str = "your-sas-key"

# Foundry AI Agent (leave blank for rule-based fallback)
foundry_endpoint: str = "https://your-openai.openai.azure.com/"
foundry_agent: str = "your-agent-name"
```

```python
# In weather_alert_policy_impact.ipynb — AlertMonitorConfig
min_severity: str = "Severe"       # Minor | Moderate | Severe | Extreme
alert_radius_km: float = 50.0     # Geo-match radius
dedup_window_hours: int = 6       # Avoid duplicate alerts
```

```python
# In weather_impact_email_notifier.ipynb — EmailNotifierConfig
foundry_endpoint: str = "https://your-openai.openai.azure.com/"
orchestrator_agent: str = "your-orchestrator-agent"
email_dispatch_webhook: str = ""   # Optional Logic App / Power Automate URL
```

### Step 4 — Run the Notebooks

Run the notebooks **in order**. Each builds on the data produced by the previous one.

**Notebook 1 — Schema & Policies** (`schema_load_with_policies.ipynb`):
- Creates 7 Delta tables (policies, outage_events, weather_data, claims, payouts, outage_raw, event_audit_log)
- Loads 250 sample policies across 40 US cities
- Safe to re-run (deduplicates policies, resets non-policy tables)

**Notebook 2 — Claims Pipeline** (`parametric_insurance_unified_demo_new.ipynb`):
- Simulates power outages with PRESTO
- Fetches live weather from NOAA (free, no API key)
- Matches outages to policies and publishes `outage.detected` events
- Validates claims via Foundry Agent (or rule-based fallback) and publishes `claim.approved`/`claim.denied`
- Processes payouts and publishes `payout.processed`
- Displays a full analytics dashboard and event audit log

**Notebook 3 — Weather Alert Monitor** (`weather_alert_policy_impact.ipynb`):
- Polls NOAA for active severe weather alerts
- Geo-matches alerts to policyholder locations using the Haversine formula (default 50 km radius)
- Computes a risk score (severity + urgency + proximity)
- Deduplicates against recent matches to avoid re-triggering
- Publishes `policy.weather.impact` events to Event Grid
- Persists impact records to the `weather_impact_events` Delta table

**Notebook 4 — Email Notifier** (`weather_impact_email_notifier.ipynb`):
- Reads unnotified impacts from `weather_impact_events`
- Enriches each impact with policy details via Spark SQL
- Calls a Foundry Orchestrator Agent (LLM-only) to compose professional emails (or uses a template fallback)
- Persists emails to the `email_notifications` Delta table
- Optionally dispatches via a webhook (Logic App / Power Automate)
- Marks source impacts as notified

## Demo Scenarios

| Scenario | Outages | Typical Claims | Typical Payout | Config Value |
|----------|---------|---------------|---------------|-------------|
| Severe Weather | 10-20 | 3-8 | $2,000-$15,000 | `severe_weather` |
| Winter Storm | 15-30 | 5-12 | $5,000-$25,000 | `winter_storm` |
| Heat Wave | 5-15 | 2-6 | $1,000-$8,000 | `heat_wave` |
| Normal Day | 2-5 | 0-2 | $0-$2,000 | `normal_day` |

## Project Structure

```
parametric-insurance-demo/
│
├── fabric/
│   └── notebooks/
│       ├── schema_load_with_policies.ipynb              ← Run 1st: schema & policy data
│       ├── parametric_insurance_unified_demo_new.ipynb   ← Run 2nd: full claims pipeline
│       ├── weather_alert_policy_impact.ipynb             ← Run 3rd: weather alert monitoring
│       └── weather_impact_email_notifier.ipynb           ← Run 4th: email notifications
│
├── setup/
│   ├── azure-setup.sh          # Create Event Grid + Functions (optional)
│   ├── azure-setup.ps1         # PowerShell version
│   └── requirements.txt        # Python dependencies
│
├── docs/
│   ├── DEPLOYMENT.md           # Full deployment guide
│   ├── PRESTO_GUIDE.md         # PRESTO simulation reference
│   └── EVENTGRID_GUIDE.md      # Event Grid wiring guide
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
├── CHANGELOG.md                # Version history
├── .env.example                # Environment variable template
└── .gitignore
```

## What's Free

| Component | Source | Cost |
|-----------|--------|------|
| Power Outage Simulation | **PRESTO** (embedded in notebook) | Free |
| Weather Enrichment | **NOAA Weather API** (api.weather.gov) | Free — no API key |
| Weather Alert Monitoring | **NOAA Alerts API** (api.weather.gov) | Free — no API key |
| Data Platform | Microsoft Fabric | Free 60-day trial |
| AI Validation (fallback) | Rule-based engine (embedded) | Free |
| Email Generation (fallback) | Template engine (embedded) | Free |

## Optional Paid Components

| Component | Service | Purpose |
|-----------|---------|---------|
| Event Grid | Azure Event Grid | Event-driven integration with Functions/Logic Apps |
| AI Validation | Azure OpenAI / Foundry | LLM-powered claim validation |
| Email Generation | Azure OpenAI / Foundry | AI-composed policyholder notifications |
| Notifications | Azure Logic Apps | Email/SMS dispatch via webhook |
| Dashboard | Power BI Pro | Shared real-time dashboards |

## Event Grid Integration

The notebooks publish 5 event types to Azure Event Grid:

| Event Type | Published By | When Published | Suggested Subscriber |
|-----------|-------------|---------------|---------------------|
| `outage.detected` | Claims pipeline | Outage matches a policy | ThresholdEvaluator Function |
| `claim.approved` | Claims pipeline | AI validates and approves claim | PayoutProcessor Function |
| `claim.denied` | Claims pipeline | AI denies claim | Audit logger |
| `payout.processed` | Claims pipeline | Payment completed | Logic App (email/SMS) |
| `policy.weather.impact` | Weather alert monitor | Weather alert geo-matches a policy | Email notifier / Logic App |

See [docs/EVENTGRID_GUIDE.md](docs/EVENTGRID_GUIDE.md) for wiring instructions.

## Delta Tables

| Table | Created By | Description |
|-------|-----------|-------------|
| `policies` | Schema notebook | 250 sample insurance policies across 40 US cities |
| `outage_events` | Claims pipeline | Simulated power outage events from PRESTO |
| `outage_raw` | Claims pipeline | Raw outage data before filtering |
| `weather_data` | Claims pipeline | NOAA weather observations per location |
| `claims` | Claims pipeline | Insurance claims with AI validation results |
| `payouts` | Claims pipeline | Payout records for approved claims |
| `event_audit_log` | Claims pipeline | Audit trail of all Event Grid publications |
| `weather_impact_events` | Weather alert monitor | Weather alert-to-policy impact matches |
| `email_notifications` | Email notifier | Generated email notification records |

## Documentation

| Guide | Description | Time |
|-------|-------------|------|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Full deployment with Event Grid & Functions | 30 min |
| [docs/PRESTO_GUIDE.md](docs/PRESTO_GUIDE.md) | PRESTO simulation reference | Reference |
| [docs/EVENTGRID_GUIDE.md](docs/EVENTGRID_GUIDE.md) | Event Grid wiring & subscriptions | 15 min |
| [powerbi/POWERBI_SETUP.md](powerbi/POWERBI_SETUP.md) | Power BI dashboard | 20 min |

## Migrating from v1

The original multi-file implementation (Azure Functions + standalone scripts) is preserved in `archive/v1/`. The unified notebook architecture consolidates all of that logic into runnable notebooks. See [CHANGELOG.md](CHANGELOG.md) for details.

## Cost

- **Notebook-only demo:** Free (Fabric trial + PRESTO + NOAA)
- **With Event Grid:** ~$1/month
- **With Azure OpenAI:** ~$5/month (demo usage)
- **Full production:** ~$85/month (10K events)

## License

MIT — See [LICENSE](LICENSE)

---

[Report Bug](https://github.com/yourusername/parametric-insurance-demo/issues) · [Request Feature](https://github.com/yourusername/parametric-insurance-demo/issues)
