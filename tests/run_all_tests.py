#!/usr/bin/env python3
"""
Run All Unit Tests

This script runs all unit tests for the DataAnnotationQA project.

Usage:
    python tests/run_all_tests.py
    python -m unittest tests.run_all_tests
"""

import unittest
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_all_tests():
    """Discover and run all tests in the unittest directory."""
    logger.info("\n" + "=" * 70)
    logger.info("Running All Unit Tests")
    logger.info("=" * 70 + "\n")
    
    # Discover all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Also load diagnose_tdengine tests
    try:
        from tests import diagnose_tdengine
        suite.addTests(loader.loadTestsFromModule(diagnose_tdengine))
    except ImportError as e:
        logger.warning(f"Could not load diagnose_tdengine tests: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("Overall Test Summary")
    logger.info("=" * 70)
    logger.info(f"Total tests run: {result.testsRun}")
    logger.info(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info("=" * 70 + "\n")
    
    if result.wasSuccessful():
        logger.info("✅ All tests passed!\n")
        return 0
    else:
        logger.error("❌ Some tests failed. See details above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())

