# DocZilla Technical Specification

This document provides detailed technical specifications for the DocZilla application implementation.

## 1. Technology Stack

### 1.1 Core Framework
- **Streamlit**: v1.28.0+ (latest stable)
  - Multipage application structure
  - Fragment support (`@st.fragment`) for performance optimization
  - Data editor (`st.data_editor`) for inline editing
  - Session state management (`st.session_state`)

### 1.2 Data Processing
- **Pandas**: v2.1.0+ (DataFrame operations, CSV/Excel handling)
- **NumPy**: v1.24.0+ (Numerical operations, array handling)
- **PyArrow**: v14.0.0+ (Parquet/Feather file support)
- **openpyxl**: v3.1.0+ (Excel XLSX read/write)
- **pyxlsb**: v1.0.10+ (Excel binary XLS support)

### 1.3 Document Processing
- **PyPDF2**: v3.0.1+ (PDF text extraction, page manipulation)
- **pdfminer.six**: v20221105+ (Advanced PDF parsing fallback)
- **pypdf**: v3.16.0+ (Alternative PDF library)
- **python-docx**: v1.1.0+ (DOCX read/write)
- **docx2txt**: v0.8 (DOC to text conversion)
- **html2text**: v2020.1.16 (HTML to text conversion)
- **xmltodict**: v0.13.0+ (XML parsing)

### 1.4 Image Processing
- **Pillow (PIL)**: v10.0.0+ (Image manipulation, format conversion)
- **img2pdf**: v0.5.1+ (Image to PDF conversion)
- **pillow-heif**: v0.13.0+ (HEIC support, optional)

### 1.5 Data Analysis & Cleaning
- **rapidfuzz**: v3.4.0+ (String similarity matching)
- **phonenumbers**: v8.13.0+ (Phone number parsing/formatting)
- **chardet**: v5.2.0+ (Encoding detection)

### 1.6 System & Utilities
- **watchdog**: v3.0.0+ (Directory monitoring)
- **pytest**: v7.4.0+ (Testing framework)
- **pytest-cov**: v4.1.0+ (Coverage reporting)

## 2. Architecture Overview

### 2.1 Application Structure
```
src/app/
├── main.py                 # Entry point, dashboard
├── pages/                  # Streamlit multipage modules
│   ├── data_handler.py
│   ├── document_handler.py
│   ├── image_handler.py
│   └── settings.py
├── components/             # Reusable UI components
│   ├── layout.py          # Page layouts, headers, sidebars
│   ├── tables.py          # Data table components
│   ├── metadata_panel.py  # Metadata display components
│   └── activity_log.py    # Activity log UI
├── services/              # Business logic services
│   ├── file_io.py        # File operations
│   ├── data_ops.py       # Data transformations
│   ├── doc_ops.py        # Document operations
│   ├── image_ops.py      # Image operations
│   ├── conversions.py    # Format conversion registry
│   └── fragments.py      # File splitting logic
├── utils/                 # Utility modules
│   ├── cache.py          # Caching utilities
│   ├── logging.py        # Logging system
│   ├── validators.py     # Validation functions
│   └── exceptions.py     # Custom exceptions
└── assets/               # Static assets
    ├── logos/
    └── animations/
```

### 2.2 Configuration Management
- **Format**: JSON
- **Location**: `src/app/config/app_config.json`
- **Template**: `src/app/config/config_template.json`
- **Structure**:
```json
{
  "directories": {
    "input": "./input",
    "output": "./output"
  },
  "cache": {
    "enabled": true,
    "max_size_gb": 2,
    "ttl_seconds": 3600
  },
  "watchdog": {
    "enabled": true,
    "polling_interval": 1.0
  },
  "logging": {
    "level": "INFO",
    "rotation_size_mb": 50,
    "retention_days": 30
  },
  "ui": {
    "auto_sample_threshold_rows": 5000,
    "auto_sample_threshold_cols": 100,
    "preview_percentage": 10
  }
}
```

## 3. Core Services Implementation

### 3.1 File I/O Service (`services/file_io.py`)

#### Functions
- `load_file(file_path: str, file_type: str) -> DataFrame | dict | bytes`
  - Loads file based on type
  - Returns appropriate data structure
  - Handles encoding detection
  - Caches results

- `save_file(data: DataFrame | dict | bytes, file_path: str, file_type: str) -> str`
  - Saves data to file with timestamp naming
  - Returns saved file path
  - Handles directory creation

- `move_file(source: str, destination: str, verify: bool = True) -> bool`
  - Moves file with verification
  - Returns success status

- `get_file_metadata(file_path: str) -> dict`
  - Returns file size, mtime, encoding, row/column count

- `generate_timestamped_filename(original_name: str, extension: str) -> str`
  - Format: `basename_YYYYMMDD_HHMMSS.ext`
  - Handles collisions with sequence number

#### Implementation Details
```python
def generate_timestamped_filename(original_name: str, extension: str) -> str:
    """Generate timestamped filename with collision handling."""
    from datetime import datetime
    import os
    
    base = os.path.splitext(os.path.basename(original_name))[0]
    base = sanitize_filename(base)  # Remove special chars
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename = f"{base}_{timestamp}.{extension}"
    
    # Handle collisions
    if os.path.exists(filename):
        counter = 1
        while os.path.exists(f"{base}_{timestamp}_{counter:03d}.{extension}"):
            counter += 1
        filename = f"{base}_{timestamp}_{counter:03d}.{extension}"
    
    # Truncate if too long (Windows 260 char limit, keep some buffer)
    if len(filename) > 200:
        max_base = 200 - len(timestamp) - len(extension) - 5  # -5 for separators
        base = base[:max_base]
        filename = f"{base}_{timestamp}.{extension}"
    
    return filename
```

### 3.2 Data Operations Service (`services/data_ops.py`)

#### Key Functions

##### Merge Operations
```python
def merge_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: str | list[str],
    how: str = "inner",
    similarity_threshold: float = 0.8,
    use_similarity: bool = False
) -> pd.DataFrame:
    """
    Merge two DataFrames with optional similarity matching.
    
    Args:
        df1: First DataFrame
        df2: Second DataFrame
        on: Column(s) to merge on
        how: Join type (inner, outer, left, right)
        similarity_threshold: Threshold for similarity matching (0-1)
        use_similarity: Enable fuzzy matching via rapidfuzz
    
    Returns:
        Merged DataFrame
    """
```

##### Group By Operations
```python
def group_by_dataframe(
    df: pd.DataFrame,
    by: str | list[str],
    aggregations: dict[str, list[str]]
) -> pd.DataFrame:
    """
    Group DataFrame with multiple aggregations.
    
    Args:
        df: Input DataFrame
        by: Column(s) to group by
        aggregations: Dict of {column: [functions]} where functions are
                      'count', 'sum', 'mean', 'min', 'max', 'median', 
                      'std', 'first', 'last', 'nunique'
    
    Returns:
        Grouped DataFrame
    """
```

##### Outlier Detection
```python
def detect_outliers(
    df: pd.DataFrame,
    columns: list[str],
    method: str = "zscore",
    threshold: float = 3.0
) -> pd.DataFrame:
    """
    Detect outliers using z-score or IQR method.
    
    Args:
        df: Input DataFrame
        columns: Numeric columns to analyze
        method: 'zscore' or 'iqr'
        threshold: Z-score threshold or IQR multiplier (1.5)
    
    Returns:
        DataFrame with outlier flags
    """
```

### 3.3 Conversion Service (`services/conversions.py`)

#### Conversion Registry Pattern
```python
class ConversionRegistry:
    """Registry for format conversions."""
    
    _converters: dict[tuple[str, str], Callable] = {}
    
    @classmethod
    def register(cls, from_type: str, to_type: str):
        """Decorator to register conversion function."""
        def decorator(func: Callable):
            cls._converters[(from_type, to_type)] = func
            return func
        return decorator
    
    @classmethod
    def convert(cls, data: Any, from_type: str, to_type: str) -> Any:
        """Convert data from one format to another."""
        key = (from_type, to_type)
        if key not in cls._converters:
            raise ValueError(f"Conversion {from_type}→{to_type} not supported")
        return cls._converters[key](data)

# Usage
@ConversionRegistry.register("csv", "xlsx")
def csv_to_xlsx(csv_data: str) -> bytes:
    """Convert CSV string to XLSX bytes."""
    df = pd.read_csv(StringIO(csv_data))
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()
```

### 3.4 Caching Service (`utils/cache.py`)

#### Implementation
```python
import streamlit as st
import hashlib
from datetime import datetime
from pathlib import Path

def get_file_hash(file_path: Path) -> str:
    """Generate SHA256 hash of file content and mtime."""
    stat = file_path.stat()
    mtime = str(stat.st_mtime)
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    combined = content + mtime.encode()
    return hashlib.sha256(combined).hexdigest()

@st.cache_data
def load_file_cached(file_path: str, file_hash: str):
    """Cached file loader with hash-based invalidation."""
    # Implementation loads file
    pass

def invalidate_cache(file_path: str):
    """Invalidate cache for specific file."""
    # Clear Streamlit cache for file
    pass
```

### 3.5 Logging Service (`utils/logging.py`)

#### Log Entry Structure
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    module: str
    request_id: str | None
    user_id: str | None
    operation: str | None
    duration_ms: float | None
    status: str  # "success" | "failure" | "warning"
    file_path: str | None
    error_details: str | None
    
    def to_csv_row(self) -> str:
        """Convert log entry to CSV row."""
        return ",".join([
            self.timestamp.isoformat(),
            self.level.value,
            f'"{self.message}"',
            self.module,
            self.request_id or "",
            self.user_id or "",
            self.operation or "",
            str(self.duration_ms) if self.duration_ms else "",
            self.status,
            self.file_path or "",
            f'"{self.error_details}"' if self.error_details else ""
        ])
```

## 4. Streamlit Components

### 4.1 Fragment Usage

#### Data Preview Fragment
```python
@st.fragment
def render_data_preview(df: pd.DataFrame, max_rows: int = 1000):
    """Render data preview with pagination."""
    # Only reruns when max_rows changes
    st.dataframe(df.head(max_rows))
    if len(df) > max_rows:
        st.caption(f"Showing first {max_rows} of {len(df)} rows")
```

#### Metadata Viewer Fragment
```python
@st.fragment
def render_metadata(file_metadata: dict):
    """Render file metadata in collapsible sections."""
    with st.expander("File Metadata"):
        st.json(file_metadata)
```

### 4.2 Progress Indicators

#### Implementation
```python
import time
from collections import deque

class ProgressEstimator:
    """Estimate ETA using exponential moving average."""
    
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.rates = deque(maxlen=10)
        self.current_rate = 0.0
    
    def update(self, items_processed: int, elapsed_time: float):
        """Update rate estimate."""
        if elapsed_time > 0:
            rate = items_processed / elapsed_time
            self.rates.append(rate)
            
            # Exponential moving average
            if self.current_rate == 0:
                self.current_rate = rate
            else:
                self.current_rate = (self.alpha * rate + 
                                   (1 - self.alpha) * self.current_rate)
    
    def estimate_eta(self, remaining_items: int) -> float:
        """Estimate time remaining in seconds."""
        if self.current_rate == 0:
            return 0.0
        return remaining_items / self.current_rate
    
    def format_eta(self, seconds: float) -> str:
        """Format ETA as human-readable string."""
        if seconds < 60:
            return f"~{int(seconds)}s"
        elif seconds < 3600:
            return f"~{int(seconds/60)}min"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"~{hours}h {minutes}min"

# Usage in UI
def show_progress(progress_bar, estimator, current, total):
    """Update progress bar with ETA."""
    progress = current / total
    remaining = total - current
    eta_seconds = estimator.estimate_eta(remaining)
    eta_str = estimator.format_eta(eta_seconds)
    
    progress_bar.progress(
        progress,
        text=f"{int(progress*100)}% | {current}/{total} files | {eta_str} remaining"
    )
```

## 5. Data Structures

### 5.1 Session State Structure
```python
st.session_state = {
    "session_id": "uuid-v4",
    "files_loaded": {
        "data_files": dict[str, pd.DataFrame],
        "document_files": dict[str, Document],
        "image_files": dict[str, Image]
    },
    "cache": {
        "file_hashes": dict[str, str],
        "metadata": dict[str, dict]
    },
    "ui_state": {
        "selected_files": list[str],
        "preview_percentage": float,
        "edits_staged": dict[str, pd.DataFrame]
    },
    "operations": {
        "current_operation": str | None,
        "progress": float,
        "errors": list[dict]
    }
}
```

### 5.2 File Metadata Structure
```python
@dataclass
class FileMetadata:
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    mtime: datetime
    encoding: str | None
    rows: int | None
    columns: int | None
    schema: dict | None  # Column types, names
    checksum: str  # SHA256 hash
```

## 6. Error Handling

### 6.1 Exception Hierarchy
```python
class DocZillaError(Exception):
    """Base exception for DocZilla."""
    pass

class OperationalError(DocZillaError):
    """Operational errors - handle gracefully."""
    def __init__(self, message: str, user_message: str = None, 
                 suggestion: str = None):
        self.message = message
        self.user_message = user_message or message
        self.suggestion = suggestion
        super().__init__(self.message)

class ProgrammerError(DocZillaError):
    """Programmer errors - log and crash."""
    pass

class ConversionError(OperationalError):
    """Error during format conversion."""
    pass

class ValidationError(OperationalError):
    """File validation error."""
    pass
```

### 6.2 Error Handler Decorator
```python
from functools import wraps
import traceback

def handle_errors(operation_name: str):
    """Decorator to wrap functions with error handling."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = generate_request_id()
            try:
                result = func(*args, **kwargs)
                log_operation(operation_name, request_id, "success")
                return result
            except OperationalError as e:
                log_error(operation_name, request_id, e, is_operational=True)
                st.error(f"⚠️ {e.user_message}")
                if e.suggestion:
                    st.info(f"💡 {e.suggestion}")
                return None
            except Exception as e:
                log_error(operation_name, request_id, e, is_operational=False)
                st.error("❌ An unexpected error occurred")
                with st.expander("Show technical details"):
                    st.code(traceback.format_exc())
                raise  # Re-raise programmer errors
        return wrapper
    return decorator
```

## 7. Testing Strategy

### 7.1 Unit Test Structure
```python
# tests/unit/test_data_ops.py
import pytest
import pandas as pd
from src.app.services.data_ops import merge_dataframes

def test_merge_inner_join():
    """Test inner join merge operation."""
    df1 = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"]})
    df2 = pd.DataFrame({"id": [2, 3, 4], "value": [10, 20, 30]})
    
    result = merge_dataframes(df1, df2, on="id", how="inner")
    
    assert len(result) == 2
    assert result.iloc[0]["name"] == "B"

def test_merge_similarity_matching():
    """Test merge with fuzzy matching."""
    df1 = pd.DataFrame({"name": ["John Smith", "Jane Doe"]})
    df2 = pd.DataFrame({"name": ["Jon Smith", "Jane Do"]})
    
    result = merge_dataframes(
        df1, df2, on="name", 
        use_similarity=True, 
        similarity_threshold=0.8
    )
    
    assert len(result) > 0
```

### 7.2 Integration Test Structure
```python
# tests/integration/test_file_conversion.py
import pytest
import tempfile
from pathlib import Path
from src.app.services.conversions import ConversionRegistry

def test_csv_to_xlsx_conversion():
    """Test CSV to XLSX conversion end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test CSV
        csv_file = Path(tmpdir) / "test.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25")
        
        # Convert
        xlsx_file = Path(tmpdir) / "test.xlsx"
        # ... conversion logic ...
        
        # Verify
        assert xlsx_file.exists()
        # ... verify content ...
```

## 8. Performance Optimization

### 8.1 Chunked Processing
```python
def process_large_file(file_path: Path, chunk_size: int = 10000):
    """Process large file in chunks."""
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Process chunk
        yield process_chunk(chunk)
```

### 8.2 Parallel Processing
```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def convert_files_parallel(file_paths: list[str], target_format: str):
    """Convert multiple files in parallel."""
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [
            executor.submit(convert_file, path, target_format)
            for path in file_paths
        ]
        results = [f.result() for f in futures]
    return results
```

## 9. Security Considerations

### 9.1 File Path Validation
```python
def validate_file_path(file_path: str, allowed_dir: Path) -> Path:
    """Validate file path to prevent directory traversal."""
    resolved = Path(file_path).resolve()
    allowed = allowed_dir.resolve()
    
    try:
        resolved.relative_to(allowed)
    except ValueError:
        raise ValidationError(
            f"File path outside allowed directory: {file_path}",
            "Access denied"
        )
    
    return resolved
```

### 9.2 File Size Limits (Runtime Checks)
```python
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB (soft limit)

def check_file_size(file_path: Path):
    """Check file size and warn if very large."""
    size = file_path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise OperationalError(
            f"File too large: {size / (1024**3):.2f}GB",
            "File exceeds recommended size limit",
            "Consider splitting the file first"
        )
    elif size > 500 * 1024 * 1024:  # 500MB
        st.warning(f"⚠️ Large file detected ({size / (1024**2):.0f}MB). Processing may be slow.")
```

## 10. Deployment Considerations

### 10.1 Windows Compatibility
- Use `pathlib.Path` for cross-platform path handling
- Handle Windows file locking with retries
- Use PowerShell for directory operations (`subprocess` with `Start-Process`)
- Test on Windows 10/11

### 10.2 Resource Management
- Monitor memory usage (warn at 80% system RAM)
- Limit cache size (2GB default)
- Cleanup temp files on app close
- Rotate logs to prevent disk space issues

---

*Last Updated: Phase 0 Design Review*
*Version: 1.0*

