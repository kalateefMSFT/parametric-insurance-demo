# Archive — v1 Multi-File Implementation

This directory contains the **original v1 implementation** of the parametric insurance demo. It used a multi-component architecture with separate Azure Functions, a standalone Foundry agent, individual SQL scripts, and a CLI demo runner.

## Why Archived

In v2, the entire demo was consolidated into a **single Microsoft Fabric notebook** (`fabric/notebooks/parametric_insurance_unified_demo.py`) that runs the complete pipeline end-to-end — including schema creation, PRESTO simulation, NOAA enrichment, policy matching, AI validation, payout processing, and Event Grid publishing.

The v1 files are preserved here because:

- The **Azure Functions** (ThresholdEvaluator, PayoutProcessor, etc.) can still be deployed as Event Grid subscribers alongside the v2 notebook for a full event-driven production architecture.
- The **standalone Foundry agent** (`foundry/agents/claims_validator_agent.py`) can be deployed to Microsoft Foundry as a standalone service.
- The **unit tests** (`tests/`) validate the individual function logic.
- The **original documentation** provides historical context.

## What's Here

```
archive/v1/
├── shared/              # Core libraries (config, models, fabric_client, eventgrid_client, presto)
├── functions/           # Azure Functions (4): OutageMonitor, ThresholdEvaluator, PayoutProcessor, OutageResolutionMonitor
├── foundry/             # Standalone Foundry AI agent + validation prompt
├── fabric/              # Original notebooks, SQL scripts, pipeline definitions
├── demo/                # CLI demo runner (run_demo.py)
├── tests/               # Unit tests for all functions
├── docs/                # Original PRESTO_GUIDE, PRESTO_SUMMARY, POWERSHELL_GUIDE
├── powerbi/             # Dashboard mockups (setup guide remains in active tree)
├── setup/               # (symlink or copy — setup scripts remain in active tree)
├── README_FIRST.md      # Original orientation guide
├── QUICKSTART.md        # Original 30-minute setup guide
├── DEPLOYMENT.md        # Original deployment guide
├── PROJECT_SUMMARY.md   # Original feature summary
├── MANIFEST.md          # Original file manifest
├── verify_structure.py  # Original file verification script
└── README.md            # This file
```

## Using v1 Functions with v2 Notebook

The v2 notebook publishes the same Event Grid event types that v1 Functions subscribe to:

| Notebook Event | v1 Function Subscriber |
|---------------|----------------------|
| `outage.detected` | `ThresholdEvaluator` |
| `claim.approved` | `PayoutProcessor` |

To deploy v1 Functions alongside the v2 notebook:

```bash
cd archive/v1/functions
func azure functionapp publish <your-function-app-name>
```

Then create Event Grid subscriptions as described in `docs/EVENTGRID_GUIDE.md`.
