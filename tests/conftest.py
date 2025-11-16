"""
Pytest configuration and shared fixtures
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_dataframe():
    """Fixture providing a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [30, 25, 35, 28, 32],
        'value': [100, 200, 150, 300, 250]
    })


@pytest.fixture
def sample_dataframe_large():
    """Fixture providing a larger sample DataFrame."""
    return pd.DataFrame({
        'id': range(1000),
        'name': [f'User_{i}' for i in range(1000)],
        'value': range(1000, 2000)
    })


@pytest.fixture
def temp_dir():
    """Fixture providing a temporary directory."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_csv_file(temp_dir, sample_dataframe):
    """Fixture providing a sample CSV file."""
    file_path = temp_dir / "test.csv"
    sample_dataframe.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def sample_json_file(temp_dir, sample_dataframe):
    """Fixture providing a sample JSON file."""
    file_path = temp_dir / "test.json"
    sample_dataframe.to_json(file_path, orient='records', indent=2)
    return file_path


@pytest.fixture
def sample_xlsx_file(temp_dir, sample_dataframe):
    """Fixture providing a sample XLSX file."""
    file_path = temp_dir / "test.xlsx"
    sample_dataframe.to_excel(file_path, index=False, engine='openpyxl')
    return file_path

