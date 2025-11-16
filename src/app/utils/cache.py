"""
Caching Utilities

Streamlit cache management with SHA256 file hashing for invalidation.
"""

import streamlit as st
import hashlib
from pathlib import Path
from typing import Any, Callable
from functools import wraps


def get_file_hash(file_path: Path) -> str:
    """
    Generate SHA256 hash of file content and modification time.
    
    Args:
        file_path: Path to file
    
    Returns:
        SHA256 hash hex string
    """
    try:
        stat = file_path.stat()
        mtime = str(stat.st_mtime)
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Combine content and mtime for hash
        combined = content + mtime.encode()
        return hashlib.sha256(combined).hexdigest()
    except Exception as e:
        # If file doesn't exist or can't be read, return hash of error
        return hashlib.sha256(str(e).encode()).hexdigest()


def get_string_hash(text: str) -> str:
    """
    Generate SHA256 hash of string.
    
    Args:
        text: String to hash
    
    Returns:
        SHA256 hash hex string
    """
    return hashlib.sha256(text.encode()).hexdigest()


def cache_file_operation(
    show_spinner: bool = True,
    ttl: int | float | None = None
):
    """
    Decorator to cache file-based operations using file hash for invalidation.
    
    Usage:
        @cache_file_operation()
        def load_data(file_path: str):
            # Load and process file
            return data
    
    Args:
        show_spinner: Show spinner while computing
        ttl: Time to live in seconds (None = infinite)
    """
    def decorator(func: Callable) -> Callable:
        @st.cache_data(
            show_spinner=show_spinner,
            ttl=ttl
        )
        def cached_func(file_path: str, file_hash: str, *args, **kwargs):
            """Cached function with file hash parameter."""
            return func(file_path, *args, **kwargs)
        
        @wraps(func)
        def wrapper(file_path: str, *args, **kwargs):
            """Wrapper that computes file hash and calls cached function."""
            file_path_obj = Path(file_path)
            file_hash = get_file_hash(file_path_obj)
            return cached_func(file_path, file_hash, *args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_file_cache(file_path: str):
    """
    Invalidate cache for a specific file.
    
    Note: Streamlit doesn't support selective cache invalidation directly.
    This function clears all data cache. For production, you may need to
    track cache keys and manage them manually.
    
    Args:
        file_path: Path to file whose cache should be invalidated
    """
    # Streamlit doesn't have selective cache invalidation
    # This clears all data cache
    st.cache_data.clear()
    st.rerun()


def clear_all_cache():
    """Clear all Streamlit cache (data and resource)."""
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()


def get_cache_info() -> dict:
    """
    Get cache statistics (if available).
    
    Returns:
        Dictionary with cache information
    """
    # Streamlit doesn't expose cache statistics directly
    # This is a placeholder for future implementation
    return {
        "data_cache_cleared": False,
        "resource_cache_cleared": False,
        "note": "Cache statistics not available in Streamlit"
    }


def get_cache_stats() -> dict:
    """
    Get cache statistics from session state tracking.
    
    Returns:
        Dictionary with cache statistics
    """
    init_cache_state()
    tracker = st.session_state.cache_tracker
    
    # Count tracked files
    file_count = len(tracker.get("file_hashes", {}))
    
    # Estimate cache size (rough approximation)
    # Streamlit doesn't expose actual cache size, so we estimate based on tracked files
    total_size_bytes = file_count * 1024 * 1024  # Rough estimate: 1MB per file
    
    return {
        "file_count": file_count,
        "total_size_bytes": total_size_bytes,
        "tracked_files": list(tracker.get("file_hashes", {}).keys())
    }


def clear_cache():
    """Clear all caches and tracking."""
    clear_all_cache()
    init_cache_state()
    st.session_state.cache_tracker = {
        "file_hashes": {},
        "cache_keys": set()
    }


# Initialize session state for cache tracking
def init_cache_state():
    """Initialize cache tracking in session state."""
    if "cache_tracker" not in st.session_state:
        st.session_state.cache_tracker = {
            "file_hashes": {},
            "cache_keys": set()
        }


def track_file_hash(file_path: str, file_hash: str):
    """
    Track file hash in session state for cache management.
    
    Args:
        file_path: Path to file
        file_hash: SHA256 hash of file
    """
    init_cache_state()
    st.session_state.cache_tracker["file_hashes"][file_path] = file_hash


def get_tracked_hash(file_path: str) -> str | None:
    """
    Get tracked file hash from session state.
    
    Args:
        file_path: Path to file
    
    Returns:
        File hash if tracked, None otherwise
    """
    init_cache_state()
    return st.session_state.cache_tracker["file_hashes"].get(file_path)


def check_file_changed(file_path: str) -> bool:
    """
    Check if file has changed since last cache.
    
    Args:
        file_path: Path to file
    
    Returns:
        True if file changed, False otherwise
    """
    current_hash = get_file_hash(Path(file_path))
    tracked_hash = get_tracked_hash(file_path)
    
    if tracked_hash is None:
        # First time seeing this file
        track_file_hash(file_path, current_hash)
        return False
    
    if current_hash != tracked_hash:
        # File changed
        track_file_hash(file_path, current_hash)
        return True
    
    return False

