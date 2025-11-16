"""
Settings Page

Configuration and management: directories, logos, logs, cache, dependencies.
"""

import streamlit as st

st.set_page_config(
    page_title="Settings - DocZilla",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Settings")
st.caption("Configure DocZilla")

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

