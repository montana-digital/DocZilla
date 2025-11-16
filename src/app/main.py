"""
DocZilla Main Entry Point

This is the main Streamlit application entry point.
Part of the SPEAR Toolkit.
"""

import streamlit as st
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.app.utils.logging import get_logger, generate_request_id
from src.app.utils.cache import init_cache_state
from src.app.utils.config import get_config
from src.app.components.animation import render_title_with_animation
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

# Main title with animation
render_title_with_animation(
    app_name="DocZilla",
    static_text="Part of the SPEAR Toolkit",
    animation_type="fade"
)
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

# Main content

