"""
Unit tests for OutageMonitor function
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from functions.OutageMonitor import main as outage_monitor


class TestOutageMonitor(unittest.TestCase):
    """Test cases for OutageMonitor function"""
    
    @patch('functions.OutageMonitor.FabricClient')
    @patch('functions.OutageMonitor.EventGridClient')
    def test_outage_monitor_success(self, mock_eventgrid, mock_fabric):
        """Test successful outage monitoring"""
        # Mock timer request
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Mock fabric client
        mock_fabric_instance = mock_fabric.return_value
        mock_fabric_instance.get_active_outages.return_value = [
            {
                'event_id': 'TEST-001',
                'utility_name': 'Test Utility',
                'zip_code': '98101',
                'latitude': 47.6062,
                'longitude': -122.3321,
                'affected_customers': 5000,
                'outage_start': datetime.utcnow(),
                'duration_minutes': 150,
                'status': 'active'
            }
        ]
        mock_fabric_instance.get_policies_in_zip.return_value = [
            {'policy_id': 'BI-001', 'business_name': 'Test Business'}
        ]
        
        # Mock eventgrid client
        mock_eventgrid_instance = mock_eventgrid.return_value
        mock_eventgrid_instance.publish_outage_detected.return_value = True
        
        # Execute function
        try:
            outage_monitor(mock_timer)
            success = True
        except Exception as e:
            success = False
            print(f"Error: {e}")
        
        # Assertions
        self.assertTrue(success)
        mock_fabric_instance.get_active_outages.assert_called_once()
        mock_eventgrid_instance.publish_outage_detected.assert_called()
    
    @patch('functions.OutageMonitor.FabricClient')
    def test_no_active_outages(self, mock_fabric):
        """Test when there are no active outages"""
        mock_timer = Mock()
        mock_timer.past_due = False
        
        mock_fabric_instance = mock_fabric.return_value
        mock_fabric_instance.get_active_outages.return_value = []
        
        try:
            outage_monitor(mock_timer)
            success = True
        except Exception as e:
            success = False
        
        self.assertTrue(success)


if __name__ == '__main__':
    unittest.main()
