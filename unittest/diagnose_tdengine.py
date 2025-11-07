#!/usr/bin/env python3
"""
TDengine Connection Diagnostic Tool

This script helps diagnose TDengine connection and query issues.
"""

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

# Connection settings
DEFAULT_HOST = "35.90.244.93"
DEFAULT_PORT = 6041
DEFAULT_USER = "root"
DEFAULT_PASSWORD = "taosdata"
DEFAULT_DATABASE = "thermal_sensors_pilot"


def test_connection(host: str, port: int, user: str, password: str) -> bool:
    """Test basic connection to TDengine server."""
    logger.info("=" * 60)
    logger.info("TEST 1: Basic Connection")
    logger.info("=" * 60)
    logger.info(f"Host: {host}:{port}")
    logger.info(f"User: {user}")
    
    try:
        url = f"http://{host}:{port}/rest/sql"
        response = requests.post(
            url,
            auth=(user, password),
            data="SHOW DATABASES;",
            timeout=10
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Response Code: {result.get('code')}")
            
            if result.get('code') == 0:
                logger.info("✅ Connection successful!")
                logger.info(f"Columns: {result.get('column_meta', [])}")
                logger.info(f"Row count: {result.get('rows', 0)}")
                return True
            else:
                logger.error(f"❌ Query failed: {result.get('desc', result.get('msg'))}")
                return False
        else:
            logger.error(f"❌ HTTP error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False


def test_database_access(host: str, port: int, user: str, password: str, database: str) -> bool:
    """Test access to specific database."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Database Access")
    logger.info("=" * 60)
    logger.info(f"Database: {database}")
    
    try:
        url = f"http://{host}:{port}/rest/sql"
        sql = f"USE {database};"
        
        response = requests.post(
            url,
            auth=(user, password),
            data=sql,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"✅ Database '{database}' accessible")
                return True
            else:
                logger.error(f"❌ Database access failed: {result.get('desc', result.get('msg'))}")
                return False
        else:
            logger.error(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False


def test_table_access(host: str, port: int, user: str, password: str, database: str) -> bool:
    """Test access to sensor_frames table."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Table Access")
    logger.info("=" * 60)
    logger.info(f"Table: {database}.sensor_frames")
    
    try:
        url = f"http://{host}:{port}/rest/sql"
        sql = f"SELECT COUNT(*) FROM {database}.sensor_frames;"
        
        response = requests.post(
            url,
            auth=(user, password),
            data=sql,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('code') == 0:
                count = result['data'][0][0] if result.get('data') else 0
                logger.info(f"✅ Table accessible")
                logger.info(f"Total records: {count:,}")
                return True
            else:
                error_msg = result.get('desc', result.get('msg', 'Unknown error'))
                logger.error(f"❌ Table query failed: {error_msg}")
                
                # Check if it's a disk space issue
                if "disk space" in error_msg.lower():
                    logger.error("\n" + "!" * 60)
                    logger.error("DISK SPACE ISSUE DETECTED ON TDENGINE SERVER")
                    logger.error("!" * 60)
                    logger.error("\nPossible solutions:")
                    logger.error("1. Contact server administrator to free up disk space")
                    logger.error("2. Check TDengine server disk usage")
                    logger.error("3. Clean up old data or logs on the server")
                    logger.error("4. Increase disk quota or storage capacity")
                
                return False
        else:
            logger.error(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Table test failed: {e}")
        return False


def test_sample_query(host: str, port: int, user: str, password: str, database: str) -> bool:
    """Test a simple sample query."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Sample Data Query")
    logger.info("=" * 60)
    
    try:
        url = f"http://{host}:{port}/rest/sql"
        sql = f"SELECT ts, sensor_mac FROM {database}.sensor_frames LIMIT 1;"
        
        response = requests.post(
            url,
            auth=(user, password),
            data=sql,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('code') == 0:
                if result.get('data'):
                    logger.info(f"✅ Sample query successful")
                    logger.info(f"Sample record: {result['data'][0]}")
                else:
                    logger.warning("⚠️ Query successful but no data returned")
                return True
            else:
                logger.error(f"❌ Sample query failed: {result.get('desc', result.get('msg'))}")
                return False
        else:
            logger.error(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Sample query test failed: {e}")
        return False


def check_server_status(host: str, port: int) -> bool:
    """Check if TDengine REST API is responding."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 0: Server Reachability")
    logger.info("=" * 60)
    logger.info(f"Checking: http://{host}:{port}")
    
    try:
        url = f"http://{host}:{port}/rest/sql"
        response = requests.get(url, timeout=5)
        
        logger.info(f"Server response: {response.status_code}")
        
        if response.status_code in [200, 401, 405]:  # These are expected
            logger.info("✅ Server is reachable")
            return True
        else:
            logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ Connection timeout - server may be down")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection refused - server may be down or unreachable")
        return False
    except Exception as e:
        logger.error(f"❌ Server check failed: {e}")
        return False


def main():
    """Run diagnostic tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " TDengine Connection Diagnostic Tool".center(58) + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("\n")
    
    logger.info("Configuration:")
    logger.info(f"  Host: {DEFAULT_HOST}")
    logger.info(f"  Port: {DEFAULT_PORT}")
    logger.info(f"  Database: {DEFAULT_DATABASE}")
    logger.info(f"  User: {DEFAULT_USER}")
    logger.info("\n")
    
    # Run tests
    tests_passed = 0
    tests_total = 5
    
    if check_server_status(DEFAULT_HOST, DEFAULT_PORT):
        tests_passed += 1
    
    if test_connection(DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USER, DEFAULT_PASSWORD):
        tests_passed += 1
    else:
        logger.error("\n⚠️ Basic connection failed. Check credentials and server status.")
        logger.info("\nSkipping remaining tests...")
        print_summary(tests_passed, tests_total)
        return
    
    if test_database_access(DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USER, DEFAULT_PASSWORD, DEFAULT_DATABASE):
        tests_passed += 1
    else:
        logger.error("\n⚠️ Database access failed. Check database name and permissions.")
        logger.info("\nSkipping remaining tests...")
        print_summary(tests_passed, tests_total)
        return
    
    if test_table_access(DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USER, DEFAULT_PASSWORD, DEFAULT_DATABASE):
        tests_passed += 1
    
    if test_sample_query(DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USER, DEFAULT_PASSWORD, DEFAULT_DATABASE):
        tests_passed += 1
    
    # Print summary
    print_summary(tests_passed, tests_total)


def print_summary(passed: int, total: int):
    """Print diagnostic summary."""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " Diagnostic Summary".center(58) + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("\n✅ All tests passed! TDengine is working correctly.")
        logger.info("\nYou can now use the export tool:")
        logger.info("  ./export_from_tdengine.sh 02:00:1a:62:51:67 '2025-10-13 00:35:00' '2025-10-13 01:20:00' LA")
    elif passed >= 2:
        logger.warning(f"\n⚠️ Some tests failed ({total - passed}/{total})")
        logger.warning("TDengine connection works but there may be issues with data access.")
        logger.warning("\nCheck the error messages above for details.")
    else:
        logger.error(f"\n❌ Connection failed ({passed}/{total} tests passed)")
        logger.error("\nPossible issues:")
        logger.error("1. TDengine server may be down")
        logger.error("2. Network connectivity issues")
        logger.error("3. Incorrect credentials")
        logger.error("4. Firewall blocking access")
        logger.error("\nContact your system administrator for help.")
    
    logger.info("\n")


if __name__ == '__main__':
    main()

