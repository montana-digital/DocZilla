import tempfile
from pathlib import Path
import pandas as pd
from src.app.services.file_io import save_data_file, load_data_file
from src.app.services.fragments import split_data_file


def test_save_and_load_csv_roundtrip():
    df = pd.DataFrame({'a': [1, 2], 'b': ['x', 'y']})
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        out_path = save_data_file(df, out_dir, 'csv')
        assert out_path.exists()
        loaded = load_data_file(out_path)
        assert list(loaded.columns) == ['a', 'b']
        assert len(loaded) == 2


def test_split_data_file_by_rows():
    """Test splitting a data file by row count."""
    # Create a test DataFrame with 100 rows
    df = pd.DataFrame({
        'id': range(100),
        'value': [f'val_{i}' for i in range(100)]
    })
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        
        # Save the test file
        source_file = save_data_file(df, tmp_dir, 'csv')
        assert source_file.exists()
        
        # Split by rows (10 rows per file)
        output_files, zip_path = split_data_file(
            source_file,
            split_method="rows",
            target_rows=10,
            output_dir=tmp_dir,
            create_zip=False
        )
        
        # Should create 10 files (100 rows / 10 rows per file)
        assert len(output_files) == 10
        
        # Verify each split file
        total_rows = 0
        for out_file in output_files:
            assert out_file.exists()
            loaded_df = load_data_file(out_file)
            assert len(loaded_df) == 10
            assert list(loaded_df.columns) == ['id', 'value']
            total_rows += len(loaded_df)
        
        # Total rows should match original
        assert total_rows == 100
        assert zip_path is None  # No zip requested


def test_split_data_file_by_size():
    """Test splitting a data file by estimated file size."""
    # Create a larger test DataFrame
    df = pd.DataFrame({
        'id': range(50),
        'text': [f'This is row {i} with some text content' * 10 for i in range(50)]
    })
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        
        # Save the test file
        source_file = save_data_file(df, tmp_dir, 'csv')
        assert source_file.exists()
        
        # Get original file size
        original_size = source_file.stat().st_size
        target_size_mb = (original_size / (1024 * 1024)) * 0.3  # Split into ~3 files
        
        # Split by size
        output_files, zip_path = split_data_file(
            source_file,
            split_method="size",
            target_size_mb=target_size_mb,
            output_dir=tmp_dir,
            create_zip=False
        )
        
        # Should create at least 2 files
        assert len(output_files) >= 2
        
        # Verify all rows are preserved
        total_rows = 0
        for out_file in output_files:
            assert out_file.exists()
            loaded_df = load_data_file(out_file)
            total_rows += len(loaded_df)
        
        assert total_rows == 50
        assert zip_path is None
