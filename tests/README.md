# Unit Tests

This directory contains unit tests for the DataAnnotationQA project using Python's `unittest` framework.

## Test Modules

### 1. `test_diagnose_tdengine.py`
Tests for TDengine database connection and data access.

**Test Classes:**
- `TDengineConnectionTests` - Basic connection, authentication, database/table access (5 tests)
- `TDengineDataFetchTests` - Data querying and structure validation (2 tests)

**Total:** 7 tests

### 2. `test_training_pipeline.py`
Tests for PyTorch ThermalAnnotationDataset and DataLoader integration.

**Test Classes:**
- `ThermalDatasetBasicTests` - Dataset initialization, sample fetching, category mapping (4 tests)
- `ThermalDatasetCacheTests` - Frame prefetching and caching (2 tests)
- `PyTorchDataLoaderTests` - DataLoader creation, batch iteration, collation (3 tests)
- `ThermalDataTransformTests` - Custom transforms (1 test)

**Total:** 10 tests

## Running Tests

### Run All Tests
```bash
# Using the test runner script
python tests/run_all_tests.py

# Using unittest discover
python -m unittest discover tests

# Or from project root
cd /path/to/DataAnnotationQA
python -m unittest discover tests
```

### Run Specific Test Module
```bash
# TDengine diagnostics
python tests/test_diagnose_tdengine.py
# Or
python -m unittest tests.test_diagnose_tdengine

# Training pipeline tests
python tests/test_training_pipeline.py
# Or
python -m unittest tests.test_training_pipeline
```

### Run Specific Test Class
```bash
python -m unittest tests.test_diagnose_tdengine.TDengineConnectionTests
python -m unittest tests.test_training_pipeline.PyTorchDataLoaderTests
```

### Run Specific Test Method
```bash
python -m unittest tests.test_diagnose_tdengine.TDengineConnectionTests.test_01_server_reachability
python -m unittest tests.test_training_pipeline.PyTorchDataLoaderTests.test_01_create_dataloader
```

### Run with Verbose Output
```bash
python -m unittest discover tests -v
```

## Test Structure

All tests follow the standard `unittest` framework pattern:

```python
import unittest

class MyTestClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run once before all tests in the class"""
        pass
    
    def setUp(self):
        """Run before each test method"""
        pass
    
    def test_01_something(self):
        """Test method - must start with 'test_'"""
        self.assertEqual(actual, expected)
        self.assertTrue(condition)
        self.assertIsNotNone(value)
    
    def tearDown(self):
        """Run after each test method"""
        pass
    
    @classmethod
    def tearDownClass(cls):
        """Run once after all tests in the class"""
        pass
```

## Requirements

Tests require the following dependencies:
- `unittest` (Python standard library)
- `requests` - For TDengine REST API access
- `torch` - For PyTorch functionality
- `numpy` - For numerical operations
- Project modules: `src.data_pipeline`

Install with:
```bash
uv pip install requests torch numpy
```

## Continuous Integration

These tests are designed to be run in CI/CD pipelines:

```bash
# Exit with code 0 if all tests pass, non-zero otherwise
python tests/run_all_tests.py
```

## Test Coverage

Current test coverage includes:
- ✅ TDengine connection and authentication
- ✅ Database and table access
- ✅ Data querying by MAC address
- ✅ Dataset initialization and loading
- ✅ Single sample and batch fetching
- ✅ Category ID mapping
- ✅ Frame caching and prefetching
- ✅ PyTorch DataLoader integration
- ✅ Batch collation
- ✅ Custom transforms

## Troubleshooting

### Network Tests Failing
If TDengine connection tests fail, verify:
- TDengine server is accessible at `35.90.244.93:6041`
- Network connectivity
- Firewall settings
- Credentials are correct

### Import Errors
Ensure you're running tests from the project root:
```bash
cd /path/to/DataAnnotationQA
PYTHONPATH=. python -m unittest discover tests
```

### Module Conflicts
If you see `ModuleNotFoundError: No module named 'unittest.mock'`, ensure:
- The directory is named `tests` not `unittest` (to avoid conflicts with Python's builtin)
- You're using Python 3.7+

## Adding New Tests

1. Create a new test file: `test_<feature_name>.py`
2. Import unittest: `import unittest`
3. Create test classes that inherit from `unittest.TestCase`
4. Name test methods starting with `test_`
5. Use assertions: `self.assertEqual()`, `self.assertTrue()`, etc.
6. Add to `__all__` in `__init__.py` if needed

Example:
```python
import unittest

class MyFeatureTests(unittest.TestCase):
    def test_basic_functionality(self):
        result = my_function()
        self.assertEqual(result, expected_value)
```

