# DocZilla Test Suite

Comprehensive test suite for DocZilla application.

## Test Structure

```
tests/
├── unit/              # Unit tests for individual functions
│   ├── test_data_ops.py
│   ├── test_file_io.py
│   ├── test_conversions.py
│   ├── test_doc_ops.py
│   ├── test_cache.py
│   └── test_validators.py
├── integration/       # Integration tests for workflows
│   ├── test_file_io_csv.py
│   ├── test_conversion_workflows.py
│   └── test_data_operations_workflow.py
├── e2e_smoke/         # End-to-end smoke tests
│   ├── test_smoke.py
│   ├── test_flows.py
│   └── test_critical_paths.py
├── fixtures/          # Test data files
└── conftest.py        # Shared fixtures
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=src/app --cov-report=html
```

### Run specific test type
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e_smoke/
```

### Run specific test file
```bash
pytest tests/unit/test_data_ops.py
```

### Run with markers
```bash
# Run only fast tests
pytest -m "not slow"

# Run only unit tests
pytest -m unit
```

## Test Coverage

Target: **80%+ coverage**

Current coverage can be viewed in `htmlcov/index.html` after running tests with coverage.

## Writing New Tests

### Unit Test Example
```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

### Integration Test Example
```python
def test_workflow_name():
    """Test complete workflow."""
    # Step 1: Setup
    # Step 2: Execute workflow
    # Step 3: Verify results
```

## Test Fixtures

Common fixtures available in `conftest.py`:
- `sample_dataframe` - Small test DataFrame
- `sample_dataframe_large` - Large test DataFrame
- `temp_dir` - Temporary directory
- `sample_csv_file` - Sample CSV file
- `sample_json_file` - Sample JSON file
- `sample_xlsx_file` - Sample XLSX file

## Notes

- All tests use temporary files/directories
- Tests are isolated (no shared state)
- Tests clean up after themselves
- Use fixtures for common test data

