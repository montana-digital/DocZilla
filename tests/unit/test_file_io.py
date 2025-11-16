"""
Unit tests for File I/O Service
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.app.services.file_io import (
    load_data_file,
    save_data_file,
    get_file_metadata,
    move_file,
    generate_timestamped_filename
)
from src.app.utils.exceptions import OperationalError, ValidationError


class TestLoadDataFile:
    """Tests for load_data_file function."""
    
    def test_load_csv(self):
        """Test loading CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,age\nAlice,30\nBob,25\n")
            f.flush()
            df = load_data_file(f.name)
            assert len(df) == 2
            assert list(df.columns) == ['name', 'age']
            assert df.iloc[0]['name'] == 'Alice'
    
    def test_load_json(self):
        """Test loading JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"name": ["Alice", "Bob"], "age": [30, 25]}')
            f.flush()
            df = load_data_file(f.name)
            assert len(df) == 2
            assert 'name' in df.columns
    
    def test_load_xlsx(self):
        """Test loading XLSX file."""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            df.to_excel(f.name, index=False)
            f.flush()
            loaded = load_data_file(f.name)
            assert len(loaded) == 2
            assert 'a' in loaded.columns
    
    def test_load_unsupported_format(self):
        """Test loading unsupported format raises error."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"test")
            f.flush()
            with pytest.raises(OperationalError):
                load_data_file(f.name)
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises error."""
        with pytest.raises(OperationalError):
            load_data_file("nonexistent_file.csv")


class TestSaveDataFile:
    """Tests for save_data_file function."""
    
    def test_save_csv(self):
        """Test saving CSV file."""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        with tempfile.TemporaryDirectory() as tmp:
            out_path = save_data_file(df, tmp, 'csv')
            assert out_path.exists()
            assert out_path.suffix == '.csv'
            loaded = pd.read_csv(out_path)
            assert len(loaded) == 2
    
    def test_save_json(self):
        """Test saving JSON file."""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        with tempfile.TemporaryDirectory() as tmp:
            out_path = save_data_file(df, tmp, 'json')
            assert out_path.exists()
            assert out_path.suffix == '.json'
    
    def test_save_xlsx(self):
        """Test saving XLSX file."""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        with tempfile.TemporaryDirectory() as tmp:
            out_path = save_data_file(df, tmp, 'xlsx')
            assert out_path.exists()
            assert out_path.suffix == '.xlsx'
    
    def test_save_unsupported_format(self):
        """Test saving unsupported format raises error."""
        df = pd.DataFrame({'a': [1, 2]})
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(OperationalError):
                save_data_file(df, tmp, 'xyz')


class TestGetFileMetadata:
    """Tests for get_file_metadata function."""
    
    def test_get_csv_metadata(self):
        """Test getting CSV file metadata."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            metadata = get_file_metadata(f.name)
            assert metadata['rows'] == 3
            assert metadata['columns'] == 2
            assert 'file_size' in metadata
            assert 'extension' in metadata
    
    def test_get_nonexistent_file_metadata(self):
        """Test getting metadata for nonexistent file raises error."""
        with pytest.raises(OperationalError):
            get_file_metadata("nonexistent.csv")


class TestMoveFile:
    """Tests for move_file function."""
    
    def test_move_file_with_verification(self):
        """Test moving file with verification."""
        # Create file and close it before moving (Windows file locking)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as src:
            src.write("test content")
            src.flush()
            src_path = Path(src.name)
        
        # File is now closed, safe to move
        try:
            with tempfile.TemporaryDirectory() as tmp:
                dest_path = Path(tmp) / "moved_file.txt"
                result = move_file(src_path, dest_path, verify=True)
                assert result is True
                assert dest_path.exists()
                assert not src_path.exists()
                assert dest_path.read_text() == "test content"
        finally:
            # Cleanup in case of failure
            if src_path.exists():
                try:
                    src_path.unlink()
                except Exception:
                    pass
    
    def test_move_nonexistent_file(self):
        """Test moving nonexistent file raises error."""
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "dest.txt"
            with pytest.raises(OperationalError):
                move_file("nonexistent.txt", dest)


class TestGenerateTimestampedFilename:
    """Tests for generate_timestamped_filename function."""
    
    def test_generate_timestamped_filename(self):
        """Test generating timestamped filename."""
        filename = generate_timestamped_filename("test", "csv")
        assert filename.startswith("test_")
        assert filename.endswith(".csv")
        assert "_" in filename  # Should contain timestamp
    
    def test_generate_timestamped_filename_sanitizes(self):
        """Test that special characters are sanitized."""
        filename = generate_timestamped_filename("test/file:name", "csv")
        assert "/" not in filename
        assert ":" not in filename
        assert filename.endswith(".csv")

