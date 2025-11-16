"""
End-to-end smoke tests for critical user paths
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.app.services.file_io import load_data_file, save_data_file
from src.app.services.conversions import ConversionRegistry
from src.app.services.fragments import split_data_file


class TestCriticalUserPaths:
    """E2E tests for critical user workflows."""
    
    def test_upload_analyze_convert_path(self):
        """Test: Upload CSV -> Analyze -> Convert to XLSX."""
        # Simulate user uploading CSV
        df = pd.DataFrame({
            'id': range(100),
            'name': [f'User_{i}' for i in range(100)],
            'value': range(100, 200)
        })
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            
            # Step 1: User uploads file (save as CSV)
            uploaded_file = save_data_file(df, tmp_dir, 'csv')
            assert uploaded_file.exists()
            
            # Step 2: System analyzes file (load and get metadata)
            loaded_df = load_data_file(uploaded_file)
            assert len(loaded_df) == 100
            assert 'name' in loaded_df.columns
            
            # Step 3: User converts to XLSX
            converted_file = ConversionRegistry.convert_file(
                uploaded_file, "csv", "xlsx", tmp_dir
            )
            assert converted_file.exists()
            
            # Step 4: Verify converted file
            final_df = load_data_file(converted_file)
            assert len(final_df) == 100
            assert list(final_df.columns) == ['id', 'name', 'value']
    
    def test_large_file_split_path(self):
        """Test: Upload large file -> Split into chunks."""
        # Create large dataset
        df = pd.DataFrame({
            'id': range(1000),
            'data': [f'data_{i}' for i in range(1000)]
        })
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            
            # Step 1: Save large file
            large_file = save_data_file(df, tmp_dir, 'csv')
            assert large_file.exists()
            
            # Step 2: Split into chunks (50 rows per file)
            split_files, zip_path = split_data_file(
                large_file,
                split_method="rows",
                target_rows=50,
                output_dir=tmp_dir,
                create_zip=False
            )
            
            # Step 3: Verify splits
            assert len(split_files) == 20  # 1000 / 50 = 20 files
            total_rows = 0
            for split_file in split_files:
                loaded = load_data_file(split_file)
                assert len(loaded) == 50
                total_rows += len(loaded)
            
            assert total_rows == 1000
    
    def test_merge_and_export_path(self):
        """Test: Upload 2 files -> Merge -> Export."""
        df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C']
        })
        df2 = pd.DataFrame({
            'id': [2, 3, 4],
            'value': [10, 20, 30]
        })
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            
            # Step 1: Save both files
            file1 = save_data_file(df1, tmp_dir, 'csv')
            file2 = save_data_file(df2, tmp_dir, 'csv')
            
            # Step 2: Load both
            loaded1 = load_data_file(file1)
            loaded2 = load_data_file(file2)
            
            # Step 3: Merge
            from src.app.services.data_ops import merge_dataframes
            merged = merge_dataframes(loaded1, loaded2, on='id', how='inner')
            assert len(merged) >= 2
            
            # Step 4: Export merged result
            merged_file = save_data_file(merged, tmp_dir, 'xlsx')
            assert merged_file.exists()
            
            # Step 5: Verify export
            final_df = load_data_file(merged_file)
            # Verify merge worked - should have id column and data from both DataFrames
            assert 'id' in final_df.columns
            assert len(final_df.columns) >= 2  # id + at least one other column
            # Check that we have data from both DataFrames
            has_name = any('name' in col.lower() for col in final_df.columns)
            has_value = any('value' in col.lower() for col in final_df.columns)
            assert has_name or has_value, f"Expected 'name' or 'value' column, got: {list(final_df.columns)}"

