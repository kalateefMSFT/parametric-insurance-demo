"""
Azure Function: Threshold Evaluator
Event Grid triggered function that evaluates policy thresholds
and calls AI agent for validation
"""
import azure.functions as func
import logging
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.fabric_client import FabricClient
from shared.eventgrid_client import EventGridClient
from shared.models import (
    Claim, ClaimStatus, create_claim_id, 
    AIValidationResult, Location, OutageEvent, OutageStatus
)
from shared.config import policy_config


def call_foundry_agent(
    policy: dict,
    outage: dict,
    weather: dict = None,
    social_signals: list = None
) -> AIValidationResult:
    """
    Call Microsoft Foundry AI agent for claim validation
    
    Args:
        policy: Policy data
        outage: Outage event data
        weather: Weather data (optional)
        social_signals: Social media signals (optional)
        
    Returns:
        AIValidationResult object
    """
    try:
        # Import here to avoid circular dependencies
        from foundry.agents.claims_validator_agent import validate_claim
        
        result = validate_claim(
            policy=policy,
            outage=outage,
            weather=weather,
            social_signals=social_signals
        )
        
        return result
        
    except Exception as e:
        logging.error(f"Error calling Foundry agent: {e}")
        
        # Fallback to rule-based validation
        return fallback_validation(policy, outage, weather)


def fallback_validation(
    policy: dict,
    outage: dict,
    weather: dict = None
) -> AIValidationResult:
    """
    Fallback rule-based validation if AI agent is unavailable
    """
    # Calculate duration
    if outage.get('duration_minutes'):
        duration = outage['duration_minutes']
    else:
        # Estimate based on current time
        outage_start = datetime.fromisoformat(outage['outage_start'].replace('Z', '+00:00'))
        duration = (datetime.utcnow() - outage_start).total_seconds() / 60
    
    # Check threshold
    threshold = policy['threshold_minutes']
    
    if duration <= threshold:
        return AIValidationResult(
            decision="deny",
            confidence_score=0.95,
            payout_amount=0.0,
            reasoning=f"Outage duration ({duration:.0f} min) does not exceed threshold ({threshold} min)",
            evidence=[],
            fraud_signals=[],
            severity_assessment="low",
            weather_factor=1.0
        )
    
    # Calculate payout
    hours_over = (duration - threshold) / 60
    base_payout = hours_over * policy['hourly_rate']
    
    # Weather severity multiplier
    severity_multiplier = 1.0
    severity = "medium"
    
    if weather:
        if weather.get('severe_weather_alert'):
            severity_multiplier = 1.5
            severity = "high"
        elif weather.get('wind_speed_mph', 0) > 40:
            severity_multiplier = 1.2
            severity = "high"
    
    final_payout = min(
        base_payout * severity_multiplier,
        policy['max_payout']
    )
    
    return AIValidationResult(
        decision="approve",
        confidence_score=0.85,
        payout_amount=final_payout,
        reasoning=f"Threshold exceeded by {hours_over:.1f} hours. Weather severity: {severity}.",
        evidence=[
            {"type": "duration", "value": f"{duration:.0f} minutes"},
            {"type": "threshold", "value": f"{threshold} minutes"},
            {"type": "weather", "value": severity}
        ],
        fraud_signals=[],
        severity_assessment=severity,
        weather_factor=severity_multiplier
    )


def main(event: func.EventGridEvent):
    """
    Event Grid triggered function for threshold evaluation
    
    Triggered by: outage.detected events
    """
    logging.info(f'Threshold Evaluator triggered by event: {event.id}')
    
    try:
        # Parse event data
        event_data = event.get_json()
        logging.info(f'Event type: {event.event_type}')
        logging.info(f'Event subject: {event.subject}')
        
        # Get outage and policy details
        outage_event_id = event_data.get('event_id')
        affected_policies = event_data.get('affected_policies', [])
        
        if not affected_policies:
            logging.info('No affected policies - exiting')
            return
        
        logging.info(f'Processing {len(affected_policies)} affected policies')
        
        # Initialize clients
        fabric_client = FabricClient()
        eventgrid_client = EventGridClient()
        
        # Get outage details from Fabric
        outage_data = fabric_client.get_outage_event(outage_event_id)
        
        if not outage_data:
            logging.error(f'Outage event {outage_event_id} not found in Fabric')
            return
        
        # Get weather data
        weather_data = None
        if outage_data.get('zip_code'):
            weather_records = fabric_client.get_recent_weather(
                zip_code=outage_data['zip_code'],
                hours=6
            )
            if weather_records:
                weather_data = weather_records[0]  # Most recent
        
        # Process each affected policy
        for policy_id in affected_policies:
            try:
                # Get policy details
                policy_data = fabric_client.get_policy(policy_id)
                
                if not policy_data:
                    logging.error(f'Policy {policy_id} not found')
                    continue
                
                # Check if threshold is exceeded
                duration = outage_data.get('duration_minutes', 0)
                threshold = policy_data['threshold_minutes']
                
                if duration < threshold:
                    logging.info(
                        f'Policy {policy_id}: threshold not yet exceeded '
                        f'({duration} < {threshold} min)'
                    )
                    continue
                
                logging.info(
                    f'Policy {policy_id}: threshold exceeded '
                    f'({duration} >= {threshold} min)'
                )
                
                # Publish threshold exceeded event
                eventgrid_client.publish_threshold_exceeded(
                    policy_id=policy_id,
                    outage_event=OutageEvent(
                        event_id=outage_data['event_id'],
                        utility_name=outage_data['utility_name'],
                        location=Location(
                            latitude=outage_data['latitude'],
                            longitude=outage_data['longitude'],
                            zip_code=outage_data['zip_code']
                        ),
                        affected_customers=outage_data['affected_customers'],
                        outage_start=outage_data['outage_start'],
                        outage_end=outage_data.get('outage_end'),
                        duration_minutes=duration,
                        status=OutageStatus(outage_data['status'])
                    ),
                    duration_minutes=duration,
                    threshold_minutes=threshold
                )
                
                # Call AI agent for validation
                logging.info(f'Calling AI agent for policy {policy_id}')
                
                validation_result = call_foundry_agent(
                    policy=policy_data,
                    outage=outage_data,
                    weather=weather_data
                )
                
                logging.info(
                    f'AI decision: {validation_result.decision} '
                    f'(confidence: {validation_result.confidence_score:.2f})'
                )
                
                # Create claim record
                claim = Claim(
                    claim_id=create_claim_id(policy_id, outage_event_id),
                    policy_id=policy_id,
                    outage_event_id=outage_event_id,
                    status=ClaimStatus.APPROVED if validation_result.decision == "approve" else ClaimStatus.DENIED,
                    filed_at=datetime.utcnow(),
                    validated_at=datetime.utcnow(),
                    approved_at=datetime.utcnow() if validation_result.decision == "approve" else None,
                    denied_at=datetime.utcnow() if validation_result.decision == "deny" else None,
                    denial_reason=validation_result.reasoning if validation_result.decision == "deny" else None,
                    payout_amount=validation_result.payout_amount,
                    ai_confidence_score=validation_result.confidence_score,
                    ai_reasoning=validation_result.reasoning,
                    fraud_flags=validation_result.fraud_signals
                )
                
                # Save claim to Fabric
                fabric_client.insert_claim(claim)
                logging.info(f'Claim {claim.claim_id} saved to Fabric')
                
                # Publish validation event
                eventgrid_client.publish_claim_validated(
                    claim=claim,
                    validation_result=validation_result.to_dict()
                )
                
                logging.info(f'Policy {policy_id} processing complete')
                
            except Exception as e:
                logging.error(f'Error processing policy {policy_id}: {e}')
                continue
        
        logging.info('Threshold Evaluator completed successfully')
        
    except Exception as e:
        logging.error(f'Fatal error in Threshold Evaluator: {e}')
        raise


# For local testing
if __name__ == "__main__":
    # Mock Event Grid event
    import uuid
    
    class MockEventGridEvent:
        def __init__(self):
            self.id = str(uuid.uuid4())
            self.event_type = "outage.detected"
            self.subject = "outage/OUT-TEST-123"
            self.data = {
                "event_id": "OUT-TEST-123",
                "affected_policies": ["BI-001", "BI-002"]
            }
        
        def get_json(self):
            return self.data
    
    logging.basicConfig(level=logging.INFO)
    main(MockEventGridEvent())
