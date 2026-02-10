# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-10

### Added
- Complete parametric insurance system
- PRESTO simulation tool (no API keys required)
- Microsoft Fabric integration (Lakehouse, Warehouse, Pipelines)
- Microsoft Foundry AI agent for claim validation
- Azure Functions for serverless processing (4 functions)
- Azure Event Grid for event-driven architecture
- Power BI dashboard (5 pages, 40+ visuals)
- 3 demo scenarios (Seattle storm, SF earthquake, NYC hurricane)
- Complete documentation (7 guides)
- PowerShell deployment support
- Python 3.11 support
- Comprehensive test suite
- CI/CD with GitHub Actions

### Features
- Real-time claim processing (<60 seconds)
- AI validation with 85-95% confidence
- Multi-source data correlation
- Fraud detection with pattern recognition
- Weather severity multipliers (1.0x - 1.5x)
- Complete audit trail
- 19 US cities simulation
- 40+ utility companies
- Historical data generation

### Documentation
- QUICKSTART.md - 30-minute setup guide
- DEPLOYMENT.md - Complete deployment instructions
- PROJECT_SUMMARY.md - Feature details
- PRESTO_GUIDE.md - Simulation tool documentation
- POWERBI_SETUP.md - Dashboard setup guide
- POWERSHELL_GUIDE.md - Windows deployment guide
- CONTRIBUTING.md - Contribution guidelines

### Infrastructure
- Azure Functions (4 functions)
  - OutageMonitor (timer-triggered, 5 min)
  - ThresholdEvaluator (event-triggered)
  - PayoutProcessor (event-triggered)
  - OutageResolutionMonitor (timer-triggered, 10 min)
- Microsoft Fabric
  - Lakehouse for raw data
  - Warehouse for structured data (6 tables, 4 views)
  - Pipelines for orchestration
- Azure Event Grid
  - 4 event types (outage.detected, threshold.exceeded, claim.validated, payout.processed)
- Power BI
  - 5 dashboard pages
  - 40+ visualizations
  - Real-time DirectQuery option

### Sample Data
- 11 sample policies across 5 cities
- 3 pre-configured demo scenarios
- Historical simulation capability (30+ days)

---

## [Unreleased]

### Planned
- Additional insurance types (flood, earthquake, drought)
- Machine learning claim prediction
- Mobile app for policyholders
- Blockchain audit trail
- Multi-language support
- Advanced fraud detection algorithms
- Integration with more weather APIs
- Real-time social media monitoring
- Customer notification system
- Policy management API

---

## Version History

- **1.0.0** (2026-02-10) - Initial release

---

[1.0.0]: https://github.com/yourusername/parametric-insurance-demo/releases/tag/v1.0.0
