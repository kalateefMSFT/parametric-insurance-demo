"""
Azure Event Grid client for publishing events
"""
from azure.eventgrid import EventGridPublisherClient
from azure.core.credentials import AzureKeyCredential
from azure.eventgrid import EventGridEvent
from typing import Dict, Any, List
from datetime import datetime
import uuid

from .config import eventgrid_config
from .models import OutageEvent, Claim, Payout


class EventGridClient:
    """Client for Azure Event Grid operations"""
    
    def __init__(
        self, 
        endpoint: str = None,
        key: str = None
    ):
        """
        Initialize Event Grid client
        
        Args:
            endpoint: Event Grid topic endpoint
            key: Event Grid access key
        """
        self.endpoint = endpoint or eventgrid_config.topic_endpoint
        self.key = key or eventgrid_config.topic_key
        
        credential = AzureKeyCredential(self.key)
        self.client = EventGridPublisherClient(self.endpoint, credential)
    
    def _create_event(
        self,
        event_type: str,
        subject: str,
        data: Dict[str, Any],
        data_version: str = "1.0"
    ) -> EventGridEvent:
        """Create an Event Grid event"""
        return EventGridEvent(
            event_type=event_type,
            subject=subject,
            data=data,
            data_version=data_version,
            event_time=datetime.utcnow(),
            id=str(uuid.uuid4())
        )
    
    def publish_event(
        self,
        event_type: str,
        subject: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Publish a single event to Event Grid
        
        Args:
            event_type: Type of event (e.g., "outage.detected")
            subject: Subject of the event (e.g., "policy/123")
            data: Event data payload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            event = self._create_event(event_type, subject, data)
            self.client.send([event])
            return True
        except Exception as e:
            print(f"Error publishing event: {e}")
            return False
    
    def publish_events(self, events: List[EventGridEvent]) -> bool:
        """
        Publish multiple events to Event Grid
        
        Args:
            events: List of EventGridEvent objects
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.send(events)
            return True
        except Exception as e:
            print(f"Error publishing events: {e}")
            return False
    
    # Outage-specific event publishers
    
    def publish_outage_detected(
        self,
        outage_event: OutageEvent,
        affected_policies: List[str]
    ) -> bool:
        """
        Publish outage detected event
        
        Args:
            outage_event: OutageEvent object
            affected_policies: List of policy IDs in affected area
        """
        return self.publish_event(
            event_type=eventgrid_config.OUTAGE_DETECTED,
            subject=f"outage/{outage_event.event_id}",
            data={
                "event_id": outage_event.event_id,
                "utility_name": outage_event.utility_name,
                "location": outage_event.location.to_dict(),
                "affected_customers": outage_event.affected_customers,
                "outage_start": outage_event.outage_start.isoformat(),
                "status": outage_event.status.value,
                "cause": outage_event.cause,
                "affected_policies": affected_policies,
                "policy_count": len(affected_policies)
            }
        )
    
    def publish_threshold_exceeded(
        self,
        policy_id: str,
        outage_event: OutageEvent,
        duration_minutes: int,
        threshold_minutes: int
    ) -> bool:
        """
        Publish threshold exceeded event
        
        Args:
            policy_id: Policy ID
            outage_event: OutageEvent object
            duration_minutes: Current outage duration
            threshold_minutes: Policy threshold
        """
        return self.publish_event(
            event_type=eventgrid_config.OUTAGE_THRESHOLD_EXCEEDED,
            subject=f"policy/{policy_id}",
            data={
                "policy_id": policy_id,
                "event_id": outage_event.event_id,
                "duration_minutes": duration_minutes,
                "threshold_minutes": threshold_minutes,
                "minutes_over_threshold": duration_minutes - threshold_minutes,
                "location": outage_event.location.to_dict(),
                "utility_name": outage_event.utility_name,
                "affected_customers": outage_event.affected_customers
            }
        )
    
    def publish_claim_validated(
        self,
        claim: Claim,
        validation_result: Dict[str, Any]
    ) -> bool:
        """
        Publish claim validated event
        
        Args:
            claim: Claim object
            validation_result: AI validation result
        """
        event_type = (
            eventgrid_config.CLAIM_APPROVED 
            if claim.status.value == "approved" 
            else eventgrid_config.CLAIM_DENIED
        )
        
        return self.publish_event(
            event_type=event_type,
            subject=f"claim/{claim.claim_id}",
            data={
                "claim_id": claim.claim_id,
                "policy_id": claim.policy_id,
                "outage_event_id": claim.outage_event_id,
                "status": claim.status.value,
                "payout_amount": claim.payout_amount,
                "ai_confidence_score": claim.ai_confidence_score,
                "ai_reasoning": claim.ai_reasoning,
                "fraud_flags": claim.fraud_flags,
                "validation_result": validation_result
            }
        )
    
    def publish_outage_resolved(
        self,
        outage_event: OutageEvent,
        affected_claims: List[str]
    ) -> bool:
        """
        Publish outage resolved event
        
        Args:
            outage_event: OutageEvent object
            affected_claims: List of claim IDs affected by this outage
        """
        return self.publish_event(
            event_type=eventgrid_config.OUTAGE_RESOLVED,
            subject=f"outage/{outage_event.event_id}",
            data={
                "event_id": outage_event.event_id,
                "utility_name": outage_event.utility_name,
                "location": outage_event.location.to_dict(),
                "outage_start": outage_event.outage_start.isoformat(),
                "outage_end": outage_event.outage_end.isoformat() if outage_event.outage_end else None,
                "duration_minutes": outage_event.duration_minutes,
                "affected_claims": affected_claims,
                "claim_count": len(affected_claims)
            }
        )
    
    def publish_payout_processed(
        self,
        payout: Payout,
        claim: Claim
    ) -> bool:
        """
        Publish payout processed event
        
        Args:
            payout: Payout object
            claim: Related Claim object
        """
        return self.publish_event(
            event_type=eventgrid_config.PAYOUT_PROCESSED,
            subject=f"payout/{payout.payout_id}",
            data={
                "payout_id": payout.payout_id,
                "claim_id": payout.claim_id,
                "policy_id": payout.policy_id,
                "amount": payout.amount,
                "status": payout.status.value,
                "initiated_at": payout.initiated_at.isoformat(),
                "completed_at": payout.completed_at.isoformat() if payout.completed_at else None,
                "payment_method": payout.payment_method,
                "transaction_id": payout.transaction_id
            }
        )
    
    # Batch event publishing
    
    def publish_batch_threshold_exceeded(
        self,
        events_data: List[Dict[str, Any]]
    ) -> bool:
        """
        Publish multiple threshold exceeded events in batch
        
        Args:
            events_data: List of event data dictionaries
        """
        events = [
            self._create_event(
                event_type=eventgrid_config.OUTAGE_THRESHOLD_EXCEEDED,
                subject=f"policy/{data['policy_id']}",
                data=data
            )
            for data in events_data
        ]
        
        return self.publish_events(events)


# Convenience function for testing
def test_event_grid_connection(endpoint: str = None, key: str = None) -> bool:
    """
    Test Event Grid connection
    
    Args:
        endpoint: Event Grid topic endpoint
        key: Event Grid access key
        
    Returns:
        True if connection successful
    """
    try:
        client = EventGridClient(endpoint, key)
        
        # Send test event
        test_data = {
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connection test"
        }
        
        return client.publish_event(
            event_type="test.connection",
            subject="test/connection",
            data=test_data
        )
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
