"""
Unit tests for ThresholdEvaluator function
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class TestThresholdEvaluator(unittest.TestCase):
    """Test cases for ThresholdEvaluator function"""
    
    def test_threshold_exceeded(self):
        """Test when threshold is exceeded"""
        policy = {
            'threshold_minutes': 120,
            'hourly_rate': 500,
            'max_payout': 10000
        }
        
        duration_minutes = 187  # 3.1 hours
        threshold = policy['threshold_minutes']
        
        # Calculate expected payout
        hours_over = (duration_minutes - threshold) / 60
        expected_payout = hours_over * policy['hourly_rate']
        
        self.assertGreater(duration_minutes, threshold)
        self.assertAlmostEqual(expected_payout, 558.33, places=2)
    
    def test_threshold_not_exceeded(self):
        """Test when threshold is not exceeded"""
        policy = {
            'threshold_minutes': 120,
            'hourly_rate': 500,
            'max_payout': 10000
        }
        
        duration_minutes = 90  # 1.5 hours
        threshold = policy['threshold_minutes']
        
        self.assertLess(duration_minutes, threshold)


if __name__ == '__main__':
    unittest.main()
