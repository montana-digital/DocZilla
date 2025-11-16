"""
DocZilla Main Entry Point

This is the main Streamlit application entry point.
Part of the SPEAR Toolkit.
"""

import streamlit as st
from pathlib import Path
import sys
import platform

# Imports using proper package structure (PYTHONPATH set by run script)
from src.app.utils.logging import get_logger, generate_request_id
from src.app.utils.cache import init_cache_state
from src.app.utils.config import get_config
from src.app.components.layout import render_sidebar

# Configure page
st.set_page_config(
    page_title="DocZilla - File Conversion Specialist",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# Initialize utilities
init_cache_state()
config = get_config()

# Initialize logger
log_dir = Path("logs")
if config.get("directories.logs"):
    log_dir = Path(config.get("directories.logs"))
logger = get_logger(log_dir)

# Log app start
request_id = generate_request_id()
logger.log(
    level="INFO",
    message="DocZilla application started",
    module=__name__,
    request_id=request_id,
    operation="app_start"
)

# Render sidebar
render_sidebar()

# Find logo path
logo_path = None
if Path("src/app/assets/logos/DocZilla_logo.jpg").exists():
    logo_path = "src/app/assets/logos/DocZilla_logo.jpg"
elif Path("docs/DocZilla_logo.jpg").exists():
    logo_path = "docs/DocZilla_logo.jpg"
elif Path("docs/logo.png").exists():
    logo_path = "docs/logo.png"

# Main header with text on left and logo on right (centered)
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("""
    <style>
    .main-title {
        font-size: 3.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">DocZilla <span style="font-size: 1.2rem; font-weight: normal; color: #666;">- Part of the SPEAR Toolkit</span></h1>', unsafe_allow_html=True)
    st.markdown("**The file conversion specialist.**")

with col2:
    if logo_path:
        st.image(logo_path, width=200, use_container_width=False)

# Welcome section
st.header("Welcome to DocZilla")
st.write("""
DocZilla is a comprehensive document conversion and manipulation application 
designed to provide users with rich but simple document conversion tools 
with advanced features and technical insight into documents.
""")

# App Specifications and System Info
st.subheader("Application Specifications & System Information")

col_specs, col_system = st.columns(2)

with col_specs:
    st.markdown("**Application Specifications:**")
    st.write("""
    - **Version**: 1.0.0
    - **Framework**: Streamlit Multipage Application
    - **Supported Data Formats**: CSV, JSON, XLSX, XLS, TXT, XML, Parquet, Feather, ODS
    - **Supported Document Formats**: PDF, DOCX, DOC, RTF, TXT, ODT, HTML
    - **Supported Image Formats**: PNG, JPG, TIFF, WEBP, PDF, GIF, BMP, SVG, HEIC
    - **Architecture**: Modular service-based design
    - **Caching**: File-based caching with hash tracking
    - **Logging**: CSV-based activity logging with rotation
    """)

with col_system:
    st.markdown("**System Information:**")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    st.write(f"""
    - **Python Version**: {python_version}
    - **Platform**: {platform.system()} {platform.release()}
    - **Architecture**: {platform.machine()}
    - **Streamlit Version**: {st.__version__}
    - **Session ID**: {st.session_state.session_id[:8] if "session_id" in st.session_state else "N/A"}
    """)
    
    # Cache info if available
    if "cache_tracker" in st.session_state:
        cached_files = len(st.session_state.cache_tracker.get("file_hashes", {}))
        if cached_files > 0:
            st.write(f"- **Cached Files**: {cached_files}")

# Quick Start and Features in two columns
col_quick, col_features = st.columns([1, 2])

with col_quick:
    # Quick Start section
    st.subheader("🚀 Quick Start")
    st.write("""
    1. **Configure Directories**
       - Go to Settings page
       - Set Input and Output directories

    2. **Upload Files**
       - Use drag-and-drop
       - Or load from Input directory

    3. **Select Operation**
       - Choose from sidebar pages
       - Data, Document, or Image Handler

    4. **Process & Save**
       - Apply transformations
       - Save to Output directory
    """)

with col_features:
    # Features section
    st.subheader("Features")

    # Data File Handler
    st.markdown("#### 📊 Data File Handler")
    st.write("""
    - Convert between data formats (CSV, JSON, XLSX, XLS, TXT, XML, Parquet, Feather, ODS)
    - Clean and transform data (remove duplicates, handle missing values, standardize formats)
    - Merge and group tables with advanced options
    - Split large files by size or row count
    - Advanced operations: outlier detection, phone/URL standardization
    """)

    # Document Handler
    st.markdown("#### 📄 Document Handler")
    st.write("""
    - Convert document formats (PDF, DOCX, DOC, RTF, TXT, ODT, HTML)
    - Full-text search across uploaded documents
    - Text extraction and display with metadata
    - Page operations: move, append, and remove pages
    - Batch operations for multiple documents
    """)

    # Image Handler
    st.markdown("#### 🖼️ Image Handler")
    st.write("""
    - Convert between image formats (PNG, JPG, TIFF, WEBP, PDF, GIF, BMP, SVG, HEIC)
    - Compress images with quality control
    - Interactive cropping with aspect ratio presets
    - Grid combine: combine multiple images into optimized layouts
    """)

# Footer with link
spec_path = Path("docs/DocZilla_design_overview.md")
if spec_path.exists():
    st.link_button("View Complete Specifications", f"file://{spec_path.absolute()}")
else:
    st.caption("See `docs/DocZilla_design_overview.md` for complete specifications")

