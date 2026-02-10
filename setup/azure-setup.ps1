# ============================================================================
# Azure Resource Setup Script (PowerShell)
# Parametric Insurance Demo
# ============================================================================

param(
    [string]$ResourceGroup = "parametric-insurance-rg",
    [string]$Location = "eastus",
    [string]$SubscriptionId = $env:AZURE_SUBSCRIPTION_ID
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resource names
$FunctionAppName = "parametric-insurance-func-$(Get-Random -Maximum 99999)"
$StorageAccountName = "parametricsa$(Get-Random -Maximum 99999)"
$AppInsightsName = "parametric-insurance-insights"
$EventGridTopicName = "parametric-insurance-events"

# Helper functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Azure CLI is not installed. Please install it first."
        Write-Host "Download from: https://aka.ms/installazurecliwindows"
        exit 1
    }
    
    # Check if logged in
    try {
        $null = az account show 2>$null
    }
    catch {
        Write-Error-Custom "Not logged into Azure. Please run 'az login' first."
        exit 1
    }
    
    # Check subscription
    if (-not $SubscriptionId) {
        Write-Warn "AZURE_SUBSCRIPTION_ID not set. Using default subscription."
        $SubscriptionId = (az account show --query id -o tsv)
    }
    
    Write-Info "Using subscription: $SubscriptionId"
    az account set --subscription $SubscriptionId
    
    Write-Info "Prerequisites check complete!"
}

# Create resource group
function New-ResourceGroupIfNotExists {
    Write-Info "Creating resource group: $ResourceGroup"
    
    $rgExists = az group exists --name $ResourceGroup
    
    if ($rgExists -eq "true") {
        Write-Warn "Resource group already exists. Skipping creation."
    }
    else {
        az group create `
            --name $ResourceGroup `
            --location $Location
        Write-Info "Resource group created successfully!"
    }
}

# Create storage account
function New-StorageAccountResource {
    Write-Info "Creating storage account: $StorageAccountName"
    
    az storage account create `
        --name $StorageAccountName `
        --resource-group $ResourceGroup `
        --location $Location `
        --sku Standard_LRS `
        --kind StorageV2
    
    Write-Info "Storage account created successfully!"
}

# Create Application Insights
function New-AppInsightsResource {
    Write-Info "Creating Application Insights: $AppInsightsName"
    
    az monitor app-insights component create `
        --app $AppInsightsName `
        --resource-group $ResourceGroup `
        --location $Location `
        --application-type web
    
    $script:InstrumentationKey = az monitor app-insights component show `
        --app $AppInsightsName `
        --resource-group $ResourceGroup `
        --query instrumentationKey -o tsv
    
    Write-Info "Application Insights created successfully!"
    Write-Info "Instrumentation Key: $InstrumentationKey"
}

# Create Event Grid Topic
function New-EventGridTopicResource {
    Write-Info "Creating Event Grid Topic: $EventGridTopicName"
    
    az eventgrid topic create `
        --name $EventGridTopicName `
        --resource-group $ResourceGroup `
        --location $Location
    
    $script:EventGridEndpoint = az eventgrid topic show `
        --name $EventGridTopicName `
        --resource-group $ResourceGroup `
        --query endpoint -o tsv
    
    $script:EventGridKey = az eventgrid topic key list `
        --name $EventGridTopicName `
        --resource-group $ResourceGroup `
        --query key1 -o tsv
    
    Write-Info "Event Grid Topic created successfully!"
    Write-Info "Endpoint: $EventGridEndpoint"
}

# Create Function App
function New-FunctionAppResource {
    Write-Info "Creating Function App: $FunctionAppName"
    
    # Create Function App
    az functionapp create `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        --storage-account $StorageAccountName `
        --consumption-plan-location $Location `
        --runtime python `
        --runtime-version 3.11 `
        --functions-version 4 `
        --os-type Linux
    
    # Configure Application Insights
    az functionapp config appsettings set `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        --settings "APPINSIGHTS_INSTRUMENTATIONKEY=$InstrumentationKey"
    
    # Configure Event Grid settings
    az functionapp config appsettings set `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        --settings `
            "EVENTGRID_TOPIC_ENDPOINT=$EventGridEndpoint" `
            "EVENTGRID_KEY=$EventGridKey"
    
    Write-Info "Function App created successfully!"
}

# Create Event Grid subscriptions
function New-EventGridSubscriptions {
    Write-Info "Creating Event Grid subscriptions..."
    
    # Get Function App ID
    $FunctionAppId = az functionapp show `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        --query id -o tsv
    
    # Subscription for threshold evaluator (listens to outage.detected)
    az eventgrid event-subscription create `
        --name "threshold-evaluator-subscription" `
        --source-resource-id "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.EventGrid/topics/$EventGridTopicName" `
        --endpoint "$FunctionAppId/functions/ThresholdEvaluator" `
        --endpoint-type azurefunction `
        --included-event-types "outage.detected"
    
    # Subscription for payout processor (listens to claim.approved)
    az eventgrid event-subscription create `
        --name "payout-processor-subscription" `
        --source-resource-id "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.EventGrid/topics/$EventGridTopicName" `
        --endpoint "$FunctionAppId/functions/PayoutProcessor" `
        --endpoint-type azurefunction `
        --included-event-types "claim.approved"
    
    Write-Info "Event Grid subscriptions created successfully!"
}

# Generate .env file
function New-EnvFile {
    Write-Info "Generating .env file..."
    
    $envContent = @"
# Azure Configuration
AZURE_SUBSCRIPTION_ID=$SubscriptionId
RESOURCE_GROUP=$ResourceGroup
LOCATION=$Location

# Event Grid
EVENTGRID_TOPIC_ENDPOINT=$EventGridEndpoint
EVENTGRID_KEY=$EventGridKey

# Function App
FUNCTION_APP_NAME=$FunctionAppName

# Application Insights
APPINSIGHTS_INSTRUMENTATIONKEY=$InstrumentationKey

# Storage Account
STORAGE_ACCOUNT_NAME=$StorageAccountName

# Microsoft Fabric (Update these manually)
FABRIC_WORKSPACE_ID=your-workspace-id
FABRIC_LAKEHOUSE_ID=your-lakehouse-id
FABRIC_WAREHOUSE_CONNECTION=your-connection-string

# Microsoft Foundry (Update these manually)
FOUNDRY_ENDPOINT=your-foundry-endpoint
FOUNDRY_API_KEY=your-foundry-api-key

# External APIs (Optional)
POWEROUTAGE_API_KEY=
NOAA_API_KEY=
TWITTER_BEARER_TOKEN=
"@
    
    $envPath = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
    $envContent | Out-File -FilePath $envPath -Encoding UTF8
    
    Write-Info ".env file created at $envPath"
    Write-Warn "Please update Fabric and Foundry settings manually!"
}

# Display summary
function Show-Summary {
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host "Azure Resources Created Successfully!" -ForegroundColor Cyan
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Resource Group:        $ResourceGroup"
    Write-Host "Location:              $Location"
    Write-Host "Storage Account:       $StorageAccountName"
    Write-Host "Function App:          $FunctionAppName"
    Write-Host "Application Insights:  $AppInsightsName"
    Write-Host "Event Grid Topic:      $EventGridTopicName"
    Write-Host ""
    Write-Host "Event Grid Endpoint:   $EventGridEndpoint"
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Update .env file with Fabric and Foundry credentials"
    Write-Host "2. Deploy Azure Functions:"
    Write-Host "   cd ..\functions"
    Write-Host "   func azure functionapp publish $FunctionAppName"
    Write-Host ""
    Write-Host "3. Setup Microsoft Fabric:"
    Write-Host "   - Create Workspace, Lakehouse, and Warehouse"
    Write-Host "   - Run SQL scripts in fabric/sql/"
    Write-Host "   - Import notebooks from fabric/notebooks/"
    Write-Host ""
    Write-Host "4. Configure Microsoft Foundry:"
    Write-Host "   - Create AI agent using foundry/agents/claims_validator_agent.py"
    Write-Host "   - Update FOUNDRY_ENDPOINT and FOUNDRY_API_KEY in .env"
    Write-Host ""
    Write-Host "5. Test the demo:"
    Write-Host "   python demo/run_demo.py --scenario storm_seattle"
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Cyan
}

# Main execution
function Main {
    Write-Info "Starting Azure resource setup..."
    Write-Host ""
    
    try {
        Test-Prerequisites
        New-ResourceGroupIfNotExists
        New-StorageAccountResource
        New-AppInsightsResource
        New-EventGridTopicResource
        New-FunctionAppResource
        New-EventGridSubscriptions
        New-EnvFile
        
        Show-Summary
    }
    catch {
        Write-Error-Custom "Setup failed: $_"
        Write-Host $_.ScriptStackTrace
        exit 1
    }
}

# Run main function
Main
