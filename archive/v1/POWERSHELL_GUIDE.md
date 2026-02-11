# PowerShell Deployment Guide

This guide is for Windows users deploying with PowerShell instead of Bash.

## Prerequisites

### Required Software

1. **PowerShell 7+** (recommended) or PowerShell 5.1+
   ```powershell
   $PSVersionTable.PSVersion
   # Should show 7.x or 5.1+
   ```

2. **Azure CLI**
   ```powershell
   az --version
   # Download from: https://aka.ms/installazurecliwindows
   ```

3. **Azure Functions Core Tools**
   ```powershell
   func --version
   # Install via: npm install -g azure-functions-core-tools@4
   # Or download from: https://docs.microsoft.com/azure/azure-functions/functions-run-local
   ```

4. **Python 3.11+**
   ```powershell
   python --version
   # Download from: https://www.python.org/downloads/
   ```

## Quick Start (Windows)

### Step 1: Install Dependencies

```powershell
# Navigate to project
cd parametric-insurance-demo

# Install Python packages
pip install -r setup\requirements.txt
```

### Step 2: Login to Azure

```powershell
# Login
az login

# List subscriptions
az account list --output table

# Set subscription
az account set --subscription "<your-subscription-id>"

# Verify
az account show
```

### Step 3: Run PowerShell Setup Script

```powershell
# Navigate to setup folder
cd setup

# Run the PowerShell script
.\azure-setup.ps1

# OR with custom parameters
.\azure-setup.ps1 -ResourceGroup "my-custom-rg" -Location "westus2"
```

**Script Parameters:**
- `-ResourceGroup` - Name of resource group (default: "parametric-insurance-rg")
- `-Location` - Azure region (default: "eastus")
- `-SubscriptionId` - Azure subscription ID (default: from environment)

**Expected Output:**
```
[INFO] Checking prerequisites...
[INFO] Using subscription: 12345678-1234-1234-1234-123456789012
[INFO] Creating resource group: parametric-insurance-rg
[INFO] Creating storage account: parametricsa12345
[INFO] Creating Application Insights: parametric-insurance-insights
[INFO] Creating Event Grid Topic: parametric-insurance-events
[INFO] Creating Function App: parametric-insurance-func-12345

============================================================================
Azure Resources Created Successfully!
============================================================================

Resource Group:        parametric-insurance-rg
Function App:          parametric-insurance-func-12345
Event Grid Topic:      parametric-insurance-events
```

### Step 4: Verify .env File

```powershell
# The script creates a .env file in the project root
cd ..
notepad .env

# OR
cat .env
```

### Step 5: Deploy Functions

```powershell
# Navigate to functions folder
cd functions

# Get function app name from .env
$FunctionApp = (Get-Content ..\.env | Select-String "FUNCTION_APP_NAME").ToString().Split("=")[1]

# Deploy
func azure functionapp publish $FunctionApp

# Verify deployment
az functionapp function list `
  --name $FunctionApp `
  --resource-group parametric-insurance-rg `
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

## PowerShell-Specific Commands

### Managing Azure Resources

```powershell
# List all resources
az resource list `
  --resource-group parametric-insurance-rg `
  --output table

# Check function app status
az functionapp show `
  --name $FunctionApp `
  --resource-group parametric-insurance-rg `
  --query state

# Stream function logs
az functionapp log tail `
  --name $FunctionApp `
  --resource-group parametric-insurance-rg

# Stop function app (save costs)
az functionapp stop `
  --name $FunctionApp `
  --resource-group parametric-insurance-rg

# Start function app
az functionapp start `
  --name $FunctionApp `
  --resource-group parametric-insurance-rg
```

### Working with .env File

```powershell
# Read .env values
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        Write-Host "$name = $value"
    }
}

# Set environment variables from .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Check specific value
(Get-Content .env | Select-String "FUNCTION_APP_NAME").ToString().Split("=")[1]
```

### Running Tests

```powershell
# Navigate to tests
cd tests

# Run all tests
python run_tests.py

# Run specific test
python test_outage_monitor.py

# Run with verbose output
python -m pytest test_outage_monitor.py -v
```

### Running Demo

```powershell
# Navigate to demo folder
cd demo

# List scenarios
python run_demo.py --list-scenarios

# Run specific scenario
python run_demo.py --scenario storm_seattle

# Run with quiet mode
python run_demo.py --scenario sf_earthquake --quiet
```

## Troubleshooting (PowerShell)

### Issue: Execution Policy Error

```powershell
# Error: "cannot be loaded because running scripts is disabled"

# Solution: Allow script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Verify
Get-ExecutionPolicy -List
```

### Issue: Azure CLI Not Found

```powershell
# Check if installed
Get-Command az -ErrorAction SilentlyContinue

# If not found, install:
# Download from: https://aka.ms/installazurecliwindows
# Or use MSI installer
```

### Issue: Function Deployment Fails

```powershell
# Check if logged in
az account show

# Re-login if needed
az login

# Try remote build
func azure functionapp publish $FunctionApp --build remote

# Check function app exists
az functionapp show `
  --name $FunctionApp `
  --resource-group parametric-insurance-rg
```

### Issue: .env File Not Created

```powershell
# Check if script completed successfully
# Look for "Azure Resources Created Successfully!" message

# Manually create .env if needed
@"
AZURE_SUBSCRIPTION_ID=your-subscription-id
RESOURCE_GROUP=parametric-insurance-rg
EVENTGRID_TOPIC_ENDPOINT=your-endpoint
EVENTGRID_KEY=your-key
FUNCTION_APP_NAME=your-function-app-name
"@ | Out-File -FilePath .env -Encoding UTF8
```

### Issue: Python Module Not Found

```powershell
# Ensure you're using the correct Python
python --version

# Check pip
pip --version

# Install dependencies again
pip install -r setup\requirements.txt

# Or use virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r setup\requirements.txt
```

## PowerShell Aliases for Common Tasks

Add these to your PowerShell profile for quick access:

```powershell
# Open profile
notepad $PROFILE

# Add these functions:
function Deploy-Functions {
    param([string]$FunctionApp)
    cd functions
    func azure functionapp publish $FunctionApp
    cd ..
}

function Show-FunctionLogs {
    param([string]$FunctionApp, [string]$ResourceGroup = "parametric-insurance-rg")
    az functionapp log tail --name $FunctionApp --resource-group $ResourceGroup
}

function Run-Demo {
    param([string]$Scenario = "storm_seattle")
    cd demo
    python run_demo.py --scenario $Scenario
    cd ..
}

function Test-Project {
    cd tests
    python run_tests.py
    cd ..
}

# Save and reload
. $PROFILE
```

Usage:
```powershell
Deploy-Functions -FunctionApp "parametric-insurance-func-12345"
Show-FunctionLogs -FunctionApp "parametric-insurance-func-12345"
Run-Demo -Scenario "sf_earthquake"
Test-Project
```

## Azure Portal Integration

### Open Resources in Portal

```powershell
# Open resource group
az portal open --resource parametric-insurance-rg --resource-type resourceGroup

# Open specific resources (requires resource ID)
$FunctionAppId = az functionapp show `
  --name $FunctionApp `
  --resource-group parametric-insurance-rg `
  --query id -o tsv

az portal open --resource $FunctionAppId
```

### Monitor with PowerShell

```powershell
# Get function app metrics
az monitor metrics list `
  --resource $FunctionAppId `
  --metric "Requests" `
  --start-time (Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") `
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")

# Check Event Grid metrics
$EventGridTopicId = az eventgrid topic show `
  --name parametric-insurance-events `
  --resource-group parametric-insurance-rg `
  --query id -o tsv

az monitor metrics list `
  --resource $EventGridTopicId `
  --metric "PublishSuccessCount"
```

## Cleanup (PowerShell)

### Delete All Resources

```powershell
# Delete entire resource group
az group delete `
  --name parametric-insurance-rg `
  --yes `
  --no-wait

# Verify deletion (will show "NotFound" when complete)
az group show --name parametric-insurance-rg
```

### Delete Specific Resources

```powershell
# Delete function app only
az functionapp delete `
  --name $FunctionApp `
  --resource-group parametric-insurance-rg

# Delete Event Grid topic
az eventgrid topic delete `
  --name parametric-insurance-events `
  --resource-group parametric-insurance-rg
```

## Best Practices for Windows

1. **Use PowerShell 7** - Better performance and features
2. **Run as Administrator** when needed for installations
3. **Use Windows Terminal** - Better experience than CMD
4. **Enable Long Paths** if you get path too long errors:
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
     -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

## Next Steps

1. ✅ Azure resources created (via PowerShell script)
2. ⬜ Configure Microsoft Fabric (see DEPLOYMENT.md)
3. ⬜ Deploy Functions (see commands above)
4. ⬜ Run demo (see commands above)

---

**PowerShell Script Location:** `setup/azure-setup.ps1`

**Full Deployment Guide:** See `DEPLOYMENT.md` for Fabric and Foundry setup
