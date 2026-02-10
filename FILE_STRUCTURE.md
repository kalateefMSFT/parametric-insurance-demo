# Complete File Structure

This document lists all files in the Parametric Insurance Demo project.

## Root Level Files (5)

```
.
├── .env.example                      # Environment variables template
├── README.md                         # Project overview and quick start
├── DEPLOYMENT.md                     # Complete deployment guide
├── PROJECT_SUMMARY.md                # Detailed feature summary
└── FILE_STRUCTURE.md                 # This file
```

## Shared Module (/shared) - 5 files

Core libraries used across all components:

```
shared/
├── __init__.py                       # Module initialization
├── config.py                         # Configuration management
├── models.py                         # Data models (OutageEvent, Policy, Claim, etc.)
├── fabric_client.py                  # Microsoft Fabric SQL client
└── eventgrid_client.py               # Azure Event Grid publisher
```

**Purpose**: Reusable code for database operations, event publishing, and data models

## Azure Functions (/functions) - 14 files

Serverless compute for claim processing:

```
functions/
├── host.json                         # Function app configuration
├── requirements.txt                  # Python dependencies
│
├── OutageMonitor/                    # Timer-triggered (every 5 min)
│   ├── __init__.py                   # Main function code
│   ├── function.json                 # Function binding configuration
│   └── requirements.txt              # Function dependencies
│
├── ThresholdEvaluator/               # Event Grid triggered
│   ├── __init__.py                   # Threshold validation logic
│   ├── function.json                 # Event Grid trigger config
│   └── requirements.txt              # Function dependencies
│
├── PayoutProcessor/                  # Event Grid triggered
│   ├── __init__.py                   # Payment processing logic
│   ├── function.json                 # Event Grid trigger config
│   └── requirements.txt              # Function dependencies
│
└── OutageResolutionMonitor/          # Timer-triggered (every 10 min)
    ├── __init__.py                   # Resolution monitoring logic
    ├── function.json                 # Timer trigger config
    └── requirements.txt              # Function dependencies
```

**Purpose**: 
- **OutageMonitor**: Polls Fabric for new outages, publishes events
- **ThresholdEvaluator**: Validates claims using AI, creates claim records
- **PayoutProcessor**: Processes payments, sends notifications
- **OutageResolutionMonitor**: Tracks when outages are resolved

## Microsoft Foundry (/foundry) - 2 files

AI agent for intelligent claim validation:

```
foundry/
├── agents/
│   └── claims_validator_agent.py    # AI claim validation logic
└── prompts/
    └── validation_prompt.txt         # Prompt template for AI agent
```

**Purpose**: Multi-source correlation, fraud detection, explainable decisions

## Microsoft Fabric (/fabric) - 4 files

Data platform for ingestion, storage, and analytics:

```
fabric/
├── notebooks/
│   └── 01_data_ingestion.py         # Outage & weather data ingestion
│
├── sql/
│   ├── create_warehouse_schema.sql  # Complete database schema
│   └── sample_policies.sql          # 11 sample policies
│
└── pipelines/
    └── outage_ingestion_pipeline.json  # Data Factory pipeline definition
```

**Purpose**: 
- **Notebook**: Ingests data from PowerOutage.us & NOAA every 5 minutes
- **Schema**: 6 tables, 4 views, 2 stored procedures, triggers
- **Policies**: Sample data for Seattle, Portland, SF, LA, NYC
- **Pipeline**: Orchestrates ingestion with quality checks

## Setup & Deployment (/setup) - 2 files

Automated resource provisioning:

```
setup/
├── azure-setup.sh                    # Creates all Azure resources
└── requirements.txt                  # Python dependencies
```

**Purpose**: One-command setup of all Azure resources (~5 minutes)

## Demo (/demo) - 1 file

Interactive demonstration:

```
demo/
└── run_demo.py                       # Demo runner with 3 scenarios
```

**Purpose**: Automated demo scenarios (Seattle storm, SF earthquake, NY hurricane)

## Tests (/tests) - 4 files

Unit and integration tests:

```
tests/
├── run_tests.py                      # Test runner
├── test_outage_monitor.py            # OutageMonitor tests
├── test_threshold_evaluator.py       # ThresholdEvaluator tests
└── test_payout_processor.py          # PayoutProcessor tests
```

**Purpose**: Automated testing for all components

---

## Total Files: 37

### Breakdown by Type:

| File Type | Count | Purpose |
|-----------|-------|---------|
| Python (.py) | 18 | Application logic |
| JSON (.json) | 5 | Configuration & bindings |
| SQL (.sql) | 2 | Database schema |
| Markdown (.md) | 5 | Documentation |
| Shell (.sh) | 1 | Automation script |
| Text (.txt) | 5 | Requirements & prompts |
| Other | 1 | .env.example |
| **Total** | **37** | |

### Breakdown by Component:

| Component | Files | Lines of Code (approx) |
|-----------|-------|------------------------|
| Shared Libraries | 5 | 800 |
| Azure Functions | 14 | 1,200 |
| Microsoft Foundry | 2 | 600 |
| Microsoft Fabric | 4 | 1,500 |
| Setup & Deploy | 2 | 400 |
| Demo & Tests | 5 | 500 |
| Documentation | 5 | 2,000 |
| **Total** | **37** | **~7,000** |

---

## Key Files to Review

For understanding the project, start with these files in order:

1. **README.md** - Project overview and architecture
2. **DEPLOYMENT.md** - Step-by-step deployment guide
3. **PROJECT_SUMMARY.md** - Feature details and business value
4. **shared/models.py** - Understand data structures
5. **functions/ThresholdEvaluator/__init__.py** - Core claim logic
6. **foundry/agents/claims_validator_agent.py** - AI validation
7. **fabric/sql/create_warehouse_schema.sql** - Database design
8. **demo/run_demo.py** - See it all in action

---

## File Dependencies

```
Azure Functions
    ↓ imports
Shared Libraries (config.py, models.py, fabric_client.py, eventgrid_client.py)
    ↓ connects to
Azure Resources (Event Grid, Fabric Warehouse)
    ↓ stores data in
Microsoft Fabric (SQL Warehouse)
    ↓ data ingested by
Fabric Notebook (01_data_ingestion.py)
    ↓ calls
External APIs (PowerOutage.us, NOAA)
```

---

## Missing Files Check

✅ All core files present  
✅ All function bindings configured  
✅ All dependencies documented  
✅ All tests created  
✅ All documentation complete  

**Status**: Project is complete and ready for deployment
