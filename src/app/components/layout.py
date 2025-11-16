"""
Layout Components

Reusable layout components: page headers, sidebars, tables.
"""

import streamlit as st
from pathlib import Path
import subprocess
import platform
from typing import Optional

# Imports using proper package structure
from src.app.utils.config import get_config


def render_page_header(title: str, subtitle: str, logo_path: Optional[str] = None):
    """
    Render standard page header with title, subtitle, and logo.
    
    Args:
        title: Page title
        subtitle: Page subtitle (2-line max)
        logo_path: Optional path to logo image (150x150px)
    """
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title(title)
        st.caption(subtitle)
    
    with col2:
        if logo_path and Path(logo_path).exists():
            st.image(logo_path, width=150)
        else:
            # Placeholder for logo
            st.info("Logo placeholder")


def render_sidebar():
    """Render standard sidebar with branding and navigation."""
    config = get_config()
    
    with st.sidebar:
        # Logo
        logo_path = config.get("logos.main", "")
        if logo_path and Path(logo_path).exists():
            st.image(logo_path, width=150)
        elif Path("docs/logo.png").exists():
            st.image("docs/logo.png", width=150)
        else:
            st.markdown("### 🦕 DocZilla")
        
        # Branding
        st.markdown("### DocZilla")
        st.caption("The file conversion specialist.")
        
        st.markdown("---")
        
        # Navigation info
        st.markdown("### Navigation")
        st.info("Use the sidebar menu above to navigate between pages")
        
        st.markdown("---")
        
        # Quick Links
        st.markdown("### Quick Links")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📂 Input Dir"):
                open_directory("input", config)
        
        with col2:
            if st.button("📂 Output Dir"):
                open_directory("output", config)
        
        st.markdown("---")
        
        # Session info
        if "session_id" in st.session_state:
            st.caption(f"Session: {st.session_state.session_id[:8]}")
        
        # Cache info (if available)
        if "cache_tracker" in st.session_state:
            cached_files = len(st.session_state.cache_tracker.get("file_hashes", {}))
            if cached_files > 0:
                st.caption(f"Cached: {cached_files} file(s)")


def open_directory(dir_type: str, config):
    """
    Open directory in system file explorer.
    
    Args:
        dir_type: Type of directory ("input" or "output")
        config: Configuration instance
    """
    dir_path = config.get(f"directories.{dir_type}", "")
    
    if not dir_path:
        st.warning(f"{dir_type.capitalize()} directory not configured. Set it in Settings.")
        return
    
    dir_path_obj = Path(dir_path)
    
    # Create directory if it doesn't exist
    if not dir_path_obj.exists():
        try:
            dir_path_obj.mkdir(parents=True, exist_ok=True)
            st.success(f"Created {dir_type} directory: {dir_path}")
        except Exception as e:
            st.error(f"Failed to create {dir_type} directory: {e}")
            return
    
    # Open directory in file explorer
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["explorer", str(dir_path_obj)], shell=False)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", str(dir_path_obj)])
        else:  # Linux
            subprocess.Popen(["xdg-open", str(dir_path_obj)])
        
        st.success(f"Opened {dir_type} directory")
    except Exception as e:
        st.error(f"Failed to open {dir_type} directory: {e}")


def render_quick_start(instructions: list[str]):
    """
    Render Quick Start instructions.
    
    Args:
        instructions: List of instruction strings (bullet points)
    """
    st.markdown("#### Quick Start")
    for instruction in instructions:
        st.markdown(f"- {instruction}")


def render_metadata_section(title: str, metadata: dict):
    """
    Render metadata in collapsible section.
    
    Args:
        title: Section title
        metadata: Dictionary of metadata key-value pairs
    """
    with st.expander(f"📋 {title}"):
        st.json(metadata)
