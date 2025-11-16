"""
Unit tests for Validators
"""

import pytest
import tempfile
from pathlib import Path
from src.app.utils.validators import (
    validate_file_path,
    validate_file_extension,
    sanitize_filename
)
from src.app.utils.exceptions import ValidationError


class TestValidateFileExtension:
    """Tests for validate_file_extension function."""
    
    def test_validate_valid_extension(self):
        """Test validating valid extension."""
        assert validate_file_extension("test.csv", [".csv", ".xlsx"]) is True
    
    def test_validate_invalid_extension(self):
        """Test validating invalid extension raises error."""
        with pytest.raises(ValidationError):
            validate_file_extension("test.xyz", [".csv", ".xlsx"])
    
    def test_validate_case_insensitive(self):
        """Test that extension validation is case insensitive."""
        assert validate_file_extension("test.CSV", [".csv"]) is True


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""
    
    def test_sanitize_removes_special_chars(self):
        """Test that special characters are removed."""
        result = sanitize_filename("test/file:name")
        assert "/" not in result
        assert ":" not in result
    
    def test_sanitize_preserves_alphanumeric(self):
        """Test that alphanumeric characters are preserved."""
        result = sanitize_filename("test_file_123")
        assert "test_file_123" == result
    
    def test_sanitize_handles_unicode(self):
        """Test that unicode characters are handled."""
        result = sanitize_filename("test_文件")
        assert isinstance(result, str)


class TestValidateFilePath:
    """Tests for validate_file_path function."""
    
    def test_validate_existing_file(self):
        """Test validating existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            f.flush()
            # Should not raise
            validate_file_path(Path(f.name))
    
    def test_validate_nonexistent_file(self):
        """Test validating nonexistent file raises error."""
        # validate_file_path raises FileNotFoundError (not ValidationError) for missing files
        from src.app.utils.exceptions import FileNotFoundError as CustomFileNotFoundError
        with pytest.raises(CustomFileNotFoundError):
            validate_file_path(Path("nonexistent_file.txt"))

