# Deployment Guide - Parametric Insurance Demo

Complete step-by-step guide to deploy and run the demo.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Setup](#azure-setup)
3. [Microsoft Fabric Setup](#microsoft-fabric-setup)
4. [Microsoft Foundry Setup](#microsoft-foundry-setup)
5. [Azure Functions Deployment](#azure-functions-deployment)
6. [Testing](#testing)
7. [Running the Demo](#running-the-demo)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Azure CLI** (v2.50+): [Install Guide](https://docs.microsoft.com/cli/azure/install-azure-cli)
- **Azure Functions Core Tools** (v4.x): [Install Guide](https://docs.microsoft.com/azure/azure-functions/functions-run-local)
- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **Git**: [Download](https://git-scm.com/)

### Required Access

- Azure subscription with Owner or Contributor role
- Microsoft Fabric workspace with Admin permissions
- Microsoft Foundry access (preview)

### Verify Installation

```bash
# Check Azure CLI
az --version

# Check Functions Core Tools
func --version

# Check Python
python --version
```

---

## Azure Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd parametric-insurance-demo
```

### Step 2: Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r setup/requirements.txt
```

### Step 3: Login to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### Step 4: Run Azure Setup Script

```bash
cd setup
chmod +x azure-setup.sh
./azure-setup.sh
```

This script creates:
- Resource Group
- Storage Account
- Application Insights
- Event Grid Topic
- Function App
- Event Grid Subscriptions

**Expected Output:**
```
[INFO] Creating resource group: parametric-insurance-rg
[INFO] Creating storage account: parametricsa12345
[INFO] Creating Application Insights: parametric-insurance-insights
[INFO] Creating Event Grid Topic: parametric-insurance-events
[INFO] Creating Function App: parametric-insurance-func-12345
```

### Step 5: Verify Resources

```bash
az resource list --resource-group parametric-insurance-rg --output table
```

You should see 5 resources created.

---

## Microsoft Fabric Setup

### Step 1: Create Workspace

1. Go to [Microsoft Fabric](https://app.fabric.microsoft.com/)
2. Click **Workspaces** → **New Workspace**
3. Name: `ParametricInsurance`
4. License: Select appropriate tier (F2+ recommended)

### Step 2: Create Lakehouse

1. In workspace, click **New** → **Lakehouse**
2. Name: `parametric_insurance_lakehouse`
3. Wait for provisioning

### Step 3: Create Warehouse

1. In workspace, click **New** → **Warehouse**
2. Name: `parametric_insurance_warehouse`
3. Wait for provisioning

### Step 4: Get Connection Details

#### Warehouse Connection String

1. Open Warehouse
2. Click **Settings** → **Connection strings**
3. Copy **SQL Connection String**
4. Format: 
   ```
   Driver={ODBC Driver 18 for SQL Server};
   Server=<workspace>.datawarehouse.fabric.microsoft.com;
   Database=parametric_insurance_warehouse;
   Authentication=ActiveDirectoryInteractive;
   ```

#### Workspace and Lakehouse IDs

1. In workspace, click **Workspace settings**
2. Copy **Workspace ID** from URL:
   ```
   https://app.fabric.microsoft.com/groups/{workspace-id}/...
   ```
3. Open Lakehouse → Settings → Copy **Lakehouse ID**

### Step 5: Run SQL Scripts

1. Open Warehouse in Fabric
2. Click **New SQL Query**
3. Run scripts in order:
   ```sql
   -- Copy/paste content from:
   fabric/sql/create_warehouse_schema.sql
   
   -- Then run:
   fabric/sql/sample_policies.sql
   ```

### Step 6: Import Notebooks

1. In workspace, click **Import** → **Notebook**
2. Upload: `fabric/notebooks/01_data_ingestion.py`
3. Attach to lakehouse: `parametric_insurance_lakehouse`
4. Create subdirectory in the lakehouse under Files called shared. (`/lakehouse/default/Files/shared`)
5. Take the presto.py from the repository shared directory (`shared/presto.py`) and upload it to the newly created shared directory in the Lakehouse.

(This py file is needed for the notebook to be able to run the PRESTO simulations.)

### Step 7: Create Data Pipeline

1. In workspace, click **New** → **Data pipeline**
2. Name: `Outage Ingestion Pipeline`
3. Add **Notebook** activity
4. Select notebook: `01_data_ingestion`
5. Schedule: **Every 5 minutes**
6. Publish pipeline

### Step 8: Update .env File

```bash
cd ..
nano .env  # or use your preferred editor
```

Update these values:
```env
FABRIC_WORKSPACE_ID=<your-workspace-id>
FABRIC_LAKEHOUSE_ID=<your-lakehouse-id>
FABRIC_WAREHOUSE_CONNECTION=<your-connection-string>
```

---

## Microsoft Foundry Setup

### Step 1: Access Foundry Portal

1. Go to [Microsoft Foundry](https://foundry.microsoft.com/) (preview)
2. Sign in with Azure AD account

### Step 2: Create Agent

1. Click **Agents** → **New Agent**
2. Name: `Claims Validator`
3. Description: `Validates parametric insurance claims using multi-source data`
4. Upload agent code:
   ```bash
   # Upload file:
   foundry/agents/claims_validator_agent.py
   ```

### Step 3: Configure Agent

1. Set **Model**: `gpt-4`
2. Set **Temperature**: `0.2`
3. Set **Max Tokens**: `2000`
4. Enable **Data Sources**:
   - Microsoft Fabric (connect to your workspace)
   - External APIs (NOAA Weather)

### Step 4: Get Agent Credentials

1. Click **Settings** → **API Access**
2. Copy:
   - **Endpoint URL**
   - **API Key**
3. Update `.env`:
   ```env
   FOUNDRY_ENDPOINT=<your-endpoint>
   FOUNDRY_API_KEY=<your-api-key>
   ```

### Step 5: Test Agent

```bash
cd foundry/agents
python claims_validator_agent.py
```

Expected output:
```
Decision: APPROVE
Confidence: 94%
Payout Amount: $1,083.33
Reasoning: Threshold exceeded by 1.12 hours...
```

---

## Azure Functions Deployment

### Step 1: Prepare Functions

```bash
cd ../functions
```

### Step 2: Create local.settings.json

```bash
cat > local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "EVENTGRID_TOPIC_ENDPOINT": "$(cat ../.env | grep EVENTGRID_TOPIC_ENDPOINT | cut -d '=' -f2)",
    "EVENTGRID_KEY": "$(cat ../.env | grep EVENTGRID_KEY | cut -d '=' -f2)",
    "FABRIC_WAREHOUSE_CONNECTION": "$(cat ../.env | grep FABRIC_WAREHOUSE_CONNECTION | cut -d '=' -f2)",
    "FOUNDRY_ENDPOINT": "$(cat ../.env | grep FOUNDRY_ENDPOINT | cut -d '=' -f2)",
    "FOUNDRY_API_KEY": "$(cat ../.env | grep FOUNDRY_API_KEY | cut -d '=' -f2)"
  }
}
EOF
```

### Step 3: Install Dependencies

```bash
cd OutageMonitor
pip install -r requirements.txt --target .python_packages/lib/site-packages
cd ..
```

Repeat for other functions:
```bash
cd ThresholdEvaluator
pip install -r requirements.txt --target .python_packages/lib/site-packages
cd ..

cd PayoutProcessor
pip install -r requirements.txt --target .python_packages/lib/site-packages
cd ..
```

### Step 4: Deploy Functions

Get Function App name from setup:
```bash
FUNCTION_APP_NAME=$(cat ../.env | grep FUNCTION_APP_NAME | cut -d '=' -f2)
```

Deploy:
```bash
func azure functionapp publish $FUNCTION_APP_NAME
```

Expected output:
```
Getting site publishing info...
Creating archive for current directory...
Uploading 2.5 MB [###############################################]
Upload completed successfully.
Deployment successful.

Functions in parametric-insurance-func-12345:
    OutageMonitor - [timerTrigger]
    PayoutProcessor - [eventGridTrigger]
    ThresholdEvaluator - [eventGridTrigger]
```

### Step 5: Verify Deployment

```bash
# Check function status
az functionapp function list \
  --name $FUNCTION_APP_NAME \
  --resource-group parametric-insurance-rg \
  --output table
```

---

## Testing

### Test 1: Configuration Validation

```bash
cd ../shared
python config.py
```

Expected:
```
✓ Configuration valid
  Resource Group: parametric-insurance-rg
  Event Grid: https://...
  Fabric Workspace: ...
  Foundry Endpoint: ...
```

### Test 2: Fabric Connection

```bash
python -c "
from fabric_client import FabricClient
client = FabricClient()
policies = client.get_policies_in_zip('98101')
print(f'Found {len(policies)} policies in ZIP 98101')
"
```

Expected:
```
Found 2 policies in ZIP 98101
```

### Test 3: Event Grid Connection

```bash
python -c "
from eventgrid_client import test_event_grid_connection
result = test_event_grid_connection()
print('Event Grid test:', 'PASSED' if result else 'FAILED')
"
```

### Test 4: AI Agent

```bash
cd ../foundry/agents
python claims_validator_agent.py
```

Should output claim validation result.

### Test 5: End-to-End Function Test

```bash
cd ../tests
python test_outage_monitor.py
python test_threshold_evaluator.py
python test_payout_processor.py
```

---

## Running the Demo

### Option 1: Automated Demo

```bash
cd ../demo
python run_demo.py --scenario storm_seattle
```

This simulates:
1. Power outage event
2. Weather data correlation
3. Policy threshold checks
4. AI claim validation
5. Automatic payouts

### Option 2: Manual Testing

1. **Trigger outage detection:**
   ```bash
   python ../tests/trigger_outage_event.py --zip 98101 --duration 150
   ```

2. **Monitor Application Insights:**
   - Go to Azure Portal
   - Open Application Insights resource
   - Check **Live Metrics**
   - Watch functions execute in real-time

3. **Check Power BI Dashboard:**
   - Open Power BI workspace
   - Refresh `Parametric Insurance Monitor` report
   - See claims appearing in real-time

### Option 3: Use Real Data

The system will automatically process real outages from PowerOutage.us:

1. Wait for data ingestion (runs every 5 minutes)
2. Outages affecting insured ZIP codes trigger automatically
3. Monitor logs in Application Insights

---

## Monitoring

### Application Insights

```bash
# Stream logs
az monitor app-insights metrics show \
  --app parametric-insurance-insights \
  --resource-group parametric-insurance-rg \
  --metrics requests/count
```

### Event Grid Metrics

```bash
az monitor metrics list \
  --resource <event-grid-topic-id> \
  --metric PublishSuccessCount
```

### Fabric Pipeline Monitoring

1. Go to Fabric workspace
2. Click **Monitoring Hub**
3. Check pipeline run history

---

## Troubleshooting

### Issue: Functions Not Triggering

**Symptoms:** Events published but functions don't execute

**Solution:**
1. Check Event Grid subscriptions:
   ```bash
   az eventgrid event-subscription list \
     --source-resource-id <topic-id> \
     --output table
   ```

2. Verify function app is running:
   ```bash
   az functionapp show \
     --name $FUNCTION_APP_NAME \
     --resource-group parametric-insurance-rg \
     --query state
   ```

3. Check logs:
   ```bash
   az functionapp log tail \
     --name $FUNCTION_APP_NAME \
     --resource-group parametric-insurance-rg
   ```

### Issue: Fabric Connection Failed

**Symptoms:** `pyodbc.OperationalError: Unable to connect`

**Solution:**
1. Verify connection string format
2. Ensure ODBC Driver 18 installed:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install unixodbc-dev msodbcsql18
   
   # macOS
   brew install unixodbc
   ```
3. Test connection:
   ```python
   import pyodbc
   conn = pyodbc.connect("<your-connection-string>")
   ```

### Issue: AI Agent Errors

**Symptoms:** `Error calling Foundry agent`

**Solution:**
1. Verify Foundry endpoint and API key
2. Check agent deployment status in Foundry portal
3. Use fallback rule-based validation (automatic)

### Issue: No Claims Created

**Symptoms:** Outages detected but no claims filed

**Solution:**
1. Check policies exist in affected ZIP codes:
   ```sql
   SELECT * FROM policies WHERE zip_code = '98101'
   ```

2. Verify outage duration exceeds threshold:
   ```sql
   SELECT duration_minutes, threshold_minutes 
   FROM outage_events o
   JOIN policies p ON o.zip_code = p.zip_code
   ```

3. Check ThresholdEvaluator logs

---

## Cost Management

### Estimated Monthly Costs (Demo Usage)

- Azure Functions: ~$5
- Event Grid: ~$0.60
- Storage: ~$1
- Application Insights: ~$2
- **Total Azure: ~$9/month**

- Microsoft Fabric (F2): ~$700/month
  - *Use free trial for demo*

### Cost Optimization

1. **Use Fabric Free Trial:**
   - 60-day trial available
   - No credit card required

2. **Disable Demo:**
   ```bash
   # Stop data ingestion pipeline
   # Disable functions when not demoing
   az functionapp stop \
     --name $FUNCTION_APP_NAME \
     --resource-group parametric-insurance-rg
   ```

3. **Delete Resources After Demo:**
   ```bash
   az group delete \
     --name parametric-insurance-rg \
     --yes --no-wait
   ```

---

## Next Steps

1. **Customize Policies:**
   - Edit `fabric/sql/sample_policies.sql`
   - Add your specific business scenarios

2. **Extend AI Agent:**
   - Add fraud detection rules
   - Integrate additional data sources
   - Customize payout calculations

3. **Build Power BI Dashboard:**
   - Connect to Warehouse
   - Create visualizations
   - Share with stakeholders

4. **Production Deployment:**
   - Use Managed Identities instead of API keys
   - Enable VNET integration
   - Set up monitoring alerts
   - Implement backup/DR

---

## Support

For issues or questions:
- Review logs in Application Insights
- Check Fabric pipeline run history
- Review this troubleshooting guide
- Contact: demo-support@yourcompany.com

---

**Deployment Complete! 🎉**

Your parametric insurance demo is ready to run.
