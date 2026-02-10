#!/bin/bash

# ============================================================================
# Azure Resource Setup Script
# Parametric Insurance Demo
# ============================================================================

set -e  # Exit on error

# Configuration
RESOURCE_GROUP=${RESOURCE_GROUP:-"parametric-insurance-rg"}
LOCATION=${LOCATION:-"eastus"}
SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}

# Resource names
FUNCTION_APP_NAME="parametric-insurance-func-${RANDOM}"
STORAGE_ACCOUNT_NAME="parametricsa${RANDOM}"
APP_INSIGHTS_NAME="parametric-insurance-insights"
EVENTGRID_TOPIC_NAME="parametric-insurance-events"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure. Please run 'az login' first."
        exit 1
    fi
    
    # Check subscription
    if [ -z "$SUBSCRIPTION_ID" ]; then
        log_warn "AZURE_SUBSCRIPTION_ID not set. Using default subscription."
        SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    fi
    
    log_info "Using subscription: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
    
    log_info "Prerequisites check complete!"
}

# Create resource group
create_resource_group() {
    log_info "Creating resource group: $RESOURCE_GROUP"
    
    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log_warn "Resource group already exists. Skipping creation."
    else
        az group create \
            --name "$RESOURCE_GROUP" \
            --location "$LOCATION"
        log_info "Resource group created successfully!"
    fi
}

# Create storage account
create_storage_account() {
    log_info "Creating storage account: $STORAGE_ACCOUNT_NAME"
    
    az storage account create \
        --name "$STORAGE_ACCOUNT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku Standard_LRS \
        --kind StorageV2
    
    log_info "Storage account created successfully!"
}

# Create Application Insights
create_app_insights() {
    log_info "Creating Application Insights: $APP_INSIGHTS_NAME"
    
    az monitor app-insights component create \
        --app "$APP_INSIGHTS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --application-type web
    
    INSTRUMENTATION_KEY=$(az monitor app-insights component show \
        --app "$APP_INSIGHTS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query instrumentationKey -o tsv)
    
    log_info "Application Insights created successfully!"
    log_info "Instrumentation Key: $INSTRUMENTATION_KEY"
}

# Create Event Grid Topic
create_eventgrid_topic() {
    log_info "Creating Event Grid Topic: $EVENTGRID_TOPIC_NAME"
    
    az eventgrid topic create \
        --name "$EVENTGRID_TOPIC_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION"
    
    EVENTGRID_ENDPOINT=$(az eventgrid topic show \
        --name "$EVENTGRID_TOPIC_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query endpoint -o tsv)
    
    EVENTGRID_KEY=$(az eventgrid topic key list \
        --name "$EVENTGRID_TOPIC_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query key1 -o tsv)
    
    log_info "Event Grid Topic created successfully!"
    log_info "Endpoint: $EVENTGRID_ENDPOINT"
}

# Create Function App
create_function_app() {
    log_info "Creating Function App: $FUNCTION_APP_NAME"
    
    # Create Function App
    az functionapp create \
        --name "$FUNCTION_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --storage-account "$STORAGE_ACCOUNT_NAME" \
        --consumption-plan-location "$LOCATION" \
        --runtime python \
        --runtime-version 3.11 \
        --functions-version 4 \
        --os-type Linux
    
    # Configure Application Insights
    az functionapp config appsettings set \
        --name "$FUNCTION_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings "APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY"
    
    # Configure Event Grid settings
    az functionapp config appsettings set \
        --name "$FUNCTION_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            "EVENTGRID_TOPIC_ENDPOINT=$EVENTGRID_ENDPOINT" \
            "EVENTGRID_KEY=$EVENTGRID_KEY"
    
    log_info "Function App created successfully!"
}

# Create Event Grid subscriptions
create_eventgrid_subscriptions() {
    log_info "Creating Event Grid subscriptions..."
    
    # Get Function App endpoints
    FUNCTION_APP_ID=$(az functionapp show \
        --name "$FUNCTION_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query id -o tsv)
    
    # Subscription for threshold evaluator (listens to outage.detected)
    az eventgrid event-subscription create \
        --name "threshold-evaluator-subscription" \
        --source-resource-id "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.EventGrid/topics/$EVENTGRID_TOPIC_NAME" \
        --endpoint "$FUNCTION_APP_ID/functions/ThresholdEvaluator" \
        --endpoint-type azurefunction \
        --included-event-types "outage.detected"
    
    # Subscription for payout processor (listens to claim.approved)
    az eventgrid event-subscription create \
        --name "payout-processor-subscription" \
        --source-resource-id "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.EventGrid/topics/$EVENTGRID_TOPIC_NAME" \
        --endpoint "$FUNCTION_APP_ID/functions/PayoutProcessor" \
        --endpoint-type azurefunction \
        --included-event-types "claim.approved"
    
    log_info "Event Grid subscriptions created successfully!"
}

# Generate .env file
generate_env_file() {
    log_info "Generating .env file..."
    
    cat > ../.env << EOF
# Azure Configuration
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
RESOURCE_GROUP=$RESOURCE_GROUP
LOCATION=$LOCATION

# Event Grid
EVENTGRID_TOPIC_ENDPOINT=$EVENTGRID_ENDPOINT
EVENTGRID_KEY=$EVENTGRID_KEY

# Function App
FUNCTION_APP_NAME=$FUNCTION_APP_NAME

# Application Insights
APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY

# Storage Account
STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME

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
EOF
    
    log_info ".env file created at ../.env"
    log_warn "Please update Fabric and Foundry settings manually!"
}

# Display summary
display_summary() {
    echo ""
    echo "============================================================================"
    echo "Azure Resources Created Successfully!"
    echo "============================================================================"
    echo ""
    echo "Resource Group:        $RESOURCE_GROUP"
    echo "Location:              $LOCATION"
    echo "Storage Account:       $STORAGE_ACCOUNT_NAME"
    echo "Function App:          $FUNCTION_APP_NAME"
    echo "Application Insights:  $APP_INSIGHTS_NAME"
    echo "Event Grid Topic:      $EVENTGRID_TOPIC_NAME"
    echo ""
    echo "Event Grid Endpoint:   $EVENTGRID_ENDPOINT"
    echo ""
    echo "============================================================================"
    echo "Next Steps:"
    echo "============================================================================"
    echo ""
    echo "1. Update .env file with Fabric and Foundry credentials"
    echo "2. Deploy Azure Functions:"
    echo "   cd ../functions"
    echo "   func azure functionapp publish $FUNCTION_APP_NAME"
    echo ""
    echo "3. Setup Microsoft Fabric:"
    echo "   - Create Workspace, Lakehouse, and Warehouse"
    echo "   - Run SQL scripts in fabric/sql/"
    echo "   - Import notebooks from fabric/notebooks/"
    echo ""
    echo "4. Configure Microsoft Foundry:"
    echo "   - Create AI agent using foundry/agents/claims_validator_agent.py"
    echo "   - Update FOUNDRY_ENDPOINT and FOUNDRY_API_KEY in .env"
    echo ""
    echo "5. Test the demo:"
    echo "   python demo/run_demo.py --scenario storm_seattle"
    echo ""
    echo "============================================================================"
}

# Main execution
main() {
    log_info "Starting Azure resource setup..."
    echo ""
    
    check_prerequisites
    create_resource_group
    create_storage_account
    create_app_insights
    create_eventgrid_topic
    create_function_app
    create_eventgrid_subscriptions
    generate_env_file
    
    display_summary
}

# Run main function
main
