"""
Unit tests for Cache Utilities
"""

import pytest
import tempfile
from pathlib import Path
from src.app.utils.cache import (
    get_file_hash,
    get_string_hash,
    track_file_hash,
    get_tracked_hash,
    check_file_changed
)


class TestFileHash:
    """Tests for file hashing functions."""
    
    def test_get_file_hash(self):
        """Test getting file hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()
            hash1 = get_file_hash(Path(f.name))
            assert len(hash1) == 64  # SHA256 hex string length
            assert isinstance(hash1, str)
    
    def test_get_file_hash_changes_with_content(self):
        """Test that hash changes when content changes."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("content1")
            f.flush()
            hash1 = get_file_hash(Path(f.name))
            
            # Modify content
            with open(f.name, 'w') as f2:
                f2.write("content2")
            
            hash2 = get_file_hash(Path(f.name))
            assert hash1 != hash2
    
    def test_get_string_hash(self):
        """Test getting string hash."""
        hash1 = get_string_hash("test")
        hash2 = get_string_hash("test")
        assert hash1 == hash2
        assert len(hash1) == 64


class TestFileTracking:
    """Tests for file tracking functions."""
    
    def test_track_and_get_hash(self):
        """Test tracking and retrieving file hash."""
        import streamlit as st
        
        # Initialize session state for testing
        if "cache_tracker" not in st.session_state:
            st.session_state.cache_tracker = {
                "file_hashes": {},
                "cache_keys": set()
            }
        
        track_file_hash("test_file.txt", "abc123")
        retrieved = get_tracked_hash("test_file.txt")
        assert retrieved == "abc123"
    
    def test_check_file_changed(self):
        """Test checking if file has changed."""
        import streamlit as st
        
        # Initialize session state
        if "cache_tracker" not in st.session_state:
            st.session_state.cache_tracker = {
                "file_hashes": {},
                "cache_keys": set()
            }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("initial")
            f.flush()
            file_path = f.name
            
            # First check (should not be changed)
            changed1 = check_file_changed(file_path)
            assert changed1 is False
            
            # Modify file
            with open(file_path, 'w') as f2:
                f2.write("modified")
            
            # Second check (should be changed)
            changed2 = check_file_changed(file_path)
            assert changed2 is True

