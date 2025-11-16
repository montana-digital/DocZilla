"""
Data File Handler Page

Handles data file operations: upload, analysis, editing, conversion, cleaning.
"""

import streamlit as st
import sys
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List
import time

# Optional visualization (used defensively)
try:
    import plotly.express as px  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    px = None

# Imports using proper package structure
from src.app.components.layout import render_page_header, render_sidebar, render_quick_start
from src.app.components.tables import render_data_table, render_data_editor
from src.app.components.metadata_panel import (
    render_metadata_summary,
)
from src.app.utils.config import get_config
from src.app.utils.cache import check_file_changed, track_file_hash
from src.app.utils.logging import get_logger, generate_request_id
from src.app.utils.exceptions import OperationalError
from src.app.services.file_io import (
    load_data_file,
    save_data_file,
    get_file_metadata,
    move_file,
    generate_timestamped_filename,
)
from src.app.services.data_ops import (
    merge_dataframes,
    group_by_dataframe,
    detect_outliers,
    remove_empty_rows_columns,
    handle_missing_values,
    remove_duplicates,
    standardize_phone_numbers,
    standardize_urls,
    remove_characters,
    trim_whitespace,
    standardize_format,
)
from src.app.services.conversions import ConversionRegistry
from src.app.services.fragments import split_data_file
from src.app.utils.watcher import get_new_files

# Streamlit multipage: Don't call st.set_page_config() here


def add_file_with_quick_preview(file_path: Path):
    """Add file to session, using quick preview for large CSVs."""
    try:
        file_path = Path(file_path)
        stat = file_path.stat()
        size_mb = stat.st_size / (1024 * 1024)
        rows_threshold = config.get("ui.auto_sample_threshold_rows", 5000)
        large_mb = float(config.get("ui.large_file_mb", 50) or 50)
        if file_path.suffix.lower() == ".csv" and size_mb >= large_mb:
            # Quick head preview
            import chardet
            with open(file_path, 'rb') as f:
                enc = chardet.detect(f.read())['encoding'] or 'utf-8'
            df = pd.read_csv(
                file_path,
                encoding=enc,
                nrows=max(int(rows_threshold * 0.5), 1000),
                low_memory=False,
            )
            meta = get_file_metadata(file_path)
            if "data_files" not in st.session_state:
                st.session_state.data_files = {}
            st.session_state.data_files[file_path.name] = {
                "path": file_path,
                "df": df,
                "metadata": meta,
                "hash": None,
                "partial": True,
                "full_loaded": False,
            }
        else:
            # Normal full load
            load_file_to_session(file_path)
    except Exception as e:
        st.warning(f"Failed to add file {file_path.name}: {e}")


def load_from_input_dir(input_dir: Path):
    """
    Load supported data files from the given input directory into session state.
    """
    supported_exts = {".csv", ".json", ".xlsx", ".xls", ".txt", ".xml", ".parquet", ".feather"}
    if "data_files" not in st.session_state:
        st.session_state.data_files = {}
    count = 0
    if input_dir.exists() and input_dir.is_dir():
        for p in sorted(input_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in supported_exts:
                try:
                    add_file_with_quick_preview(p)
                    count += 1
                except Exception:
                    continue
    return count


def process_uploaded_files(uploaded_files):
    """Process uploaded files and add to session state."""
    if "data_files" not in st.session_state:
        st.session_state.data_files = {}
    request_id = generate_request_id()
    temp_dir = Path("temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    for uploaded_file in uploaded_files:
        try:
            temp_path = temp_dir / uploaded_file.name
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            add_file_with_quick_preview(temp_path)
        except Exception as e:
            st.warning(f"Failed to load {uploaded_file.name}: {e}")


def preview_dataframe(df: pd.DataFrame, key: str):
    """Thin wrapper around standard table renderer for consistency."""
    render_data_table(df, max_rows=1000, key=f"table_{key}")


def display_file_statistics():
    """Show high-level statistics for all loaded files."""
    if not st.session_state.data_files:
        return

    rows: List[Dict[str, object]] = []
    for name, info in st.session_state.data_files.items():
        path: Path = info.get("path")
        df: Optional[pd.DataFrame] = info.get("df")
        meta: Optional[Dict[str, object]] = info.get("metadata")

        # Prefer stored metadata; fall back to DataFrame shape
        if meta is None and path is not None:
            try:
                meta = get_file_metadata(path)
                info["metadata"] = meta
            except Exception:
                meta = {}

        rows.append(
            {
                "File": name,
                "Rows": meta.get("rows") if meta else (len(df) if df is not None else None),
                "Columns": meta.get("columns") if meta else (len(df.columns) if df is not None else None),
                "Size (MB)": round(float(meta.get("file_size_mb", 0.0)), 2) if meta else None,
                "Type": Path(name).suffix.lower() or (meta.get("extension") if meta else ""),
                "Partial": bool(info.get("partial", False)),
                "Full Loaded": bool(info.get("full_loaded", True)),
            }
        )

    stats_df = pd.DataFrame(rows)
    st.markdown("#### File Summary")
    render_data_table(stats_df, max_rows=1000, key="file_stats")


def display_file_analysis(file_name: str, index: int):
    """Render detailed analysis panel for a single file."""
    info = st.session_state.data_files.get(file_name)
    if not info:
        st.warning(f"File not found in session: {file_name}")
        return

    df: Optional[pd.DataFrame] = info.get("df")
    meta: Optional[Dict[str, object]] = info.get("metadata")
    path: Optional[Path] = info.get("path")

    if meta is None and path is not None:
        try:
            meta = get_file_metadata(path)
            info["metadata"] = meta
        except Exception:
            meta = {}

    container = st.container()
    with container:
        st.markdown(f"#### 📁 {file_name}")

        cols = st.columns([2, 1])
        with cols[0]:
            if df is not None:
                st.markdown("**Data Preview**")
                preview_dataframe(df.head(1000), key=f"analysis_preview_{index}")
            else:
                st.info("No DataFrame loaded for this file yet.")

        with cols[1]:
            if meta:
                render_metadata_summary(meta, show_details=False)
            if info.get("partial", False) and not info.get("full_loaded", False) and path is not None:
                if st.button("⬇️ Load full file", key=f"load_full_{index}"):
                    try:
                        load_file_to_session(path)
                        st.success("Full file loaded")
                    except Exception as e:
                        st.error(f"Failed to load full file: {e}")

        # Optional simple numeric distribution plot
        if df is not None and px is not None:
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if numeric_cols:
                with st.expander("📊 Quick numeric summary", expanded=False):
                    col = st.selectbox(
                        "Numeric column",
                        numeric_cols,
                        key=f"numeric_summary_{index}",
                    )
                    try:
                        fig = px.histogram(df, x=col, nbins=30, title=f"Distribution of {col}")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        st.info("Could not render chart for this column.")


# Initialize session state for data files
if "data_files" not in st.session_state:
    st.session_state.data_files = {}  # {file_name: {path: Path, df: DataFrame, metadata: dict}}

if "selected_files" not in st.session_state:
    st.session_state.selected_files = []

if "edits_staged" not in st.session_state:
    st.session_state.edits_staged = {}  # {file_name: edited_df}

# Initialize config and logger
config = get_config()
logger = get_logger()

# Render sidebar
render_sidebar()

# Page header
render_page_header(
    title="📊 Data File Handler",
    subtitle="Convert, clean, and manipulate data files"
)

# Quick Start instructions
render_quick_start([
    "Upload files using drag-and-drop or load from Input directory",
    "Select files to view and analyze (up to 3 at once)",
    "Edit, clean, or convert your data files",
    "Save results to Output directory (never overwrites originals)"
])

# Main content sections
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Upload & Analysis", 
    "✏️ Edit & Clean", 
    "🔄 Merge & Group", 
    "🔄 Convert", 
    "✂️ Split Files"
])

# ============================================
# TAB 1: Upload & Analysis
# ============================================
with tab1:
    st.markdown("### Upload Files")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Drag and drop data files here",
        type=['csv', 'json', 'xlsx', 'xls', 'txt', 'xml', 'parquet', 'feather'],
        accept_multiple_files=True,
        help="Supported formats: CSV, JSON, XLSX, XLS, TXT, XML, Parquet, Feather"
    )
    
    # Load from Input directory & detect new files
    col1, col2 = st.columns([3, 1])
    with col1:
        input_dir = Path(config.get("directories.input", "./input"))
        # Detect new files
        new_files = get_new_files(input_dir, [".csv", ".json", ".xlsx", ".xls", ".txt", ".xml", ".parquet", ".feather"], seen=None)
        if new_files:
            st.info(f"Detected {len(new_files)} file(s) in Input directory")
        auto_watch_default = bool(config.get("watchdog.enabled", True))
        auto_load = st.checkbox("Auto-load new files", value=auto_watch_default)
        if auto_load:
            # Periodic refresh every 10 seconds to detect new files
            try:
                st.experimental_rerun  # type: ignore
                from streamlit_autorefresh import st_autorefresh  # type: ignore
            except Exception:
                st.caption("Install streamlit-autorefresh for periodic checks: pip install streamlit-autorefresh")
            else:
                st_autorefresh(interval=10_000, key="auto_refresh_input")
        if auto_load and new_files:
            load_from_input_dir(input_dir)
        if st.button("📂 Load from Input Directory"):
            load_from_input_dir(input_dir)
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Process uploaded files
    if uploaded_files:
        process_uploaded_files(uploaded_files)
    
    # Display loaded files
    if st.session_state.data_files:
        st.markdown("---")
        st.markdown("### Loaded Files")
        
        # File selection (up to 3)
        file_names = list(st.session_state.data_files.keys())
        max_select = min(3, len(file_names))
        
        selected = st.multiselect(
            "Select files to view (up to 3)",
            file_names,
            default=st.session_state.selected_files[:max_select] if st.session_state.selected_files else file_names[:max_select],
            max_selections=max_select
        )
        
        st.session_state.selected_files = selected
        
        # Display file statistics table
        display_file_statistics()
        
        # Show selected files
        if selected:
            for i, file_name in enumerate(selected[:3]):  # Max 3
                display_file_analysis(file_name, i)
 
        st.markdown("---")
        st.markdown("### Output → Input Mover")
        out_dir = Path(config.get("directories.output", "./output"))
        in_dir = Path(config.get("directories.input", "./input"))
        if not out_dir.exists():
            st.info("Output directory not found")
        else:
            supported_exts = [".csv", ".json", ".xlsx", ".xls", ".txt", ".xml", ".parquet", ".feather"]
            out_files = [p for p in sorted(out_dir.iterdir()) if p.is_file() and p.suffix.lower() in supported_exts]
            if not out_files:
                st.caption("No compatible files in Output directory")
            else:
                choices = st.multiselect("Select files in Output to move to Input", [p.name for p in out_files])
                verify = st.checkbox("Verify copy before delete", value=True)
                if st.button("🚚 Move Selected to Input") and choices:
                    moved = 0
                    in_dir.mkdir(parents=True, exist_ok=True)
                    for name in choices:
                        src = out_dir / name
                        dest = in_dir / name
                        try:
                            # If conflict, append timestamped suffix
                            if dest.exists():
                                dest = in_dir / generate_timestamped_filename(Path(name).stem, src.suffix.lstrip('.'))
                            if move_file(src, dest, verify=verify):
                                moved += 1
                        except Exception as e:
                            st.warning(f"Failed to move {name}: {e}")
                    st.success(f"Moved {moved}/{len(choices)} file(s) to Input")
                    st.caption("Use 'Load from Input Directory' to load moved files into the app")
    
    else:
        st.info("👆 Upload files or click 'Load from Input Directory' to begin")


# ============================================
# TAB 2: Edit & Clean
# ============================================
with tab2:
    if not st.session_state.data_files:
        st.info("📤 Upload files in the 'Upload & Analysis' tab first")
    else:
        st.markdown("### Data Cleaning & Editing")
        
        # Select file to edit
        edit_file = st.selectbox(
            "Select file to edit",
            list(st.session_state.data_files.keys())
        )
        
        if edit_file:
            file_info = st.session_state.data_files[edit_file]
            df = file_info.get("df")
            
            if df is not None:
                # Data preview with auto-sampling
                st.markdown("#### Data Preview")
                preview_dataframe(df, key=f"preview_{edit_file}")
                
                # Editing section
                st.markdown("#### Edit Data")
                with st.expander("📝 Inline Editing", expanded=False):
                    edited_df = render_data_editor(
                        df.head(1000),  # Limit editing to 1000 rows for performance
                        num_rows="dynamic",
                        key=f"editor_{edit_file}"
                    )
                    
                    if st.button("💾 Save Edits", key=f"save_{edit_file}"):
                        if not edited_df.equals(df.head(1000)):
                            # Store edits
                            st.session_state.edits_staged[edit_file] = edited_df
                            st.success("Edits staged. Click 'Save As Copy' to save.")
                
                # Cleaning operations
                st.markdown("---")
                st.markdown("#### Data Cleaning Operations")
                
                cleaning_tab1, cleaning_tab2, cleaning_tab3, cleaning_tab4 = st.tabs([
                    "Remove", "Standardize", "Outliers", "Format"
                ])
                
                with cleaning_tab1:
                    handle_remove_operations(df, edit_file)
                
                with cleaning_tab2:
                    handle_standardization(df, edit_file)
                
                with cleaning_tab3:
                    handle_outlier_detection(df, edit_file)
                
                with cleaning_tab4:
                    handle_format_operations(df, edit_file)
                
                # Save button
                st.markdown("---")
                if st.button("💾 Save As Copy", key=f"save_copy_{edit_file}"):
                    save_edited_file(edit_file, df)


# ============================================
# TAB 3: Merge & Group
# ============================================
with tab3:
    if len(st.session_state.data_files) < 2:
        st.info("📤 Upload at least 2 files to use merge operations")
    else:
        merge_group_tab1, merge_group_tab2 = st.tabs(["🔄 Merge Tables", "📊 Group By"])
        
        with merge_group_tab1:
            handle_merge_operations()
        
        with merge_group_tab2:
            handle_group_by_operations()


# ============================================
# TAB 4: Convert
# ============================================
with tab4:
    if not st.session_state.data_files:
        st.info("📤 Upload files in the 'Upload & Analysis' tab first")
    else:
        handle_conversion_operations()


# ============================================
# TAB 5: Split Files
# ============================================
with tab5:
    if not st.session_state.data_files:
        st.info("📤 Upload files in the 'Upload & Analysis' tab first")
    else:
        handle_split_operations()


# ============================================
# Helper Functions
# ============================================


@st.cache_data
def load_file_to_session_cached(file_path: Path, file_hash: str) -> tuple[pd.DataFrame, dict]:
    """Cached file loader."""
    df = load_data_file(file_path)
    metadata = get_file_metadata(file_path)
    return df, metadata


def load_file_to_session(file_path: Path):
    """Load file into session state."""
    from src.app.utils.cache import get_file_hash
    
    file_name = file_path.name
    file_hash = get_file_hash(file_path)
    
    # Check if already loaded
    if file_name in st.session_state.data_files:
        # Check if file changed
        if check_file_changed(str(file_path)):
            st.info(f"File changed: {file_name}. Reloading...")
        else:
            return  # Already loaded and unchanged
    
    # Load file
    try:
        df, metadata = load_file_to_session_cached(file_path, file_hash)
        
        # Store in session state
        st.session_state.data_files[file_name] = {
            "path": file_path,
            "df": df,
            "metadata": metadata,
            "hash": file_hash,
            "partial": False,
            "full_loaded": True
        }
        
        # Track file hash
        track_file_hash(str(file_path), file_hash)
        
    except Exception as e:
        raise OperationalError(
            f"Failed to load file: {e}",
            user_message=f"Could not load file: {file_name}",
            suggestion="Check file format and encoding"
        ) from e


def handle_remove_operations(df: pd.DataFrame, file_name: str):
    """Handle remove operations (empty rows/columns, duplicates, characters)."""
    st.markdown("##### Remove Operations")
    remove_col1, remove_col2 = st.columns(2)
    with remove_col1:
        if st.button("🗑️ Remove Empty Rows/Columns", key=f"remove_empty_{file_name}"):
            cleaned_df, rows_removed, cols_removed = remove_empty_rows_columns(df)
            st.success(f"Removed {rows_removed} empty rows and {cols_removed} empty columns")
            st.session_state.edits_staged[file_name] = cleaned_df
    with remove_col2:
        cols_for_dedup = st.multiselect(
            "Columns for duplicate check",
            df.columns.tolist(),
            key=f"dedup_cols_{file_name}"
        )
        if cols_for_dedup and st.button("🗑️ Remove Duplicates", key=f"remove_dup_{file_name}"):
            cleaned_df, dup_count = remove_duplicates(df, cols_for_dedup)
            st.success(f"Removed {dup_count} duplicate rows")
            st.session_state.edits_staged[file_name] = cleaned_df
    st.markdown("---")
    st.markdown("##### Remove Characters")
    char_cols = st.multiselect("Select columns", df.columns.tolist(), key=f"char_cols_{file_name}")
    chars_to_remove = st.text_input("Characters to remove (comma or space separated)", key=f"chars_{file_name}")
    use_regex = st.checkbox("Use regex", key=f"regex_{file_name}")
    if char_cols and chars_to_remove and st.button("🗑️ Remove Characters", key=f"remove_chars_{file_name}"):
        cleaned_df = remove_characters(df, char_cols, chars_to_remove, use_regex)
        st.session_state.edits_staged[file_name] = cleaned_df
        st.success("Characters removed")

def handle_standardization(df: pd.DataFrame, file_name: str):
    """Handle standardization (phone numbers, URLs, whitespace)."""
    st.markdown("##### Standardize Data")
    st.markdown("**Phone Numbers**")
    phone_col = st.selectbox("Select column", [None] + df.columns.tolist(), key=f"phone_col_{file_name}")
    phone_format = st.selectbox(
        "Format",
        ["E.164", "National", "International", "Dashed"],
        key=f"phone_fmt_{file_name}"
    )
    if phone_col and st.button("📱 Standardize Phone", key=f"phone_{file_name}"):
        try:
            cleaned_df = standardize_phone_numbers(df, phone_col, phone_format)
            st.session_state.edits_staged[file_name] = cleaned_df
            st.success(f"Phone numbers standardized (new column: {phone_col}_formatted)")
        except Exception as e:
            st.error(f"Phone standardization failed: {e}")
    st.markdown("---")
    st.markdown("**URLs**")
    url_col = st.selectbox("Select column", [None] + df.columns.tolist(), key=f"url_col_{file_name}")
    if url_col:
        url_base_only = st.checkbox("Base domain only", key=f"url_base_{file_name}")
        url_include_protocol = st.checkbox("Include protocol", value=True, key=f"url_proto_{file_name}")
        url_include_path = st.checkbox("Include path", value=True, key=f"url_path_{file_name}")
        if st.button("🔗 Standardize URL", key=f"url_{file_name}"):
            cleaned_df = standardize_urls(
                df, url_col,
                include_protocol=url_include_protocol,
                include_path=url_include_path,
                base_domain_only=url_base_only
            )
            st.session_state.edits_staged[file_name] = cleaned_df
            st.success(f"URLs standardized (new column: {url_col}_formatted)")
    st.markdown("---")
    trim_cols = st.multiselect("Columns to trim", df.columns.tolist(), key=f"trim_cols_{file_name}")
    if trim_cols and st.button("✂️ Trim Whitespace", key=f"trim_{file_name}"):
        cleaned_df = trim_whitespace(df, trim_cols)
        st.session_state.edits_staged[file_name] = cleaned_df
        st.success("Whitespace trimmed")

def handle_outlier_detection(df: pd.DataFrame, file_name: str):
    """Handle outlier detection with configurable thresholds."""
    st.markdown("##### Detect Outliers")
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if not numeric_cols:
        st.info("No numeric columns found")
        return
    outlier_cols = st.multiselect("Select columns", numeric_cols, key=f"outlier_cols_{file_name}")
    method = st.selectbox("Method", ["zscore", "iqr"], key=f"outlier_method_{file_name}")
    default_threshold = 3.0 if method == "zscore" else 1.5
    threshold = st.slider(
        "Threshold",
        min_value=0.1,
        max_value=10.0,
        value=default_threshold,
        step=0.1,
        key=f"outlier_thresh_{file_name}"
    )
    if outlier_cols and st.button("🔍 Detect Outliers", key=f"detect_outliers_{file_name}"):
        result_df = detect_outliers(df, outlier_cols, method, threshold)
        outlier_flags = [f"{col}_outlier" for col in outlier_cols]
        total_outliers = result_df[outlier_flags].any(axis=1).sum()
        if total_outliers > 0:
            st.warning(f"Found {total_outliers} rows with outliers")
            outlier_rows = result_df[result_df[outlier_flags].any(axis=1)]
            st.dataframe(outlier_rows, use_container_width=True)
            action = st.radio(
                "Action",
                ["Keep as is", "Delete outlier rows", "Show for manual review"],
                key=f"outlier_action_{file_name}"
            )
            if action == "Delete outlier rows":
                result_df = result_df[~result_df[outlier_flags].any(axis=1)]
                result_df = result_df.drop(columns=outlier_flags)
                st.session_state.edits_staged[file_name] = result_df
                st.success("Outlier rows deleted")
        else:
            st.success("No outliers detected")

def handle_format_operations(df: pd.DataFrame, file_name: str):
    """Handle format operations (decimal places, missing values)."""
    st.markdown("##### Format & Missing Values")
    st.markdown("**Handle Missing Values**")
    missing_cols = st.multiselect("Select columns", df.columns.tolist(), key=f"missing_cols_{file_name}")
    missing_strategy = st.selectbox(
        "Strategy",
        ["fill_na", "forward_fill", "backward_fill", "mean", "median", "drop"],
        key=f"missing_strat_{file_name}"
    )
    fill_value = None
    if missing_strategy == "fill_na":
        fill_value = st.text_input("Fill value", value="N/A", key=f"fill_val_{file_name}")
    if missing_cols and st.button("🔧 Handle Missing", key=f"missing_{file_name}"):
        cleaned_df = handle_missing_values(df, missing_cols, missing_strategy, fill_value)
        st.session_state.edits_staged[file_name] = cleaned_df
        st.success("Missing values handled")
    st.markdown("---")
    st.markdown("**Numeric Format**")
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if numeric_cols:
        format_col = st.selectbox("Select column", [None] + numeric_cols, key=f"format_col_{file_name}")
        if format_col:
            decimal_places = st.number_input("Decimal places", min_value=0, max_value=10, value=2, key=f"decimals_{file_name}")
            use_scientific = st.checkbox("Scientific notation", key=f"sci_{file_name}")
            if st.button("🔧 Format Number", key=f"format_num_{file_name}"):
                cleaned_df = standardize_format(df, format_col, decimal_places, use_scientific)
                st.session_state.edits_staged[file_name] = cleaned_df
                st.success("Number format updated")


def save_edited_file(file_name: str, original_df: pd.DataFrame):
    """Save edited file to Output directory."""
    output_dir = Path(config.get("directories.output", "./output"))
    edited_df = st.session_state.edits_staged.get(file_name, original_df)
    file_info = st.session_state.data_files[file_name]
    original_path = file_info["path"]
    extension = original_path.suffix.lstrip('.')
    try:
        output_file = save_data_file(edited_df, output_dir, extension)
        st.success(f"✅ Saved: {output_file.name}")
        if file_name in st.session_state.edits_staged:
            del st.session_state.edits_staged[file_name]
    except Exception as e:
        st.error(f"Save failed: {e}")


def convert_single_file(file_path: Path, from_format: str, to_format: str, output_dir: Path):
    """Convert single file to target format."""
    output_file = ConversionRegistry.convert_file(file_path, from_format, to_format, output_dir)
    return output_file


def convert_all_files(target_format: str, output_dir: Path):
    """Convert all loaded files to target format with progress."""
    from src.app.utils.progress import ProgressEstimator, show_progress_bar
    files_to_convert = list(st.session_state.data_files.keys())
    total = len(files_to_convert)
    estimator = ProgressEstimator()
    estimator.start()
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    successful = 0
    failed = []
    for i, file_name in enumerate(files_to_convert):
        file_info = st.session_state.data_files[file_name]
        file_path = file_info["path"]
        from_format = file_path.suffix.lstrip('.')
        try:
            ConversionRegistry.convert_file(file_path, from_format, target_format, output_dir)
            successful += 1
        except Exception as e:
            failed.append((file_name, str(e)))
        with progress_placeholder.container():
            show_progress_bar(i + 1, total, estimator, key="convert_progress")
        status_placeholder.text(f"Converting {i + 1}/{total}: {file_name}")
        time.sleep(0.1)
    progress_placeholder.empty()
    status_placeholder.empty()
    if successful > 0:
        st.success(f"✅ Converted {successful}/{total} files to {target_format}")
    if failed:
        st.warning(f"⚠️ Failed to convert {len(failed)} files:")
        for file_name, error in failed:
            st.error(f"  - {file_name}: {error}")


def convert_and_combine_files(target_format: str, output_dir: Path):
    """Combine all files and convert to target format."""
    try:
        formats = [Path(info["path"]).suffix.lstrip('.') for info in st.session_state.data_files.values()]
        if len(set(formats)) > 1:
            st.warning("Files are different formats. Converting individually instead.")
            convert_all_files(target_format, output_dir)
            return
        combined_dfs = []
        for _, file_info in st.session_state.data_files.items():
            df = file_info["df"]
            combined_dfs.append(df)
        combined_df = pd.concat(combined_dfs, ignore_index=True)
        output_file = save_data_file(combined_df, output_dir, target_format)
        st.success(f"✅ Combined and converted: {output_file.name} ({len(combined_df):,} rows)")
    except Exception as e:
        st.error(f"Combine and convert failed: {e}")


def save_merged_result(merged_df: pd.DataFrame, file1: str, file2: str):
    """Save merged result to Output directory."""
    output_dir = Path(config.get("directories.output", "./output"))
    output_file = save_data_file(merged_df, output_dir, "xlsx")
    st.success(f"✅ Saved merged result: {output_file.name}")


def save_grouped_result(grouped_df: pd.DataFrame, source_file: str):
    """Save grouped result to Output directory."""
    output_dir = Path(config.get("directories.output", "./output"))
    output_file = save_data_file(grouped_df, output_dir, "xlsx")
    st.success(f"✅ Saved grouped result: {output_file.name}")


def handle_merge_operations():
    """Handle merge operations between two data files."""
    st.markdown("##### Merge Two Tables")
    
    file_names = list(st.session_state.data_files.keys())
    if len(file_names) < 2:
        st.info("Upload at least 2 files to merge")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        file1_name = st.selectbox("First file (left)", file_names, key="merge_file1")
    with col2:
        file2_options = [f for f in file_names if f != file1_name]
        file2_name = st.selectbox("Second file (right)", file2_options if file2_options else file_names, key="merge_file2")
    
    if not file1_name or not file2_name:
        return
    
    file1_info = st.session_state.data_files[file1_name]
    file2_info = st.session_state.data_files[file2_name]
    df1 = file1_info.get("df")
    df2 = file2_info.get("df")
    
    if df1 is None or df2 is None:
        st.error("Could not load DataFrames for selected files")
        return
    
    st.markdown("**Merge Configuration**")
    
    # Find common columns
    common_cols = [c for c in df1.columns if c in df2.columns]
    if not common_cols:
        st.warning("No common columns found between files. Cannot merge.")
        return
    
    # Select join keys
    on_columns = st.multiselect(
        "Join on columns (select one or more)",
        common_cols,
        default=common_cols[0] if common_cols else None,
        key="merge_on"
    )
    
    if not on_columns:
        st.warning("Please select at least one join column")
        return
    
    # Join type
    how = st.selectbox(
        "Join type",
        ["inner", "left", "right", "outer"],
        index=0,
        key="merge_how"
    )
    
    # Similarity matching option
    use_similarity = st.checkbox("Enable fuzzy matching (for text columns)", value=False, key="merge_similarity")
    similarity_threshold = 0.8
    similarity_columns = None
    
    if use_similarity:
        similarity_threshold = st.slider(
            "Similarity threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.05,
            key="merge_sim_thresh"
        )
        similarity_columns = st.multiselect(
            "Columns for similarity matching",
            on_columns,
            default=on_columns if len(on_columns) == 1 else [],
            key="merge_sim_cols"
        )
        if not similarity_columns:
            similarity_columns = on_columns
    
    if st.button("🔄 Merge Tables", key="merge_execute"):
        try:
            merged_df = merge_dataframes(
                df1, df2,
                on=on_columns[0] if len(on_columns) == 1 else on_columns,
                how=how,
                similarity_threshold=similarity_threshold,
                use_similarity=use_similarity,
                similarity_columns=similarity_columns
            )
            
            st.success(f"Merged successfully! Result: {len(merged_df):,} rows × {len(merged_df.columns)} columns")
            
            # Preview merged result
            st.markdown("**Preview Merged Result**")
            preview_dataframe(merged_df.head(100), key="merge_preview")
            
            # Save option
            st.markdown("---")
            if st.button("💾 Save Merged Result", key="save_merged"):
                save_merged_result(merged_df, file1_name, file2_name)
        
        except Exception as e:
            st.error(f"Merge failed: {e}")


def handle_group_by_operations():
    """Handle group-by operations on a data file."""
    st.markdown("##### Group By & Aggregate")
    
    file_names = list(st.session_state.data_files.keys())
    if not file_names:
        st.info("Upload at least one file")
        return
    
    source_file = st.selectbox("Select file", file_names, key="group_file")
    
    if not source_file:
        return
    
    file_info = st.session_state.data_files[source_file]
    df = file_info.get("df")
    
    if df is None:
        st.error("Could not load DataFrame for selected file")
        return
    
    st.markdown("**Group By Configuration**")
    
    # Select group-by columns
    group_by_cols = st.multiselect(
        "Group by columns",
        df.columns.tolist(),
        key="group_by_cols"
    )
    
    if not group_by_cols:
        st.warning("Please select at least one group-by column")
        return
    
    st.markdown("**Aggregations**")
    st.caption("Select columns and aggregation functions")
    
    # Build aggregation dictionary
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    text_cols = [c for c in df.columns if c not in numeric_cols and c not in group_by_cols]
    
    aggregations = {}
    
    if numeric_cols:
        st.markdown("**Numeric Columns**")
        selected_numeric = st.multiselect(
            "Select numeric columns",
            numeric_cols,
            key="group_numeric_cols"
        )
        
        if selected_numeric:
            agg_functions = st.multiselect(
                "Aggregation functions",
                ["count", "sum", "mean", "min", "max", "median", "std", "nunique"],
                default=["count", "mean"],
                key="group_numeric_funcs"
            )
            
            if agg_functions:
                for col in selected_numeric:
                    aggregations[col] = agg_functions
    
    if text_cols:
        st.markdown("**Text Columns**")
        selected_text = st.multiselect(
            "Select text columns",
            text_cols,
            key="group_text_cols"
        )
        
        if selected_text:
            agg_functions = st.multiselect(
                "Aggregation functions",
                ["count", "first", "last", "nunique"],
                default=["count"],
                key="group_text_funcs"
            )
            
            if agg_functions:
                for col in selected_text:
                    aggregations[col] = agg_functions
    
    if not aggregations:
        st.warning("Please select at least one column to aggregate")
        return
    
    if st.button("📊 Group By & Aggregate", key="group_execute"):
        try:
            grouped_df = group_by_dataframe(df, group_by_cols, aggregations)
            
            st.success(f"Grouped successfully! Result: {len(grouped_df):,} groups × {len(grouped_df.columns)} columns")
            
            # Preview grouped result
            st.markdown("**Preview Grouped Result**")
            preview_dataframe(grouped_df, key="group_preview")
            
            # Save option
            st.markdown("---")
            if st.button("💾 Save Grouped Result", key="save_grouped"):
                save_grouped_result(grouped_df, source_file)
        
        except Exception as e:
            st.error(f"Group by failed: {e}")


def handle_conversion_operations():
    """Handle file format conversion operations."""
    st.markdown("##### Convert File Formats")
    
    file_names = list(st.session_state.data_files.keys())
    if not file_names:
        st.info("Upload files first")
        return
    
    # File selection
    selected_files = st.multiselect(
        "Select files to convert",
        file_names,
        default=file_names[:min(5, len(file_names))],
        key="convert_files"
    )
    
    if not selected_files:
        st.warning("Please select at least one file")
        return
    
    # Target format
    target_format = st.selectbox(
        "Target format",
        ["csv", "json", "xlsx", "parquet", "feather", "txt", "xml"],
        index=0,
        key="convert_target"
    )
    
    # Conversion mode
    conversion_mode = st.radio(
        "Conversion mode",
        ["Convert individually", "Combine and convert"],
        index=0,
        key="convert_mode"
    )
    
    output_dir = Path(config.get("directories.output", "./output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if st.button("🔄 Convert Files", key="convert_execute"):
        try:
            if conversion_mode == "Combine and convert":
                # Temporarily store selected files
                original_files = st.session_state.data_files.copy()
                st.session_state.data_files = {k: v for k, v in original_files.items() if k in selected_files}
                
                convert_and_combine_files(target_format, output_dir)
                
                # Restore original files
                st.session_state.data_files = original_files
            else:
                # Convert individually with progress
                from src.app.utils.progress import ProgressEstimator, show_progress_bar
                
                total = len(selected_files)
                estimator = ProgressEstimator()
                estimator.start()
                
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                
                successful = 0
                failed = []
                
                for i, file_name in enumerate(selected_files):
                    file_info = st.session_state.data_files[file_name]
                    file_path = file_info["path"]
                    from_format = file_path.suffix.lstrip('.')
                    
                    try:
                        ConversionRegistry.convert_file(file_path, from_format, target_format, output_dir)
                        successful += 1
                    except Exception as e:
                        failed.append((file_name, str(e)))
                    
                    # Update progress
                    with progress_placeholder.container():
                        show_progress_bar(i + 1, total, estimator, key="convert_progress")
                    status_placeholder.text(f"Converting {i + 1}/{total}: {file_name}")
                    time.sleep(0.05)  # Small delay for UI update
                
                progress_placeholder.empty()
                status_placeholder.empty()
                
                if successful > 0:
                    st.success(f"✅ Converted {successful}/{total} file(s) to {target_format.upper()}")
                
                if failed:
                    st.warning(f"⚠️ Failed to convert {len(failed)} file(s):")
                    for file_name, error in failed:
                        st.error(f"  - {file_name}: {error}")
        
        except Exception as e:
            st.error(f"Conversion failed: {e}")


def handle_split_operations():
    """Handle file splitting operations."""
    st.markdown("##### Split Large Files")
    
    file_names = list(st.session_state.data_files.keys())
    if not file_names:
        st.info("Upload files first")
        return
    
    # File selection
    source_file = st.selectbox(
        "Select file to split",
        file_names,
        key="split_file"
    )
    
    if not source_file:
        return
    
    file_info = st.session_state.data_files[source_file]
    file_path = file_info.get("path")
    df = file_info.get("df")
    
    if df is None or file_path is None:
        st.error("Could not load file for splitting")
        return
    
    # Show file info
    st.info(f"File: {source_file} | Rows: {len(df):,} | Columns: {len(df.columns)}")
    
    # Split method
    split_method = st.radio(
        "Split method",
        ["By row count", "By file size (MB)"],
        index=0,
        key="split_method"
    )
    
    if split_method == "By row count":
        target_rows = st.number_input(
            "Rows per file",
            min_value=1,
            max_value=len(df),
            value=min(10000, len(df) // 2) if len(df) > 10000 else len(df) // 2,
            key="split_rows"
        )
        target_size_mb = None
    else:
        target_size_mb = st.number_input(
            "Target file size (MB)",
            min_value=0.1,
            max_value=1000.0,
            value=50.0,
            step=0.1,
            key="split_size"
        )
        target_rows = None
    
    # Optional zip
    create_zip = st.checkbox("Create ZIP archive of split files", value=False, key="split_zip")
    
    output_dir = Path(config.get("directories.output", "./output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if st.button("✂️ Split File", key="split_execute"):
        try:
            method_str = "rows" if split_method == "By row count" else "size"
            
            output_files, zip_path = split_data_file(
                file_path,
                split_method=method_str,
                target_size_mb=target_size_mb,
                target_rows=target_rows,
                output_dir=output_dir,
                create_zip=create_zip
            )
            
            if output_files:
                st.success(f"✅ Split into {len(output_files)} file(s)")
                
                # Show output files
                with st.expander("📂 View split files", expanded=False):
                    for i, out_file in enumerate(output_files, 1):
                        st.text(f"{i}. {out_file.name}")
                
                if zip_path and zip_path.exists():
                    st.success(f"📦 ZIP archive created: {zip_path.name}")
            
        except Exception as e:
            st.error(f"Split failed: {e}")