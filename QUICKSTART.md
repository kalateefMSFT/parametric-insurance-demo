# Quick Start Guide - 30 Minutes to Running Demo

This guide gets you from zero to a running parametric insurance demo in 30 minutes.

## Prerequisites Check (2 minutes)

### Required Software
```bash
# Check Azure CLI
az --version
# Need: v2.50+

# Check Python
python --version
# Need: 3.11+

# Check Azure Functions Core Tools
func --version
# Need: 4.x
```

### Install Missing Tools

**Azure CLI:**
```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**Azure Functions Core Tools:**
```bash
# macOS
brew tap azure/functions
brew install azure-functions-core-tools@4

# Windows
npm install -g azure-functions-core-tools@4

# Linux
wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

## Step 1: Project Setup (3 minutes)

```bash
# Clone repository
git clone <repository-url>
cd parametric-insurance-demo

# Verify structure
python verify_structure.py

# Install Python dependencies
pip install -r setup/requirements.txt
```

**Expected Output:**
```
✓ All files present - Project structure is complete!
Total expected files: 37
Files found: 37
```

## Step 2: Azure Login (2 minutes)

```bash
# Login to Azure
az login

# Set subscription (if you have multiple)
az account list --output table
az account set --subscription "<your-subscription-id>"

# Verify
az account show
```

## Step 3: Create Azure Resources (5 minutes)

```bash
cd setup
./azure-setup.sh
```

**What this creates:**
- Resource Group: `parametric-insurance-rg`
- Storage Account: `parametricsa<random>`
- Event Grid Topic: `parametric-insurance-events`
- Function App: `parametric-insurance-func-<random>`
- Application Insights: `parametric-insurance-insights`

**Expected Output:**
```
============================================================================
Azure Resources Created Successfully!
============================================================================

Resource Group:        parametric-insurance-rg
Location:              eastus
Function App:          parametric-insurance-func-12345
Event Grid Topic:      parametric-insurance-events

Event Grid Endpoint:   https://...

.env file created at ../.env
```

**Action Required:** The script creates a `.env` file. You'll update it in Step 4.

## Step 4: Microsoft Fabric Setup (10 minutes)

### 4.1 Create Workspace

1. Go to [Microsoft Fabric](https://app.fabric.microsoft.com/)
2. Click **Workspaces** → **New Workspace**
3. Name: `Parametric Insurance`
4. Select license tier (F2+ recommended, or use trial)

### 4.2 Create Lakehouse

1. In workspace, click **New** → **Lakehouse**
2. Name: `parametric_insurance_lakehouse`
3. Wait for provisioning (~1 minute)

### 4.3 Create Warehouse

1. In workspace, click **New** → **Warehouse**  
2. Name: `parametric_insurance_warehouse`
3. Wait for provisioning (~1 minute)

### 4.4 Get Connection Details

**Workspace ID:**
- Look at URL: `https://app.fabric.microsoft.com/groups/{workspace-id}/...`
- Copy the GUID

**Lakehouse ID:**
- Open Lakehouse → Settings → Copy ID

**Warehouse Connection String:**
- Open Warehouse → Settings → Connection strings
- Copy SQL connection string (format below)

```
Driver={ODBC Driver 18 for SQL Server};Server=<workspace>.datawarehouse.fabric.microsoft.com;Database=parametric_insurance_warehouse;Authentication=ActiveDirectoryInteractive;
```

### 4.5 Update .env File

```bash
cd ..  # Back to project root
nano .env  # or use your editor
```

Update these lines:
```env
FABRIC_WORKSPACE_ID=<your-workspace-id>
FABRIC_LAKEHOUSE_ID=<your-lakehouse-id>
FABRIC_WAREHOUSE_CONNECTION=<your-connection-string>
```

### 4.6 Run SQL Scripts

1. Open Warehouse in Fabric
2. Click **New SQL Query**
3. Copy content from `fabric/sql/create_warehouse_schema.sql`
4. Paste and **Run**
5. Create another query
6. Copy content from `fabric/sql/sample_policies.sql`
7. Paste and **Run**

**Verify:**
```sql
SELECT COUNT(*) FROM policies;
-- Should return 11
```

### 4.7 Import Notebook

1. In workspace, click **Import** → **Notebook**
2. Upload: `fabric/notebooks/01_data_ingestion.py`
3. Open notebook
4. Click **Lakehouse** → Attach to `parametric_insurance_lakehouse`

## Step 5: Microsoft Foundry Setup (5 minutes)

### Option A: Use Azure OpenAI (Recommended for Demo)

1. Update `.env`:
```env
FOUNDRY_ENDPOINT=https://<your-openai>.openai.azure.com/
FOUNDRY_API_KEY=<your-openai-key>
```

2. The agent will use Azure OpenAI for validation

### Option B: Use Rule-Based Fallback

If you don't have Foundry/OpenAI access:

1. Leave `.env` values empty:
```env
FOUNDRY_ENDPOINT=
FOUNDRY_API_KEY=
```

2. The system will automatically use rule-based validation (still works!)

## Step 6: Deploy Azure Functions (3 minutes)

```bash
cd functions

# Get function app name
FUNCTION_APP=$(grep FUNCTION_APP_NAME ../.env | cut -d '=' -f2)

# Deploy
func azure functionapp publish $FUNCTION_APP

# Verify deployment
az functionapp function list \
  --name $FUNCTION_APP \
  --resource-group parametric-insurance-rg \
  --output table
```

**Expected Output:**
```
Name                        FunctionType
--------------------------  --------------
OutageMonitor              timerTrigger
ThresholdEvaluator         eventGridTrigger
PayoutProcessor            eventGridTrigger
OutageResolutionMonitor    timerTrigger
```

## Step 7: Run Demo! (2 minutes)

```bash
cd ../demo
python run_demo.py --scenario storm_seattle
```

**Expected Output:**
```
============================================================================
DEMO SCENARIO: Seattle Thunderstorm Outage
============================================================================
Severe thunderstorm causes 3-hour power outage affecting downtown businesses

[INFO] Creating outage event in Fabric
[SUCCESS] Outage event created: OUT-SEATTLECITYLIGHT-...
[INFO] Publishing 'outage.detected' event to Event Grid
[SUCCESS] Event published successfully
[INFO] Azure Functions processing events...

============================================================================
DEMO COMPLETE
============================================================================
Total Claims Processed: 2
Total Payout Amount: $2,151.25
============================================================================
```

## Troubleshooting

### Issue: Function deployment fails

**Solution:**
```bash
# Check if logged in
az account show

# Check if function app exists
az functionapp show --name $FUNCTION_APP --resource-group parametric-insurance-rg

# Try deploying again
func azure functionapp publish $FUNCTION_APP --build remote
```

### Issue: Fabric connection fails

**Solution:**
```bash
# Install ODBC driver (if not already)
# Ubuntu/Debian:
sudo apt-get install unixodbc-dev msodbcsql18

# macOS:
brew install unixodbc

# Test connection
python -c "import pyodbc; print(pyodbc.drivers())"
```

### Issue: No outages detected

**Solution:**
The demo creates simulated outages. Real outages from PowerOutage.us require:
1. Fabric notebook running (manually run it first)
2. Wait 5 minutes for next scheduled run
3. Actual outages in monitored ZIP codes

For testing, use demo scenarios:
```bash
python run_demo.py --scenario storm_seattle
python run_demo.py --scenario sf_earthquake
python run_demo.py --scenario ny_hurricane
```

## Next Steps

### View Results

**1. Check Application Insights:**
```bash
# Get instrumentation key
grep APPINSIGHTS_INSTRUMENTATIONKEY .env

# Open in portal
az portal open --resource parametric-insurance-insights --resource-group parametric-insurance-rg
```

**2. Query Fabric Warehouse:**
```sql
-- See all claims
SELECT * FROM claims ORDER BY filed_at DESC;

-- See all payouts
SELECT * FROM payouts ORDER BY initiated_at DESC;

-- Summary stats
SELECT * FROM v_claim_statistics;
```

**3. Monitor Functions:**
```bash
# Stream logs
az functionapp log tail \
  --name $FUNCTION_APP \
  --resource-group parametric-insurance-rg
```

### Run More Scenarios

```bash
# List available scenarios
python run_demo.py --list-scenarios

# Run different scenarios
python run_demo.py --scenario sf_earthquake
python run_demo.py --scenario ny_hurricane
```

### Customize

1. **Add your own policies:**
   - Edit `fabric/sql/sample_policies.sql`
   - Add new businesses with your parameters

2. **Modify AI logic:**
   - Edit `foundry/agents/claims_validator_agent.py`
   - Adjust severity multipliers, fraud detection rules

3. **Change thresholds:**
   - Update policies in Fabric Warehouse:
   ```sql
   UPDATE policies 
   SET threshold_minutes = 90, hourly_rate = 750
   WHERE policy_id = 'BI-001';
   ```

## Success Checklist

- [ ] Azure resources created
- [ ] Fabric workspace, lakehouse, warehouse created
- [ ] SQL schema and sample policies loaded
- [ ] `.env` file updated with all IDs
- [ ] Functions deployed successfully
- [ ] Demo runs and shows claims processed
- [ ] Can query results in Fabric Warehouse

## Cost Management

**Pause demo when not in use:**
```bash
# Stop function app
az functionapp stop --name $FUNCTION_APP --resource-group parametric-insurance-rg

# Resume when needed
az functionapp start --name $FUNCTION_APP --resource-group parametric-insurance-rg
```

**Delete everything:**
```bash
az group delete --name parametric-insurance-rg --yes --no-wait
```

## Get Help

1. Check logs in Application Insights
2. Review DEPLOYMENT.md for detailed steps
3. Run verification: `python verify_structure.py`
4. Check function status: `az functionapp function list ...`

---

**Congratulations! Your parametric insurance demo is running!** 🎉

Try the other scenarios, customize policies, and show off your AI-powered insurance automation!
