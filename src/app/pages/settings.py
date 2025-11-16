"""
Settings Page

Configure directories, manage temp data, check dependencies, and view logs.
"""

import streamlit as st
from pathlib import Path
import shutil

# Imports using proper package structure
from src.app.components.layout import render_page_header, render_sidebar
from src.app.utils.config import get_config
from src.app.components.activity_log import render_activity_log

# Streamlit multipage: Don't call st.set_page_config() here

render_sidebar()

config = get_config()

render_page_header(
    title="⚙️ Settings",
    subtitle="Configure directories, logs, cache and dependencies"
)

st.markdown("### Directories")

col1, col2 = st.columns(2)
with col1:
    input_dir = st.text_input("Input directory", value=str(config.get("directories.input", "./input")))
with col2:
    output_dir = st.text_input("Output directory", value=str(config.get("directories.output", "./output")))

save_dirs = st.button("Save Directories")
if save_dirs:
    config.set("directories.input", input_dir)
    config.set("directories.output", output_dir)
    config.save()
    st.success("Directories saved")

st.markdown("---")

st.markdown("### Temp / Index Management")
col3, col4 = st.columns(2)
with col3:
    if st.button("Clear temp folder (temp/)"):
        temp_path = Path("temp")
        if temp_path.exists():
            try:
                shutil.rmtree(temp_path)
                st.success("Temp folder cleared")
            except Exception as e:
                st.error(f"Failed to clear temp: {e}")
        else:
            st.info("Temp folder not found")
with col4:
    if st.button("Clear persistent index (temp/index)"):
        idx = Path("temp") / "index"
        if idx.exists():
            try:
                shutil.rmtree(idx)
                st.success("Persistent index cleared")
            except Exception as e:
                st.error(f"Failed to clear index: {e}")
        else:
            st.info("No persistent index found")

st.markdown("---")

st.markdown("### Input Watcher")
watch_enabled = st.toggle("Enable live Input folder watching", value=bool(config.get("watchdog.enabled", True)))
if st.button("Save Watcher Settings"):
    config.set("watchdog.enabled", bool(watch_enabled))
    config.save()
    st.success("Watcher settings saved")

st.markdown("---")

st.markdown("### Dependency Check")

required = [
    ("streamlit", "Core UI"),
    ("pandas", "Data handling"),
    ("numpy", "Numerics"),
    ("openpyxl", "Excel XLSX"),
    ("rapidfuzz", "Similarity merge"),
    ("pyarrow", "Parquet/Feather"),
    ("xmltodict", "XML parsing"),
    ("chardet", "Encoding detection (CSV/TXT)"),
    ("PyPDF2", "PDF page ops"),
    ("pdfminer.high_level", "PDF text extract (fallback)"),
    ("docx", "DOCX text"),
    ("docx2pdf", "DOCX→PDF conversion"),
    ("pdf2docx", "PDF→DOCX conversion"),
    ("PIL", "Images (Pillow)"),
    ("plotly", "Interactive charts (optional)"),
    ("streamlit_autorefresh", "Auto-refresh input directory (optional)"),
    ("streamlit_cropper", "Image cropping (optional)"),
    ("watchdog", "File watching (optional, falls back to polling)")
]

missing = []
for mod, purpose in required:
    try:
        __import__(mod.split('.')[0])
        st.success(f"{mod} ✓ ({purpose})")
    except Exception:
        st.warning(f"{mod} ✗ missing ({purpose})")
        missing.append(mod)

if missing:
    st.info("Feature unavailable: install missing packages")
    st.code("pip install " + " ".join(sorted(set(missing))), language="bash")

st.markdown("---")

st.markdown("### Logs (last 200 lines)")
logs_dir = Path("logs")
if logs_dir.exists():
    latest = sorted(logs_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if latest:
        sel = st.selectbox("Select log file", [p.name for p in latest])
        if sel:
            p = logs_dir / sel
            try:
                text = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                tail = "\n".join(text[-200:])
                st.text_area("Log tail", value=tail, height=200)
                st.download_button("Download log", data=p.read_bytes(), file_name=p.name)
            except Exception as e:
                st.error(f"Failed to read log: {e}")
    else:
        st.info("No log files yet")
else:
    st.info("Logs directory not found")

st.markdown("---")

st.markdown("### Logo Management")
st.info("Upload logos for each page (150x150px recommended)")

logo_tabs = st.tabs(["Main Logo", "Data Handler", "Document Handler", "Image Handler", "Settings"])

logo_pages = {
    "Main Logo": "main",
    "Data Handler": "data_handler",
    "Document Handler": "document_handler",
    "Image Handler": "image_handler",
    "Settings": "settings"
}

for tab, page_name in zip(logo_tabs, logo_pages.keys()):
    with tab:
        logo_key = f"logo_{logo_pages[page_name]}"
        current_logo = config.get(f"logos.{logo_key}", "")
        
        if current_logo and Path(current_logo).exists():
            st.image(current_logo, width=150, caption=f"Current {page_name} logo")
        
        uploaded_logo = st.file_uploader(
            f"Upload {page_name} logo",
            type=["png", "jpg", "jpeg"],
            key=f"upload_{logo_key}"
        )
        
        if uploaded_logo:
            logo_dir = Path("src/app/assets/logos")
            logo_dir.mkdir(parents=True, exist_ok=True)
            logo_path = logo_dir / f"{logo_key}_{uploaded_logo.name}"
            
            with open(logo_path, "wb") as f:
                f.write(uploaded_logo.getbuffer())
            
            config.set(f"logos.{logo_key}", str(logo_path))
            config.save()
            st.success(f"Logo saved: {logo_path.name}")
            st.rerun()

st.markdown("---")

st.markdown("### Cache Statistics")
try:
    from src.app.utils.cache import get_cache_stats
    
    cache_stats = get_cache_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cached Files", cache_stats.get("file_count", 0))
    with col2:
        cache_size_mb = cache_stats.get("total_size_bytes", 0) / (1024 * 1024)
        st.metric("Cache Size", f"{cache_size_mb:.2f} MB")
    with col3:
        max_size_gb = config.get("cache.max_size_gb", 2)
        st.metric("Max Cache Size", f"{max_size_gb} GB")
    
    if st.button("Clear Cache"):
        from src.app.utils.cache import clear_cache
        clear_cache()
        st.success("Cache cleared")
        st.rerun()
        
except Exception as e:
    st.warning(f"Cache statistics unavailable: {e}")

st.markdown("---")
st.markdown("### Activity Log (Filters)")
render_activity_log("logs")

