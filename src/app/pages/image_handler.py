"""
Image File Handler Page

Handles image operations: upload, conversion, compression, cropping, grid combine.
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
    title="🖼️ Image File Handler",
    subtitle="Convert, compress, crop, and combine images"
)

# Placeholder content
st.info("🚧 Under construction - Coming in Phase 4")

st.markdown("""
This page will handle:
- PNG, JPG, TIFF, WEBP, PDF, GIF, BMP image operations
- Format conversion
- Compression with quality control
- Interactive cropping
- Grid combine for OCR preparation

See `docs/DocZilla_design_overview.md` for specifications.
""")

