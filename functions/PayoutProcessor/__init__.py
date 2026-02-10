"""
Azure Function: Payout Processor
Event Grid triggered function that processes approved claims
and initiates payouts
"""
import azure.functions as func
import logging
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.fabric_client import FabricClient
from shared.eventgrid_client import EventGridClient
from shared.models import Payout, PayoutStatus, create_payout_id, Claim, ClaimStatus


def process_payment(payout: Payout, policy: dict) -> tuple[bool, str]:
    """
    Process actual payment (integration with payment system)
    
    In production, this would integrate with:
    - ACH processing system
    - Banking APIs
    - Payment gateways
    
    Args:
        payout: Payout object
        policy: Policy data with payment details
        
    Returns:
        Tuple of (success: bool, transaction_id: str)
    """
    try:
        # SIMULATION: In production, call actual payment API
        # For demo purposes, we'll simulate success
        
        logging.info(f'Processing payment of ${payout.amount:.2f} for policy {payout.policy_id}')
        logging.info(f'Payment method: {payout.payment_method}')
        
        # Simulate payment processing delay
        import time
        time.sleep(1)
        
        # Generate mock transaction ID
        transaction_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{payout.claim_id[-4:]}"
        
        logging.info(f'Payment processed successfully: {transaction_id}')
        
        return True, transaction_id
        
    except Exception as e:
        logging.error(f'Payment processing error: {e}')
        return False, None


def send_notification(payout: Payout, policy: dict, claim: dict) -> bool:
    """
    Send notification to policyholder
    
    In production, this would send:
    - Email notification
    - SMS notification
    - Push notification (mobile app)
    
    Args:
        payout: Payout object
        policy: Policy data
        claim: Claim data
        
    Returns:
        True if notification sent successfully
    """
    try:
        # SIMULATION: In production, use SendGrid, Twilio, etc.
        
        notification_message = f"""
        Parametric Insurance Claim Approved
        
        Dear {policy['business_name']},
        
        Your claim has been automatically processed and approved.
        
        Claim Details:
        - Claim ID: {claim['claim_id']}
        - Policy ID: {policy['policy_id']}
        - Payout Amount: ${payout.amount:.2f}
        - Transaction ID: {payout.transaction_id}
        
        The funds will be deposited to your account within 1-2 business days.
        
        This claim was validated using AI-powered analysis of:
        - Power outage duration and severity
        - Weather conditions
        - Historical claim patterns
        
        AI Confidence Score: {claim.get('ai_confidence_score', 0) * 100:.0f}%
        
        Thank you for choosing our parametric insurance service.
        """
        
        logging.info(f'Notification to be sent to: {policy.get("contact_email")}')
        logging.info(f'Notification content:\n{notification_message}')
        
        # In production: Send actual email/SMS
        # email_service.send(to=policy['contact_email'], message=notification_message)
        # sms_service.send(to=policy['contact_phone'], message=notification_message)
        
        return True
        
    except Exception as e:
        logging.error(f'Notification error: {e}')
        return False


def main(event: func.EventGridEvent):
    """
    Event Grid triggered function for payout processing
    
    Triggered by: claim.approved events
    """
    logging.info(f'Payout Processor triggered by event: {event.id}')
    
    try:
        # Parse event data
        event_data = event.get_json()
        logging.info(f'Event type: {event.event_type}')
        logging.info(f'Event subject: {event.subject}')
        
        # Get claim details
        claim_id = event_data.get('claim_id')
        policy_id = event_data.get('policy_id')
        payout_amount = event_data.get('payout_amount')
        
        if not all([claim_id, policy_id, payout_amount]):
            logging.error('Missing required fields in event data')
            return
        
        if payout_amount <= 0:
            logging.info(f'Zero payout amount for claim {claim_id} - no payment needed')
            return
        
        logging.info(f'Processing payout for claim {claim_id}: ${payout_amount:.2f}')
        
        # Initialize clients
        fabric_client = FabricClient()
        eventgrid_client = EventGridClient()
        
        # Get claim details from Fabric
        claim_data = fabric_client.get_claim(claim_id)
        
        if not claim_data:
            logging.error(f'Claim {claim_id} not found in Fabric')
            return
        
        # Get policy details
        policy_data = fabric_client.get_policy(policy_id)
        
        if not policy_data:
            logging.error(f'Policy {policy_id} not found in Fabric')
            return
        
        # Create payout record
        payout = Payout(
            payout_id=create_payout_id(claim_id),
            claim_id=claim_id,
            policy_id=policy_id,
            amount=payout_amount,
            status=PayoutStatus.PROCESSING,
            initiated_at=datetime.utcnow(),
            payment_method="ACH"  # Default to ACH
        )
        
        # Save initial payout record
        fabric_client.insert_payout(payout)
        logging.info(f'Payout record {payout.payout_id} created in Fabric')
        
        # Process payment
        success, transaction_id = process_payment(payout, policy_data)
        
        if success:
            # Update payout record
            fabric_client.update_payout(
                payout_id=payout.payout_id,
                status=PayoutStatus.COMPLETED.value,
                completed_at=datetime.utcnow(),
                transaction_id=transaction_id
            )
            
            payout.status = PayoutStatus.COMPLETED
            payout.completed_at = datetime.utcnow()
            payout.transaction_id = transaction_id
            
            logging.info(f'Payout {payout.payout_id} completed successfully')
            
            # Update claim status
            fabric_client.update_claim(
                claim_id=claim_id,
                status=ClaimStatus.PAID.value
            )
            
            # Send notification
            notification_sent = send_notification(payout, policy_data, claim_data)
            
            if notification_sent:
                logging.info('Notification sent successfully')
            else:
                logging.warning('Failed to send notification')
            
            # Publish payout processed event
            claim = Claim(
                claim_id=claim_data['claim_id'],
                policy_id=claim_data['policy_id'],
                outage_event_id=claim_data['outage_event_id'],
                status=ClaimStatus.PAID,
                filed_at=claim_data['filed_at']
            )
            
            eventgrid_client.publish_payout_processed(
                payout=payout,
                claim=claim
            )
            
            logging.info('Payout processing completed successfully')
            
        else:
            # Payment failed
            fabric_client.update_payout(
                payout_id=payout.payout_id,
                status=PayoutStatus.FAILED.value
            )
            
            logging.error(f'Payment processing failed for payout {payout.payout_id}')
            
            # In production: Trigger retry logic or manual review
        
    except Exception as e:
        logging.error(f'Fatal error in Payout Processor: {e}')
        raise


# For local testing
if __name__ == "__main__":
    import uuid
    
    class MockEventGridEvent:
        def __init__(self):
            self.id = str(uuid.uuid4())
            self.event_type = "claim.approved"
            self.subject = "claim/CLM-TEST-123"
            self.data = {
                "claim_id": "CLM-BI-001-20260209120000",
                "policy_id": "BI-001",
                "payout_amount": 1250.00,
                "ai_confidence_score": 0.94
            }
        
        def get_json(self):
            return self.data
    
    logging.basicConfig(level=logging.INFO)
    main(MockEventGridEvent())
