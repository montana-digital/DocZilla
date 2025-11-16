"""
DocZilla Main Entry Point

This is the main Streamlit application entry point.
Part of the SPEAR Toolkit.
"""

import streamlit as st
from pathlib import Path

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

# Main title with animation placeholder
st.title("DocZilla")
st.caption("Part of the SPEAR Toolkit")
st.markdown("**The file conversion specialist.**")

# Placeholder content
st.markdown("""
## Welcome to DocZilla

DocZilla is a comprehensive document conversion and manipulation application.

### Features

#### 📊 Data File Handler
- Convert between data formats (CSV, JSON, XLSX, etc.)
- Clean and transform data
- Merge and group tables
- Split large files

#### 📄 Document Handler
- Convert document formats (PDF, DOCX, etc.)
- Search across documents
- Manipulate pages

#### 🖼️ Image Handler
- Convert image formats
- Compress images
- Crop and combine images

### Getting Started

1. Configure Input/Output directories in Settings
2. Upload files using drag-and-drop or Input directory
3. Select operation from the sidebar
4. Process and save files

---

**Note**: This is a placeholder. Full implementation in progress.

See `docs/DocZilla_design_overview.md` for complete specifications.
""")

# Sidebar
with st.sidebar:
    st.image("docs/logo.png", width=150) if Path("docs/logo.png").exists() else st.write("Logo placeholder")
    st.markdown("### DocZilla")
    st.caption("The file conversion specialist.")
    
    st.markdown("---")
    st.markdown("### Navigation")
    st.info("Navigate using the sidebar menu above")
    
    st.markdown("---")
    st.markdown("### Quick Links")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Input Dir"):
            st.info("Open Input Directory")
    with col2:
        if st.button("Output Dir"):
            st.info("Open Output Directory")
    
    st.markdown("---")
    st.caption(f"Session: {st.session_state.session_id[:8]}")

