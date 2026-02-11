"""
Azure Function: Outage Monitor
Runs every 5 minutes to check for new outages and publish events
"""
import azure.functions as func
import logging
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.fabric_client import FabricClient
from shared.eventgrid_client import EventGridClient
from shared.models import OutageEvent, Location, OutageStatus, create_event_id


def main(mytimer: func.TimerRequest) -> None:
    """
    Timer-triggered function that monitors for new outages
    
    Runs every 5 minutes
    """
    timestamp = datetime.utcnow().isoformat()
    
    if mytimer.past_due:
        logging.info('The timer is past due!')
    
    logging.info(f'Outage Monitor function executed at {timestamp}')
    
    try:
        # Initialize clients
        fabric_client = FabricClient()
        eventgrid_client = EventGridClient()
        
        # Get active outages from Fabric
        active_outages = fabric_client.get_active_outages()
        logging.info(f'Found {len(active_outages)} active outages in Fabric')
        
        # Process each outage
        events_published = 0
        
        for outage_data in active_outages:
            try:
                # Check if this outage affects any policies
                affected_policies = fabric_client.get_policies_in_zip(
                    outage_data['zip_code']
                )
                
                if not affected_policies:
                    logging.debug(f"No policies affected by outage {outage_data['event_id']}")
                    continue
                
                # Also check nearby policies (within 10 miles)
                if outage_data.get('latitude') and outage_data.get('longitude'):
                    nearby_policies = fabric_client.get_policies_near_location(
                        latitude=outage_data['latitude'],
                        longitude=outage_data['longitude'],
                        radius_miles=10
                    )
                    
                    # Merge and deduplicate
                    all_policies = {p['policy_id']: p for p in affected_policies + nearby_policies}
                    affected_policies = list(all_policies.values())
                
                logging.info(
                    f"Outage {outage_data['event_id']} affects {len(affected_policies)} policies"
                )
                
                # Create OutageEvent object
                location = Location(
                    latitude=outage_data['latitude'],
                    longitude=outage_data['longitude'],
                    zip_code=outage_data['zip_code'],
                    city=outage_data.get('city'),
                    state=outage_data.get('state')
                )
                
                outage_event = OutageEvent(
                    event_id=outage_data['event_id'],
                    utility_name=outage_data['utility_name'],
                    location=location,
                    affected_customers=outage_data['affected_customers'],
                    outage_start=outage_data['outage_start'],
                    outage_end=outage_data.get('outage_end'),
                    duration_minutes=outage_data.get('duration_minutes'),
                    status=OutageStatus(outage_data['status']),
                    cause=outage_data.get('cause'),
                    reported_cause=outage_data.get('reported_cause'),
                    data_source=outage_data.get('data_source', 'fabric'),
                    last_updated=outage_data.get('last_updated')
                )
                
                # Publish outage detected event
                policy_ids = [p['policy_id'] for p in affected_policies]
                success = eventgrid_client.publish_outage_detected(
                    outage_event=outage_event,
                    affected_policies=policy_ids
                )
                
                if success:
                    events_published += 1
                    logging.info(f"Published event for outage {outage_event.event_id}")
                else:
                    logging.error(f"Failed to publish event for outage {outage_event.event_id}")
                
            except Exception as e:
                logging.error(f"Error processing outage {outage_data.get('event_id')}: {e}")
                continue
        
        logging.info(f"Outage Monitor completed: {events_published} events published")
        
    except Exception as e:
        logging.error(f"Fatal error in Outage Monitor: {e}")
        raise


# For local testing
if __name__ == "__main__":
    # Mock timer request
    class MockTimerRequest:
        past_due = False
    
    logging.basicConfig(level=logging.INFO)
    main(MockTimerRequest())
