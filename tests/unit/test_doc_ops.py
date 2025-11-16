"""
Unit tests for Document Operations Service
"""

import pytest
import tempfile
from pathlib import Path
from src.app.services.doc_ops import (
    extract_text,
    InMemorySearchIndex,
    PersistentSearchIndex
)


class TestExtractText:
    """Tests for extract_text function."""
    
    def test_extract_text_txt(self):
        """Test extracting text from TXT file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content\nLine 2")
            f.flush()
            text = extract_text(Path(f.name))
            assert "test content" in text
            assert "Line 2" in text
    
    def test_extract_text_nonexistent(self):
        """Test extracting from nonexistent file handles gracefully."""
        # extract_text may raise FileNotFoundError for .txt files
        # This is expected behavior - test that it doesn't crash the app
        try:
            text = extract_text(Path("nonexistent.txt"))
            # If it returns, should be string
            assert isinstance(text, str)
        except FileNotFoundError:
            # This is acceptable - file doesn't exist
            pass


class TestInMemorySearchIndex:
    """Tests for InMemorySearchIndex."""
    
    def test_add_and_search(self):
        """Test adding documents and searching."""
        index = InMemorySearchIndex()
        index.add("doc1", "This is a test document with keywords")
        index.add("doc2", "Another document with different content")
        
        results = index.search("keywords")
        assert "doc1" in results
        assert len(results["doc1"]) > 0
    
    def test_search_no_matches(self):
        """Test searching with no matches."""
        index = InMemorySearchIndex()
        index.add("doc1", "Some content")
        results = index.search("nonexistent")
        assert len(results) == 0
    
    def test_clear(self):
        """Test clearing index."""
        index = InMemorySearchIndex()
        index.add("doc1", "content")
        index.clear()
        results = index.search("content")
        assert len(results) == 0


class TestPersistentSearchIndex:
    """Tests for PersistentSearchIndex."""
    
    def test_add_and_search_persistent(self):
        """Test persistent index add and search."""
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "index"
            index = PersistentSearchIndex(index_path)
            index.add("doc1", "Test content with keywords")
            index.add("doc2", "Other content")
            
            results = index.search("keywords")
            assert "doc1" in results
    
    def test_persistent_across_instances(self):
        """Test that index persists across instances."""
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "index"
            
            # First instance
            index1 = PersistentSearchIndex(index_path)
            index1.add("doc1", "Persistent content")
            
            # Second instance (should see previous data)
            index2 = PersistentSearchIndex(index_path)
            results = index2.search("Persistent")
            assert "doc1" in results
    
    def test_clear_persistent(self):
        """Test clearing persistent index."""
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "index"
            index = PersistentSearchIndex(index_path)
            index.add("doc1", "content")
            index.clear()
            results = index.search("content")
            assert len(results) == 0

