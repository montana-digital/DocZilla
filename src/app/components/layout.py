"""
Layout Components

Reusable layout components: page headers, sidebars, tables.
"""

import streamlit as st


def render_page_header(title: str, subtitle: str, logo_path: str | None = None):
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
        if logo_path:
            st.image(logo_path, width=150)
        else:
            st.info("Logo placeholder")


def render_sidebar():
    """Render standard sidebar with branding and navigation."""
    with st.sidebar:
        st.markdown("### DocZilla")
        st.caption("The file conversion specialist.")
        
        st.markdown("---")
        st.markdown("### Navigation")
        st.info("Use sidebar menu to navigate")
        
        st.markdown("---")
        st.markdown("### Quick Links")
        # Input/Output directory buttons will go here


def render_quick_start(instructions: list[str]):
    """
    Render Quick Start instructions.
    
    Args:
        instructions: List of instruction strings (bullet points)
    """
    st.markdown("#### Quick Start")
    for instruction in instructions:
        st.markdown(f"- {instruction}")

