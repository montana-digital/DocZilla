"""
Settings Page

Configuration and management: directories, logos, logs, cache, dependencies.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.app.components.layout import render_page_header, render_sidebar

# Streamlit multipage: Don't call st.set_page_config() here

# Render sidebar
render_sidebar()

# Page header
render_page_header(
    title="⚙️ Settings",
    subtitle="Configure DocZilla"
)

# Placeholder content
st.info("🚧 Under construction - Coming in Phase 5")

st.markdown("""
This page will handle:
- Input/Output directory configuration
- Logo upload and management
- Activity log viewing and download
- Cache management and statistics
- Dependency health checks
- Temp data cleanup

See `docs/DocZilla_design_overview.md` for specifications.
""")

