"""
Shared configuration for Parametric Insurance Demo
"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AzureConfig:
    """Azure resource configuration"""
    subscription_id: str
    resource_group: str
    location: str
    
    @classmethod
    def from_env(cls):
        return cls(
            subscription_id=os.getenv('AZURE_SUBSCRIPTION_ID', ''),
            resource_group=os.getenv('RESOURCE_GROUP', 'parametric-insurance-rg'),
            location=os.getenv('LOCATION', 'westus3')
        )


@dataclass
class EventGridConfig:
    """Event Grid configuration"""
    topic_endpoint: str
    topic_key: str
    
    # Event types
    OUTAGE_DETECTED = "outage.detected"
    OUTAGE_THRESHOLD_EXCEEDED = "outage.threshold.exceeded"
    OUTAGE_VALIDATED = "outage.validated"
    OUTAGE_RESOLVED = "outage.resolved"
    CLAIM_APPROVED = "claim.approved"
    CLAIM_DENIED = "claim.denied"
    PAYOUT_PROCESSED = "payout.processed"
    
    @classmethod
    def from_env(cls):
        return cls(
            topic_endpoint=os.getenv('EVENTGRID_TOPIC_ENDPOINT', ''),
            topic_key=os.getenv('EVENTGRID_KEY', '')
        )


@dataclass
class FabricConfig:
    """Microsoft Fabric configuration"""
    workspace_id: str
    lakehouse_id: str
    warehouse_server: str
    warehouse_database: str = "parametric_insurance_warehouse"
    lakehouse_name: str = "parametric_insurance_lakehouse"
    warehouse_name: str = "parametric_insurance_warehouse"
    
    # Table names
    TABLE_OUTAGE_EVENTS = "outage_events"
    TABLE_WEATHER_DATA = "weather_data"
    TABLE_SOCIAL_SIGNALS = "social_signals"
    TABLE_POLICIES = "policies"
    TABLE_CLAIMS = "claims"
    TABLE_PAYOUTS = "payouts"
    
    @classmethod
    def from_env(cls):
        return cls(
            workspace_id=os.getenv('FABRIC_WORKSPACE_ID', ''),
            lakehouse_id=os.getenv('FABRIC_LAKEHOUSE_ID', ''),
            warehouse_server=os.getenv('FABRIC_WAREHOUSE_SERVER', ''),
            warehouse_database=os.getenv('FABRIC_DATABASE', 'parametric_insurance_warehouse')
        )


@dataclass
class FoundryConfig:
    """Microsoft Foundry AI configuration"""
    endpoint: str
    api_key: str
    agent_id: str = "claims-validator"
    model: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.2  # Lower for consistent claims validation
    
    @classmethod
    def from_env(cls):
        return cls(
            endpoint=os.getenv('FOUNDRY_ENDPOINT', ''),
            api_key=os.getenv('FOUNDRY_API_KEY', ''),
            agent_id=os.getenv('FOUNDRY_AGENT_ID', 'claims-validator')
        )


@dataclass
class ExternalAPIConfig:
    """External API configuration"""
    poweroutage_api_url: str = "https://poweroutage.us/api/outages"
    poweroutage_api_key: Optional[str] = None
    
    noaa_api_url: str = "https://api.weather.gov"
    noaa_api_key: Optional[str] = None
    
    twitter_api_url: str = "https://api.twitter.com/2"
    twitter_bearer_token: Optional[str] = None
    
    # User agent required by NOAA
    user_agent: str = "ParametricInsuranceDemo/1.0"
    
    @classmethod
    def from_env(cls):
        return cls(
            poweroutage_api_key=os.getenv('POWEROUTAGE_API_KEY'),
            noaa_api_key=os.getenv('NOAA_API_KEY'),
            twitter_bearer_token=os.getenv('TWITTER_BEARER_TOKEN')
        )


@dataclass
class PolicyConfig:
    """Default policy configuration"""
    # Default threshold in minutes
    DEFAULT_THRESHOLD_MINUTES = 120
    
    # Default hourly rate in USD
    DEFAULT_HOURLY_RATE = 500
    
    # Maximum payout per claim
    MAX_PAYOUT_PER_CLAIM = 50000
    
    # Severity multipliers
    SEVERITY_MULTIPLIERS = {
        "low": 1.0,
        "medium": 1.2,
        "high": 1.5,
        "severe": 2.0
    }
    
    # Fraud detection thresholds
    MAX_CLAIMS_PER_MONTH = 5
    MAX_CLAIMS_PER_YEAR = 20


# Singleton instances
azure_config = AzureConfig.from_env()
eventgrid_config = EventGridConfig.from_env()
fabric_config = FabricConfig.from_env()
foundry_config = FoundryConfig.from_env()
external_api_config = ExternalAPIConfig.from_env()
policy_config = PolicyConfig()


def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not eventgrid_config.topic_endpoint:
        errors.append("EVENTGRID_TOPIC_ENDPOINT not set")
    
    if not eventgrid_config.topic_key:
        errors.append("EVENTGRID_KEY not set")
    
    if not fabric_config.workspace_id:
        errors.append("FABRIC_WORKSPACE_ID not set")
    
    if not fabric_config.warehouse_server:
        errors.append("FABRIC_WAREHOUSE_SERVER not set")
    
    if not foundry_config.endpoint:
        errors.append("FOUNDRY_ENDPOINT not set")
    
    if not foundry_config.api_key:
        errors.append("FOUNDRY_API_KEY not set")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True


if __name__ == "__main__":
    # Test configuration
    try:
        validate_config()
        print("✓ Configuration valid")
        print(f"  Resource Group: {azure_config.resource_group}")
        print(f"  Event Grid: {eventgrid_config.topic_endpoint}")
        print(f"  Fabric Workspace: {fabric_config.workspace_id}")
        print(f"  Fabric Warehouse Server: {fabric_config.warehouse_server}")
        print(f"  Foundry Endpoint: {foundry_config.endpoint}")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
