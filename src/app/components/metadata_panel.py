"""
Metadata Panel Components

Reusable components for displaying file and data metadata.
"""

import streamlit as st
from typing import Optional, Dict, Any
from pathlib import Path


def render_file_metadata(metadata: Dict[str, Any], title: str = "File Metadata"):
    """
    Render file metadata in collapsible section.
    
    Args:
        metadata: Dictionary of metadata key-value pairs
        title: Section title (default: "File Metadata")
    """
    with st.expander(f"📋 {title}"):
        st.json(metadata)


def render_multiple_file_metadata(
    files_metadata: Dict[str, Dict[str, Any]],
    title: str = "Files Metadata"
):
    """
    Render metadata for multiple files in collapsible sections.
    
    Args:
        files_metadata: Dictionary mapping file names to metadata dicts
        title: Section title (default: "Files Metadata")
    """
    if not files_metadata:
        return
    
    with st.expander(f"📋 {title}"):
        for file_name, metadata in files_metadata.items():
            st.markdown(f"**{file_name}**")
            st.json(metadata)
            st.markdown("---")


def render_metadata_summary(
    metadata: Dict[str, Any],
    show_details: bool = False
):
    """
    Render metadata summary with optional details.
    
    Args:
        metadata: Dictionary of metadata
        show_details: Whether to show detailed metadata (default: False)
    """
    # Summary columns
    if "file_size" in metadata:
        size_mb = metadata["file_size"] / (1024 * 1024)
        st.metric("File Size", f"{size_mb:.2f} MB")
    
    if "rows" in metadata:
        st.metric("Rows", f"{metadata['rows']:,}")
    
    if "columns" in metadata:
        st.metric("Columns", metadata["columns"])
    
    # Optional detailed metadata
    if show_details:
        render_file_metadata(metadata)

