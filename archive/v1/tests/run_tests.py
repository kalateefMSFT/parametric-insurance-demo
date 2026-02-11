#!/usr/bin/env python3
"""
Run all tests for Parametric Insurance Demo
"""
import sys
import unittest

def run_all_tests():
    """Discover and run all tests"""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
