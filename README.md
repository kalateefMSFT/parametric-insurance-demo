# Parametric Insurance Demo

> AI-powered automatic insurance claims processing for power outage business interruption

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Azure](https://img.shields.io/badge/Azure-0078D4?logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/)

## Overview

Complete parametric insurance system that automatically validates and pays claims when power outages exceed policy thresholds. Built with Microsoft Fabric, Azure Functions, and AI-powered validation.

**⚡ <60 seconds** end-to-end processing | **🤖 94% accuracy** AI validation | **💰 $9/month** demo cost

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yourusername/parametric-insurance-demo.git
cd parametric-insurance-demo

# 2. Install
pip install -r setup/requirements.txt

# 3. Deploy (Windows)
cd setup && .\azure-setup.ps1

# 3. Deploy (Linux/Mac)
cd setup && ./azure-setup.sh

# 4. Run Demo
python demo/run_demo.py --scenario storm_seattle
```

**Result:** 2 claims processed, $2,151 paid out in 45 seconds

## Features

- 🤖 **AI Validation** - Microsoft Foundry agent with 85-95% confidence
- ⚡ **Real-Time** - Sub-60-second claim processing  
- 🎯 **PRESTO Tool** - FREE outage simulation (no API keys!)
- 📊 **Power BI** - Complete analytics dashboard
- 🔒 **Fraud Detection** - Multi-source correlation
- 📝 **Complete Audit** - Full lineage tracking

## Architecture

```
PRESTO → Fabric → Functions → Foundry AI → Event Grid → Payout
```

## Demo Scenarios

| Scenario | Duration | Payout | Command |
|----------|----------|--------|---------|
| 🌩️ Seattle Storm | 187 min | $2,151 | `--scenario storm_seattle` |
| 🏢 SF Earthquake | 45 min | $1,000 | `--scenario sf_earthquake` |
| 🌀 NYC Hurricane | 358 min | $8,000 | `--scenario ny_hurricane` |

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - 30-minute setup
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete guide
- [docs/PRESTO_GUIDE.md](docs/PRESTO_GUIDE.md) - Simulation tool
- [powerbi/POWERBI_SETUP.md](powerbi/POWERBI_SETUP.md) - Dashboard

## Project Structure

```
├── shared/          # Core libraries
├── functions/       # Azure Functions (4)
├── foundry/         # AI agent
├── fabric/          # Data platform
├── powerbi/         # Analytics
├── setup/           # Deployment scripts
├── demo/            # Demo scenarios
└── docs/            # Documentation
```

## Cost

- **Demo:** ~$9/month (Azure + Fabric trial)
- **Production:** ~$85/month (10K events)

## Tech Stack

Microsoft Fabric | Foundry AI | Azure Functions | Event Grid | Power BI | Python 3.11

## License

MIT - See [LICENSE](LICENSE)

---

⭐ **Star this repo if you find it useful!**

[Report Bug](https://github.com/yourusername/parametric-insurance-demo/issues) · [Request Feature](https://github.com/yourusername/parametric-insurance-demo/issues)
