#!/usr/bin/env python3
"""
TDengine Connection Diagnostic Tests

Unit tests for TDengine connection and query operations.
Run with: python -m unittest tests.diagnose_tdengine
"""

import unittest
import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TDengineConnectionTests(unittest.TestCase):
    """Test suite for TDengine connection and basic operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration - runs once before all tests."""
        cls.host = "35.90.244.93"
        cls.port = 6041
        cls.user = "root"
        cls.password = "taosdata"
        cls.database = "thermal_sensors_pilot"
        cls.base_url = f"http://{cls.host}:{cls.port}/rest/sql"
        
        logger.info("\n" + "=" * 70)
        logger.info("TDengine Connection Test Suite")
        logger.info("=" * 70)
        logger.info(f"Host: {cls.host}:{cls.port}")
        logger.info(f"Database: {cls.database}")
        logger.info("=" * 70 + "\n")
    
    def test_01_server_reachability(self):
        """Test if TDengine REST API server is reachable."""
        logger.info("\nTEST: Server Reachability")
        logger.info("-" * 50)
        
        try:
            response = requests.get(self.base_url, timeout=5)
            logger.info(f"Server response: {response.status_code}")
            
            # 200, 401, 405 are all acceptable (server is responding)
            # 404 means server is up but endpoint behaves differently
            self.assertIn(
                response.status_code,
                [200, 401, 404, 405],
                "Server should be reachable"
            )
            logger.info("✅ Server is reachable")
            
        except requests.exceptions.Timeout:
            self.fail("Connection timeout - server may be down")
        except requests.exceptions.ConnectionError:
            self.fail("Connection refused - server may be down or unreachable")
    
    def test_02_basic_connection(self):
        """Test basic connection with authentication."""
        logger.info("\nTEST: Basic Connection")
        logger.info("-" * 50)
        
        response = requests.post(
            self.base_url,
            auth=(self.user, self.password),
            data="SHOW DATABASES;",
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200, "HTTP request should succeed")
        
        result = response.json()
        logger.info(f"Response code: {result.get('code')}")
        
        self.assertEqual(result.get('code'), 0, "TDengine query should succeed")
        self.assertIn('column_meta', result, "Response should contain column metadata")
        
        logger.info(f"✅ Connection successful - found {result.get('rows', 0)} databases")
    
    def test_03_database_access(self):
        """Test access to specific database."""
        logger.info("\nTEST: Database Access")
        logger.info("-" * 50)
        logger.info(f"Database: {self.database}")
        
        sql = f"USE {self.database};"
        response = requests.post(
            self.base_url,
            auth=(self.user, self.password),
            data=sql,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200, "HTTP request should succeed")
        
        result = response.json()
        self.assertEqual(
            result.get('code'), 0,
            f"Database '{self.database}' should be accessible"
        )
        
        logger.info(f"✅ Database '{self.database}' is accessible")
    
    def test_04_table_access(self):
        """Test access to sensor_frames table and count records."""
        logger.info("\nTEST: Table Access")
        logger.info("-" * 50)
        logger.info(f"Table: {self.database}.sensor_frames")
        
        sql = f"SELECT COUNT(*) FROM {self.database}.sensor_frames;"
        response = requests.post(
            self.base_url,
            auth=(self.user, self.password),
            data=sql,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200, "HTTP request should succeed")
        
        result = response.json()
        
        if result.get('code') != 0:
            error_msg = result.get('desc', result.get('msg', 'Unknown error'))
            if "disk space" in error_msg.lower():
                self.fail(f"Disk space issue on TDengine server: {error_msg}")
            else:
                self.fail(f"Table query failed: {error_msg}")
        
        self.assertEqual(result.get('code'), 0, "Table query should succeed")
        self.assertIn('data', result, "Response should contain data")
        
        count = result['data'][0][0] if result.get('data') else 0
        self.assertGreater(count, 0, "Table should contain records")
        
        logger.info(f"✅ Table accessible - Total records: {count:,}")
    
    def test_05_sample_data_query(self):
        """Test querying sample data from the table."""
        logger.info("\nTEST: Sample Data Query")
        logger.info("-" * 50)
        
        sql = f"SELECT ts, sensor_mac FROM {self.database}.sensor_frames LIMIT 1;"
        response = requests.post(
            self.base_url,
            auth=(self.user, self.password),
            data=sql,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200, "HTTP request should succeed")
        
        result = response.json()
        self.assertEqual(result.get('code'), 0, "Sample query should succeed")
        self.assertIn('data', result, "Response should contain data")
        self.assertTrue(result.get('data'), "Query should return at least one record")
        
        sample_record = result['data'][0]
        logger.info(f"✅ Sample query successful")
        logger.info(f"   Sample record: {sample_record}")
        
        # Verify data structure
        self.assertEqual(len(sample_record), 2, "Record should have 2 fields (ts, sensor_mac)")


class TDengineDataFetchTests(unittest.TestCase):
    """Test suite for fetching and decompressing thermal data."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        cls.host = "35.90.244.93"
        cls.port = 6041
        cls.user = "root"
        cls.password = "taosdata"
        cls.database = "thermal_sensors_pilot"
        cls.base_url = f"http://{cls.host}:{cls.port}/rest/sql"
        cls.test_mac = "02:00:1a:62:51:67"
        
        logger.info("\n" + "=" * 70)
        logger.info("TDengine Data Fetch Test Suite")
        logger.info("=" * 70 + "\n")
    
    def test_01_query_by_mac_address(self):
        """Test querying data by specific MAC address."""
        logger.info("\nTEST: Query by MAC Address")
        logger.info("-" * 50)
        logger.info(f"MAC: {self.test_mac}")
        
        sql = f"SELECT COUNT(*) FROM {self.database}.sensor_frames WHERE sensor_mac = '{self.test_mac}';"
        response = requests.post(
            self.base_url,
            auth=(self.user, self.password),
            data=sql,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200, "HTTP request should succeed")
        
        result = response.json()
        self.assertEqual(result.get('code'), 0, "MAC query should succeed")
        
        count = result['data'][0][0] if result.get('data') else 0
        logger.info(f"✅ Found {count:,} records for MAC {self.test_mac}")
        
        # We expect data for this MAC, but don't fail if missing (test environment)
        if count == 0:
            logger.warning(f"⚠️ No data found for MAC {self.test_mac}")
    
    def test_02_query_frame_data_structure(self):
        """Test that frame data has expected structure."""
        logger.info("\nTEST: Frame Data Structure")
        logger.info("-" * 50)
        
        sql = f"SELECT ts, sensor_mac, width, height, frame_data FROM {self.database}.sensor_frames LIMIT 1;"
        response = requests.post(
            self.base_url,
            auth=(self.user, self.password),
            data=sql,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200, "HTTP request should succeed")
        
        result = response.json()
        self.assertEqual(result.get('code'), 0, "Query should succeed")
        
        if result.get('data'):
            record = result['data'][0]
            logger.info(f"✅ Frame data structure valid")
            logger.info(f"   Fields: ts, sensor_mac, width, height, frame_data")
            logger.info(f"   Width: {record[2]}, Height: {record[3]}")
            
            # Verify expected dimensions
            self.assertIn(record[2], [60, 64], "Width should be 60 or 64")
            self.assertIn(record[3], [40, 48], "Height should be 40 or 48")
        else:
            logger.warning("⚠️ No data returned - cannot verify structure")


def run_diagnostic_suite():
    """Run the diagnostic test suite and print summary."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TDengineConnectionTests))
    suite.addTests(loader.loadTestsFromTestCase(TDengineDataFetchTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("Test Summary")
    logger.info("=" * 70)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info("=" * 70 + "\n")
    
    if result.wasSuccessful():
        logger.info("✅ All tests passed! TDengine is working correctly.\n")
    else:
        logger.warning("⚠️ Some tests failed. Check the output above for details.\n")
    
    return result


if __name__ == '__main__':
    # Run with custom summary
    run_diagnostic_suite()

