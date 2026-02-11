"""
Azure Function: Outage Resolution Monitor
Timer-triggered function that checks if active outages have been resolved
"""
import azure.functions as func
import logging
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.fabric_client import FabricClient
from shared.eventgrid_client import EventGridClient


def main(mytimer: func.TimerRequest) -> None:
    """
    Timer-triggered function that monitors for outage resolutions
    Runs every 10 minutes
    """
    timestamp = datetime.utcnow().isoformat()
    
    if mytimer.past_due:
        logging.info('The timer is past due!')
    
    logging.info(f'Outage Resolution Monitor executed at {timestamp}')
    
    try:
        fabric_client = FabricClient()
        eventgrid_client = EventGridClient()
        
        # Get active outages
        active_outages = fabric_client.get_active_outages()
        logging.info(f'Monitoring {len(active_outages)} active outages')
        
        resolutions_found = 0
        
        for outage in active_outages:
            # Check if outage is still active in source
            # In production, would query PowerOutage.us API
            # For demo, check if duration suggests resolution
            
            if outage.get('duration_minutes') and outage['duration_minutes'] > 480:
                # Outage longer than 8 hours - likely resolved
                logging.info(f"Marking outage {outage['event_id']} as resolved")
                
                # Update status
                fabric_client.update_outage_event(
                    event_id=outage['event_id'],
                    status='resolved',
                    outage_end=datetime.utcnow()
                )
                
                # Get affected claims
                # Query claims for this outage
                # Publish resolution event
                
                resolutions_found += 1
        
        logging.info(f'Found {resolutions_found} resolved outages')
        
    except Exception as e:
        logging.error(f'Error in Outage Resolution Monitor: {e}')
        raise
