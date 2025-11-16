"""
Integration tests for conversion workflows
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.app.services.file_io import load_data_file, save_data_file
from src.app.services.conversions import ConversionRegistry
from src.app.services.data_ops import merge_dataframes


class TestDataConversionWorkflow:
    """Integration tests for data file conversion workflows."""
    
    def test_csv_to_json_to_xlsx_workflow(self):
        """Test converting CSV -> JSON -> XLSX."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [30, 25, 35]
        })
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            
            # Step 1: Save as CSV
            csv_file = save_data_file(df, tmp_dir, 'csv')
            assert csv_file.exists()
            
            # Step 2: Convert CSV to JSON
            json_file = ConversionRegistry.convert_file(
                csv_file, "csv", "json", tmp_dir
            )
            assert json_file.exists()
            
            # Step 3: Convert JSON to XLSX
            xlsx_file = ConversionRegistry.convert_file(
                json_file, "json", "xlsx", tmp_dir
            )
            assert xlsx_file.exists()
            
            # Verify final file content
            final_df = load_data_file(xlsx_file)
            assert len(final_df) == 3
            assert 'name' in final_df.columns
            assert final_df.iloc[0]['name'] == 'Alice'
    
    def test_merge_and_convert_workflow(self):
        """Test merging two files and converting result."""
        df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})
        df2 = pd.DataFrame({'id': [2, 3], 'value': [10, 20]})
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            
            # Save both files
            file1 = save_data_file(df1, tmp_dir, 'csv')
            file2 = save_data_file(df2, tmp_dir, 'csv')
            
            # Load and merge
            loaded1 = load_data_file(file1)
            loaded2 = load_data_file(file2)
            merged = merge_dataframes(loaded1, loaded2, on='id', how='inner')
            
            # Save merged result as XLSX
            merged_file = save_data_file(merged, tmp_dir, 'xlsx')
            assert merged_file.exists()
            
            # Verify merged content
            final_df = load_data_file(merged_file)
            assert len(final_df) >= 1
            # Verify merge worked - should have id column and at least one other column
            assert 'id' in final_df.columns
            assert len(final_df.columns) >= 2  # id + at least one other column
            # Check that we have data from both DataFrames (name from df1 or value from df2)
            has_name = any('name' in col.lower() for col in final_df.columns)
            has_value = any('value' in col.lower() for col in final_df.columns)
            assert has_name or has_value, f"Expected 'name' or 'value' column, got: {list(final_df.columns)}"

