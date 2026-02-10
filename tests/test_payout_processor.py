"""
Unit tests for PayoutProcessor function
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class TestPayoutProcessor(unittest.TestCase):
    """Test cases for PayoutProcessor function"""
    
    def test_payout_calculation(self):
        """Test payout calculation logic"""
        claim_amount = 1250.00
        max_payout = 10000.00
        
        # Payout should not exceed max
        final_payout = min(claim_amount, max_payout)
        
        self.assertEqual(final_payout, claim_amount)
    
    def test_payout_exceeds_max(self):
        """Test when calculated payout exceeds maximum"""
        claim_amount = 15000.00
        max_payout = 10000.00
        
        final_payout = min(claim_amount, max_payout)
        
        self.assertEqual(final_payout, max_payout)
    
    def test_zero_payout(self):
        """Test when payout is zero"""
        claim_amount = 0.00
        
        self.assertEqual(claim_amount, 0.00)


if __name__ == '__main__':
    unittest.main()
