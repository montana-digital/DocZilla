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

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.app.components.layout import render_page_header, render_sidebar, render_quick_start
from src.app.components.tables import render_data_table, render_data_editor
from src.app.components.metadata_panel import render_file_metadata, render_multiple_file_metadata
from src.app.utils.config import get_config
from src.app.utils.cache import check_file_changed, track_file_hash, cache_file_operation
from src.app.utils.logging import get_logger, generate_request_id
from src.app.utils.exceptions import OperationalError
from src.app.services.file_io import (
    load_data_file, save_data_file, get_file_metadata, 
    move_file, generate_timestamped_filename
)
from src.app.services.data_ops import (
    merge_dataframes, group_by_dataframe, detect_outliers,
    remove_empty_rows_columns, handle_missing_values, remove_duplicates,
    standardize_phone_numbers, standardize_urls, remove_characters,
    trim_whitespace, standardize_format
)
from src.app.services.conversions import ConversionRegistry
from src.app.services.fragments import split_data_file

# Streamlit multipage: Don't call st.set_page_config() here

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
    
    # Load from Input directory button
    col1, col2 = st.columns([3, 1])
    with col1:
        input_dir = Path(config.get("directories.input", "./input"))
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

def load_from_input_dir(input_dir: Path):
    """Load compatible files from Input directory."""
    if not input_dir.exists():
        st.error(f"Input directory not found: {input_dir}")
        return
    
    compatible_extensions = ['.csv', '.json', '.xlsx', '.xls', '.txt', '.xml', '.parquet', '.feather']
    files_found = []
    
    for ext in compatible_extensions:
        files_found.extend(list(input_dir.glob(f"*{ext}")))
        files_found.extend(list(input_dir.glob(f"*{ext.upper()}")))
    
    if files_found:
        st.info(f"Found {len(files_found)} compatible file(s) in Input directory")
        
        # Process each file
        for file_path in files_found:
            try:
                load_file_to_session(file_path)
            except Exception as e:
                st.error(f"Failed to load {file_path.name}: {e}")
    else:
        st.info("No compatible files found in Input directory")


def process_uploaded_files(uploaded_files):
    """Process uploaded files and add to session state."""
    request_id = generate_request_id()
    
    for uploaded_file in uploaded_files:
        try:
            # Save to temp file first
            temp_path = Path("temp") / uploaded_file.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Load file
            load_file_to_session(temp_path)
            
            logger.log(
                level="INFO",
                message=f"File uploaded: {uploaded_file.name}",
                module=__name__,
                request_id=request_id,
                operation="file_upload",
                file_path=str(temp_path),
                status="success"
            )
            
            st.success(f"✅ Loaded: {uploaded_file.name}")
            
        except Exception as e:
            st.error(f"❌ Failed to load {uploaded_file.name}: {e}")
            logger.log(
                level="ERROR",
                message=f"Upload failed: {uploaded_file.name} - {e}",
                module=__name__,
                request_id=request_id,
                operation="file_upload",
                file_path=uploaded_file.name,
                status="failure",
                error_details=str(e)
            )


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
            "hash": file_hash
        }
        
        # Track file hash
        track_file_hash(str(file_path), file_hash)
        
    except Exception as e:
        raise OperationalError(
            f"Failed to load file: {e}",
            user_message=f"Could not load file: {file_name}",
            suggestion="Check file format and encoding"
        ) from e


def display_file_statistics():
    """Display statistics table for all loaded files."""
    files_data = []
    
    for file_name, file_info in st.session_state.data_files.items():
        metadata = file_info.get("metadata", {})
        df = file_info.get("df")
        
        files_data.append({
            "File": file_name,
            "Size (MB)": f"{metadata.get('file_size_mb', 0):.2f}",
            "Rows": f"{metadata.get('rows', 0):,}",
            "Columns": metadata.get("columns", 0),
            "Status": "✅ Valid" if df is not None else "❌ Error"
        })
    
    if files_data:
        stats_df = pd.DataFrame(files_data)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)


@st.fragment
def display_file_analysis(file_name: str, index: int):
    """Display file analysis in fragment (prevents rerun)."""
    file_info = st.session_state.data_files[file_name]
    df = file_info.get("df")
    metadata = file_info.get("metadata", {})
    
    if df is None:
        st.error(f"Could not load {file_name}")
        return
    
    with st.container():
        st.markdown(f"#### File {index + 1}: {file_name}")
        
        # File stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rows", f"{len(df):,}")
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            st.metric("Size", f"{metadata.get('file_size_mb', 0):.2f} MB")
        with col4:
            missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100)
            st.metric("Missing", f"{missing_pct:.1f}%")
        
        # Metadata toggle
        if st.checkbox(f"Show metadata", key=f"meta_{file_name}"):
            render_file_metadata(metadata, title=f"Metadata: {file_name}")
        
        # Data preview
        st.markdown("##### Data Preview")
        preview_dataframe(df, key=f"file_{index}")


def preview_dataframe(df: pd.DataFrame, key: str):
    """Display DataFrame preview with auto-sampling."""
    rows_threshold = config.get("ui.auto_sample_threshold_rows", 5000)
    cols_threshold = config.get("ui.auto_sample_threshold_cols", 100)
    preview_pct = config.get("ui.preview_percentage", 10) / 100
    
    rows = len(df)
    cols = len(df.columns)
    
    # Check if auto-sampling needed
    if rows > rows_threshold or cols > cols_threshold:
        st.info(f"⚠️ Large dataset detected ({rows:,} rows, {cols} columns). Showing {preview_pct*100:.0f}% preview.")
        
        preview_rows = max(int(rows * preview_pct), 100)
        
        # Slider to adjust preview
        slider_rows = st.slider(
            "Preview rows",
            min_value=100,
            max_value=min(rows, 10000),
            value=preview_rows,
            step=100,
            key=f"preview_rows_{key}"
        )
        
        render_data_table(df.head(slider_rows), max_rows=slider_rows, key=f"table_{key}")
    else:
        render_data_table(df, max_rows=1000, key=f"table_{key}")


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
        # Remove duplicates
        cols_for_dedup = st.multiselect(
            "Columns for duplicate check",
            df.columns.tolist(),
            key=f"dedup_cols_{file_name}"
        )
        if cols_for_dedup and st.button("🗑️ Remove Duplicates", key=f"remove_dup_{file_name}"):
            cleaned_df, dup_count = remove_duplicates(df, cols_for_dedup)
            st.success(f"Removed {dup_count} duplicate rows")
            st.session_state.edits_staged[file_name] = cleaned_df
    
    # Remove characters
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
    
    # Phone number standardization
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
    
    # URL standardization
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
    
    # Trim whitespace
    st.markdown("---")
    trim_cols = st.multiselect("Columns to trim", df.columns.tolist(), key=f"trim_cols_{file_name}")
    if trim_cols and st.button("✂️ Trim Whitespace", key=f"trim_{file_name}"):
        cleaned_df = trim_whitespace(df, trim_cols)
        st.session_state.edits_staged[file_name] = cleaned_df
        st.success("Whitespace trimmed")


def handle_outlier_detection(df: pd.DataFrame, file_name: str):
    """Handle outlier detection with configurable thresholds."""
    st.markdown("##### Detect Outliers")
    
    # Select numeric columns
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_cols:
        st.info("No numeric columns found")
        return
    
    outlier_cols = st.multiselect("Select columns", numeric_cols, key=f"outlier_cols_{file_name}")
    method = st.selectbox("Method", ["zscore", "iqr"], key=f"outlier_method_{file_name}")
    
    # Threshold slider
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
        
        # Count outliers
        outlier_flags = [f"{col}_outlier" for col in outlier_cols]
        total_outliers = result_df[outlier_flags].any(axis=1).sum()
        
        if total_outliers > 0:
            st.warning(f"Found {total_outliers} rows with outliers")
            
            # Show outlier rows
            outlier_rows = result_df[result_df[outlier_flags].any(axis=1)]
            st.dataframe(outlier_rows, use_container_width=True)
            
            # Options: delete, edit, keep
            action = st.radio(
                "Action",
                ["Keep as is", "Delete outlier rows", "Show for manual review"],
                key=f"outlier_action_{file_name}"
            )
            
            if action == "Delete outlier rows":
                result_df = result_df[~result_df[outlier_flags].any(axis=1)]
                # Remove outlier flag columns
                result_df = result_df.drop(columns=outlier_flags)
                st.session_state.edits_staged[file_name] = result_df
                st.success("Outlier rows deleted")
        else:
            st.success("No outliers detected")


def handle_format_operations(df: pd.DataFrame, file_name: str):
    """Handle format operations (decimal places, missing values)."""
    st.markdown("##### Format & Missing Values")
    
    # Missing values
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
    
    # Format numeric columns
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


def handle_merge_operations():
    """Handle merge operations with similarity matching."""
    st.markdown("### Merge Tables")
    
    if len(st.session_state.data_files) < 2:
        st.warning("Need at least 2 files to merge")
        return
    
    file_names = list(st.session_state.data_files.keys())
    
    merge_col1, merge_col2 = st.columns(2)
    
    with merge_col1:
        file1 = st.selectbox("First DataFrame", file_names, key="merge_file1")
        df1 = st.session_state.data_files[file1]["df"]
        col1 = st.selectbox("Merge column (DF1)", df1.columns.tolist(), key="merge_col1")
    
    with merge_col2:
        file2 = st.selectbox("Second DataFrame", [f for f in file_names if f != file1], key="merge_file2")
        df2 = st.session_state.data_files[file2]["df"]
        col2 = st.selectbox("Merge column (DF2)", df2.columns.tolist(), key="merge_col2")
    
    # Merge options
    join_type = st.selectbox("Join type", ["inner", "outer", "left", "right"], key="join_type")
    use_similarity = st.checkbox("Enable similarity matching (80% threshold)", key="use_sim")
    
    if use_similarity:
        similarity_cols = st.multiselect(
            "Columns for similarity matching",
            [col1, col2],
            default=[col1],
            key="sim_cols"
        )
    else:
        similarity_cols = None
    
    # Column selection
    st.markdown("**Select columns to include**")
    all_cols_df1 = {f"{file1}_{col}": col for col in df1.columns}
    all_cols_df2 = {f"{file2}_{col}": col for col in df2.columns}
    
    selected_cols_df1 = st.multiselect(f"Columns from {file1}", list(all_cols_df1.keys()), default=list(all_cols_df1.keys())[:3])
    selected_cols_df2 = st.multiselect(f"Columns from {file2}", list(all_cols_df2.keys()), default=list(all_cols_df2.keys())[:3])
    
    if st.button("🔄 Merge", key="merge_btn"):
        try:
            # Prepare dataframes with selected columns
            df1_selected = df1[[col1] + [all_cols_df1[k] for k in selected_cols_df1 if k in all_cols_df1]].copy()
            df2_selected = df2[[col2] + [all_cols_df2[k] for k in selected_cols_df2 if k in all_cols_df2]].copy()
            
            # Rename merge columns to match
            df2_selected = df2_selected.rename(columns={col2: col1})
            
            # Perform merge
            merged_df = merge_dataframes(
                df1_selected, df2_selected,
                on=col1,
                how=join_type,
                use_similarity=use_similarity,
                similarity_columns=similarity_cols if use_similarity else None
            )
            
            st.success(f"✅ Merged successfully: {len(merged_df)} rows")
            st.dataframe(merged_df, use_container_width=True)
            
            # Save option
            if st.button("💾 Save Merged Result", key="save_merged"):
                save_merged_result(merged_df, file1, file2)
        
        except Exception as e:
            st.error(f"Merge failed: {e}")


def handle_group_by_operations():
    """Handle group-by operations with aggregations."""
    st.markdown("### Group By Operations")
    
    if not st.session_state.data_files:
        return
    
    file_name = st.selectbox("Select file", list(st.session_state.data_files.keys()), key="group_file")
    df = st.session_state.data_files[file_name]["df"]
    
    # Group by columns
    group_cols = st.multiselect("Group by columns", df.columns.tolist(), key="group_cols")
    
    if group_cols:
        st.markdown("**Select aggregations**")
        
        # For each numeric column, allow aggregations
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        
        aggregations = {}
        for col in numeric_cols:
            funcs = st.multiselect(
                f"{col} aggregations",
                ["sum", "mean", "min", "max", "count", "median", "std", "first", "last", "nunique"],
                default=["count"],
                key=f"agg_{col}"
            )
            if funcs:
                aggregations[col] = funcs
        
        if aggregations and st.button("📊 Group By", key="group_btn"):
            try:
                grouped_df = group_by_dataframe(df, group_cols, aggregations)
                
                st.success(f"✅ Grouped successfully: {len(grouped_df)} groups")
                st.dataframe(grouped_df, use_container_width=True)
                
                # Save option
                if st.button("💾 Save Grouped Result", key="save_grouped"):
                    save_grouped_result(grouped_df, file_name)
            
            except Exception as e:
                st.error(f"Group by failed: {e}")


def handle_conversion_operations():
    """Handle format conversion operations."""
    st.markdown("### Convert File Format")
    
    if not st.session_state.data_files:
        return
    
    # File selection
    file_name = st.selectbox("Select file to convert", list(st.session_state.data_files.keys()), key="conv_file")
    file_info = st.session_state.data_files[file_name]
    file_path = file_info["path"]
    
    # Get current format
    current_ext = file_path.suffix.lower().lstrip('.')
    
    # Target format selection
    target_format = st.selectbox(
        "Convert to",
        ["csv", "json", "xlsx", "xls", "txt", "xml", "parquet", "feather"],
        key="target_format"
    )
    
    # Conversion options
    if len(st.session_state.data_files) > 1:
        convert_all = st.checkbox("Convert all files", key="convert_all")
        combine = st.checkbox("Combine into single file (same format only)", key="combine")
    else:
        convert_all = False
        combine = False
    
    if st.button("🔄 Convert", key="convert_btn"):
        output_dir = Path(config.get("directories.output", "./output"))
        
        try:
            if convert_all and combine:
                # Combine and convert all files
                convert_and_combine_files(target_format, output_dir)
            elif convert_all:
                # Convert all files individually
                convert_all_files(target_format, output_dir)
            else:
                # Convert single file
                convert_single_file(file_path, current_ext, target_format, output_dir)
        
        except Exception as e:
            st.error(f"Conversion failed: {e}")


def handle_split_operations():
    """Handle file splitting operations."""
    st.markdown("### Split Large Files")
    
    if not st.session_state.data_files:
        return
    
    file_name = st.selectbox("Select file to split", list(st.session_state.data_files.keys()), key="split_file")
    file_info = st.session_state.data_files[file_name]
    file_path = file_info["path"]
    df = file_info["df"]
    
    # Split method
    split_method = st.radio("Split by", ["File size (MB)", "Row count"], key="split_method")
    
    if split_method == "File size (MB)":
        target_size = st.number_input("Target file size (MB)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1)
        target_rows = None
    else:
        target_rows = st.number_input("Rows per file", min_value=1, max_value=1000000, value=10000, step=1000)
        target_size = None
    
    create_zip = st.checkbox("Zip output folder", key="split_zip")
    
    if st.button("✂️ Split File", key="split_btn"):
        output_dir = Path(config.get("directories.output", "./output"))
        
        try:
            with st.spinner("Splitting file..."):
                if split_method == "File size (MB)":
                    output_files, zip_path = split_data_file(
                        file_path, "size", target_size_mb=target_size,
                        output_dir=output_dir, create_zip=create_zip
                    )
                else:
                    output_files, zip_path = split_data_file(
                        file_path, "rows", target_rows=target_rows,
                        output_dir=output_dir, create_zip=create_zip
                    )
            
            st.success(f"✅ Split into {len(output_files)} files")
            st.info(f"Output: {output_dir}")
            if zip_path:
                st.info(f"Zip file: {zip_path.name}")
        
        except Exception as e:
            st.error(f"Split failed: {e}")


def save_edited_file(file_name: str, original_df: pd.DataFrame):
    """Save edited file to Output directory."""
    output_dir = Path(config.get("directories.output", "./output"))
    
    # Get edited version if exists, otherwise use original
    edited_df = st.session_state.edits_staged.get(file_name, original_df)
    
    file_info = st.session_state.data_files[file_name]
    original_path = file_info["path"]
    extension = original_path.suffix.lstrip('.')
    
    try:
        output_file = save_data_file(edited_df, output_dir, extension)
        st.success(f"✅ Saved: {output_file.name}")
        
        # Clear staged edits
        if file_name in st.session_state.edits_staged:
            del st.session_state.edits_staged[file_name]
    
    except Exception as e:
        st.error(f"Save failed: {e}")


def convert_single_file(file_path: Path, from_format: str, to_format: str, output_dir: Path):
    """Convert single file to target format."""
    output_file = ConversionRegistry.convert_file(file_path, from_format, to_format, output_dir)
    st.success(f"✅ Converted: {output_file.name}")


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
        
        # Update progress
        with progress_placeholder.container():
            show_progress_bar(i + 1, total, estimator, key="convert_progress")
        
        status_placeholder.text(f"Converting {i + 1}/{total}: {file_name}")
        time.sleep(0.1)  # Small delay for UI update
    
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
        # Check if all files are same format
        formats = [Path(info["path"]).suffix.lstrip('.') for info in st.session_state.data_files.values()]
        if len(set(formats)) > 1:
            st.warning("Files are different formats. Converting individually instead.")
            convert_all_files(target_format, output_dir)
            return
        
        # Load and combine all files
        combined_dfs = []
        for file_name, file_info in st.session_state.data_files.items():
            df = file_info["df"]
            combined_dfs.append(df)
        
        combined_df = pd.concat(combined_dfs, ignore_index=True)
        
        # Save combined file
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
