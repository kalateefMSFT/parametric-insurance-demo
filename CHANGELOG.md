# Changelog

All notable changes to this project will be documented in this file.

## [3.0.0] - 2026-02-17

### Changed — Multi-Notebook Pipeline Architecture

The demo has been restructured from a single monolithic notebook into a **4-notebook pipeline** with clear separation of concerns. Each notebook handles a distinct stage of the parametric insurance workflow and builds on data produced by the previous one.

### Added

- **Schema & policy notebook** (`fabric/notebooks/schema_load_with_policies.ipynb`)
  - Separated schema creation and policy loading from the demo pipeline
  - Creates/resets all non-policy Delta tables while preserving existing policies
  - Loads 250 sample policies across 40 US cities with deduplication
  - Safe to re-run without data loss

- **Weather alert monitor notebook** (`fabric/notebooks/weather_alert_policy_impact.ipynb`)
  - Polls NOAA for active severe weather alerts in real time
  - Geo-matches alerts to policyholder locations using Haversine formula (configurable radius, default 50 km)
  - Computes risk scores (45% severity + 35% urgency + 20% proximity)
  - Built-in deduplication (6-hour window) to avoid re-triggering
  - Publishes `policy.weather.impact` events to Event Grid
  - New `weather_impact_events` Delta table for impact persistence
  - Designed for scheduled execution (e.g., every 15 minutes)

- **Email notifier notebook** (`fabric/notebooks/weather_impact_email_notifier.ipynb`)
  - Two-step orchestration: Spark SQL enrichment + Foundry Orchestrator Agent (LLM-only) for email composition
  - Professional AI-generated email notifications to impacted policyholders
  - Rule-based template fallback when Foundry is unavailable
  - New `email_notifications` Delta table for notification tracking
  - Optional webhook dispatch to Logic App / Power Automate
  - Marks source impacts as notified to prevent duplicate emails

- **New Event Grid event type**: `policy.weather.impact` — published when a weather alert geo-matches a policy

- **New Foundry Agent experience** — the claims pipeline notebook now uses `AIProjectClient` and the Responses API instead of the legacy thread-based `AgentsClient`

### Changed

- **Claims pipeline notebook** renamed focus to `parametric_insurance_unified_demo_new.ipynb` targeting the New Foundry Agent experience (Responses API)
- Documentation (README.md, DEPLOYMENT.md, EVENTGRID_GUIDE.md, CHANGELOG.md) updated to reflect the 4-notebook architecture
- Event Grid guide updated to document all 5 event types across both publishing notebooks

---

## [2.0.0] - 2026-02-10

### Changed — Unified Notebook Architecture

The entire demo has been consolidated into a **single Microsoft Fabric notebook** that runs the complete pipeline end-to-end. This replaces the multi-component deployment (4 Azure Functions + standalone scripts + separate SQL scripts) with a single importable file.

### Added

- **Unified notebook** (`fabric/notebooks/parametric_insurance_unified_demo.py`)
  - All 8 pipeline steps in one file: schema creation, sample data, PRESTO simulation, NOAA weather enrichment, policy matching, AI claim validation, payout processing, analytics dashboard
  - Embedded PRESTO engine (no separate file upload required)
  - Embedded Event Grid client (REST API, no SDK dependency)
  - Embedded rule-based claim validator (fallback when Foundry Agent not configured)
  - `LocalEventLogger` for offline/local-only mode
  - `event_audit_log` Delta table for full event traceability
  - Connection test for Event Grid on startup with automatic fallback

- **Event Grid integration** wired at every pipeline stage:
  - `outage.detected` — published when outages match policies
  - `claim.approved` / `claim.denied` — published after AI validation
  - `payout.processed` — published when payment completes

- **New documentation**
  - `docs/DEPLOYMENT.md` — full deployment with optional integrations
  - `docs/EVENTGRID_GUIDE.md` — Event Grid wiring, subscriptions, monitoring

### Archived

The original v1 multi-file implementation has been moved to `archive/v1/`:
- `shared/` — config, models, fabric_client, eventgrid_client, presto
- `functions/` — OutageMonitor, ThresholdEvaluator, PayoutProcessor, OutageResolutionMonitor
- `foundry/` — claims_validator_agent, validation_prompt
- `fabric/` — original notebooks, SQL scripts, pipeline definitions
- `demo/` — run_demo.py CLI runner
- `tests/` — unit tests
- Original documentation (DEPLOYMENT.md, QUICKSTART.md, README_FIRST.md, etc.)

These files remain functional and can be deployed alongside the notebook for a full event-driven production architecture.

### Removed (from active tree)

- Multiple separate SQL script files (consolidated into notebook Step 1)
- Separate sample_policies.sql (consolidated into notebook Step 2)
- Standalone run_demo.py (replaced by notebook Run All)
- verify_structure.py (no longer needed — single notebook)

---

## [1.0.0] - 2026-02-10

### Added — Initial Release

- Complete parametric insurance system
- PRESTO simulation tool (no API keys required)
- Microsoft Fabric integration (Lakehouse, Warehouse, Pipelines)
- Microsoft Foundry AI agent for claim validation
- Azure Functions for serverless processing (4 functions)
- Azure Event Grid for event-driven architecture
- Power BI dashboard (5 pages, 40+ visuals)
- 3 demo scenarios (Seattle storm, SF earthquake, NYC hurricane)
- Complete documentation (7 guides)
- PowerShell and Bash deployment support
- Python 3.11 support
- Comprehensive test suite

---

[3.0.0]: https://github.com/yourusername/parametric-insurance-demo/releases/tag/v3.0.0
[2.0.0]: https://github.com/yourusername/parametric-insurance-demo/releases/tag/v2.0.0
[1.0.0]: https://github.com/yourusername/parametric-insurance-demo/releases/tag/v1.0.0
