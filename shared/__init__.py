"""
Shared modules for Parametric Insurance Demo
"""
from .config import (
    azure_config,
    eventgrid_config,
    fabric_config,
    foundry_config,
    external_api_config,
    policy_config,
    validate_config
)
from .models import (
    OutageEvent,
    WeatherData,
    Policy,
    Claim,
    Payout,
    AIValidationResult,
    Location,
    OutageStatus,
    ClaimStatus,
    PayoutStatus
)
from .fabric_client import FabricClient
from .eventgrid_client import EventGridClient

__all__ = [
    'azure_config',
    'eventgrid_config',
    'fabric_config',
    'foundry_config',
    'external_api_config',
    'policy_config',
    'validate_config',
    'OutageEvent',
    'WeatherData',
    'Policy',
    'Claim',
    'Payout',
    'AIValidationResult',
    'Location',
    'OutageStatus',
    'ClaimStatus',
    'PayoutStatus',
    'FabricClient',
    'EventGridClient'
]
