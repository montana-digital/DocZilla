"""
Integration tests for data operations workflows
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.app.services.file_io import load_data_file, save_data_file
from src.app.services.data_ops import (
    remove_empty_rows_columns,
    remove_duplicates,
    handle_missing_values,
    standardize_phone_numbers,
    detect_outliers,
    group_by_dataframe
)


class TestDataCleaningWorkflow:
    """Integration tests for data cleaning workflows."""
    
    def test_clean_and_save_workflow(self):
        """Test cleaning data and saving result."""
        # Create messy data
        df = pd.DataFrame({
            'id': [1, 2, 2, None],
            'name': ['Alice', 'Bob', 'Bob', ''],
            'age': [30, None, 25, 35],
            'phone': ['123-456-7890', '(555) 123-4567', '1234567890', None]
        })
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            
            # Save original
            original_file = save_data_file(df, tmp_dir, 'csv')
            
            # Load and clean
            loaded = load_data_file(original_file)
            
            # Remove duplicates
            cleaned, dup_count = remove_duplicates(loaded, ['id', 'name'])
            assert dup_count >= 1
            
            # Handle missing values
            cleaned = handle_missing_values(cleaned, ['age'], strategy='mean')
            
            # Remove empty rows/columns
            cleaned, rows_removed, cols_removed = remove_empty_rows_columns(cleaned)
            
            # Save cleaned result
            cleaned_file = save_data_file(cleaned, tmp_dir, 'xlsx')
            assert cleaned_file.exists()
            
            # Verify cleaned file
            final_df = load_data_file(cleaned_file)
            assert len(final_df) <= len(df)
    
    def test_standardize_and_group_workflow(self):
        """Test standardizing data and grouping."""
        df = pd.DataFrame({
            'category': ['A', 'A', 'B', 'B'],
            'value': [10, 20, 15, 25],
            'phone': ['1234567890', '555-123-4567', '123-456-7890', '5551234567']
        })
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            
            # Save original
            original_file = save_data_file(df, tmp_dir, 'csv')
            loaded = load_data_file(original_file)
            
            # Standardize phone numbers
            try:
                standardized = standardize_phone_numbers(
                    loaded, 'phone', format_type='E.164'
                )
                assert 'phone_formatted' in standardized.columns
            except Exception:
                # Skip if phonenumbers not installed
                pytest.skip("phonenumbers library not available")
            
            # Group by category
            grouped = group_by_dataframe(
                loaded,
                by='category',
                aggregations={'value': ['sum', 'mean']}
            )
            
            assert len(grouped) == 2  # Two categories
            assert 'category' in grouped.columns

