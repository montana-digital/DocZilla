"""
File I/O Service

Handles file operations: loading, saving, moving, metadata extraction.
"""

from pathlib import Path
from datetime import datetime
import hashlib
import pandas as pd
import json
import xmltodict
from io import StringIO, BytesIO
from typing import Any

# Imports using proper package structure
from src.app.utils.exceptions import OperationalError, ValidationError
from src.app.utils.validators import validate_file_path, validate_file_extension, sanitize_filename


def load_data_file(file_path: str | Path) -> pd.DataFrame:
    """
    Load data file (CSV, JSON, XLSX, XLS, TXT, XML, Parquet, Feather).
    
    Args:
        file_path: Path to file
    
    Returns:
        DataFrame
    
    Raises:
        OperationalError: If file cannot be loaded
    """
    file_path = Path(file_path)
    
    # Validate file
    validate_file_path(file_path)
    
    extension = file_path.suffix.lower()
    
    try:
        if extension == '.csv':
            # Try auto-detecting encoding
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            return pd.read_csv(file_path, encoding=encoding, low_memory=False)
        
        elif extension == '.tsv':
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            return pd.read_csv(file_path, sep='\t', encoding=encoding, low_memory=False)
        
        elif extension == '.json' or extension == '.jsonl':
            if extension == '.jsonl':
                return pd.read_json(file_path, lines=True)
            return pd.read_json(file_path)
        
        elif extension == '.xlsx':
            return pd.read_excel(file_path, engine='openpyxl')
        
        elif extension == '.xls':
            return pd.read_excel(file_path, engine='xlrd')
        
        elif extension == '.parquet':
            return pd.read_parquet(file_path, engine='pyarrow')
        
        elif extension == '.feather':
            return pd.read_feather(file_path)
        
        elif extension == '.xml':
            # XML to dict to DataFrame
            with open(file_path, 'r', encoding='utf-8') as f:
                xml_dict = xmltodict.parse(f.read())
            return pd.json_normalize(xml_dict)
        
        elif extension == '.txt':
            # Try CSV first, then JSON, then plain text
            try:
                return pd.read_csv(file_path, sep=None, engine='python')
            except:
                try:
                    return pd.read_json(file_path, lines=True)
                except:
                    # Plain text - create single column DataFrame
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    return pd.DataFrame({'text': lines})
        
        else:
            raise OperationalError(
                f"Unsupported file type: {extension}",
                user_message=f"File type not supported: {extension}",
                suggestion="Supported formats: CSV, JSON, XLSX, XLS, TXT, XML, Parquet, Feather"
            )
    
    except Exception as e:
        if isinstance(e, OperationalError):
            raise
        raise OperationalError(
            f"Failed to load file: {e}",
            user_message=f"Could not load file: {file_path.name}",
            suggestion="Check file format and encoding"
        ) from e


def save_data_file(df: pd.DataFrame, file_path: str | Path, file_type: str) -> Path:
    """
    Save DataFrame to file with timestamp naming.
    
    Args:
        df: DataFrame to save
        file_path: Destination directory or full path
        file_type: File extension (csv, json, xlsx, etc.)
    
    Returns:
        Path to saved file
    
    Raises:
        OperationalError: If save fails
    """
    file_path = Path(file_path)
    file_type = file_type.lower().lstrip('.')
    
    # If directory provided, generate filename
    if file_path.is_dir() or not file_path.suffix:
        filename = generate_timestamped_filename("data", file_type)
        file_path = file_path / filename
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if file_type == 'csv':
            df.to_csv(file_path, index=False, encoding='utf-8')
        
        elif file_type == 'json':
            df.to_json(file_path, orient='records', indent=2)
        
        elif file_type == 'jsonl':
            df.to_json(file_path, orient='records', lines=True)
        
        elif file_type == 'xlsx':
            df.to_excel(file_path, index=False, engine='openpyxl')
        
        elif file_type == 'xls':
            # XLS format limited - use XLSX if possible
            df.to_excel(file_path, index=False, engine='xlwt')
        
        elif file_type == 'parquet':
            df.to_parquet(file_path, engine='pyarrow')
        
        elif file_type == 'feather':
            df.to_feather(file_path)
        
        elif file_type == 'xml':
            # DataFrame to dict to XML
            records = df.to_dict('records')
            xml_dict = {'root': {'record': records}}
            xml_str = xmltodict.unparse(xml_dict, pretty=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_str)
        
        elif file_type == 'txt':
            # Save as CSV format text
            df.to_csv(file_path, index=False, sep='\t')
        
        else:
            raise OperationalError(
                f"Unsupported output format: {file_type}",
                user_message=f"Output format not supported: {file_type}",
                suggestion="Supported formats: CSV, JSON, XLSX, XLS, TXT, XML, Parquet, Feather"
            )
        
        return file_path
    
    except Exception as e:
        if isinstance(e, OperationalError):
            raise
        raise OperationalError(
            f"Failed to save file: {e}",
            user_message=f"Could not save file: {file_path.name}",
            suggestion="Check directory permissions and disk space"
        ) from e


def get_file_metadata(file_path: str | Path) -> dict:
    """
    Get file metadata including stats and schema.
    
    Args:
        file_path: Path to file
    
    Returns:
        Dictionary with file metadata
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise OperationalError(
            f"File not found: {file_path}",
            user_message=f"File not found: {file_path.name}"
        )
    
    stat = file_path.stat()
    extension = file_path.suffix.lower()
    
    metadata = {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "file_size": stat.st_size,
        "file_size_mb": stat.st_size / (1024 * 1024),
        "extension": extension,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat()
    }
    
    # Try to get data-specific metadata
    try:
        if extension in ['.csv', '.json', '.xlsx', '.xls', '.txt', '.xml', '.parquet', '.feather']:
            df = load_data_file(file_path)
            metadata.update({
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "missing_values": df.isnull().sum().to_dict(),
                "has_index": df.index.name is not None
            })
    except Exception:
        # If can't read, just return file metadata
        pass
    
    return metadata


def move_file(source: str | Path, destination: str | Path, verify: bool = True) -> bool:
    """
    Move file with verification.
    
    Args:
        source: Source file path
        destination: Destination file path
        verify: Verify copy was successful before deleting source
    
    Returns:
        True if successful
    
    Raises:
        OperationalError: If move fails
    """
    import shutil
    
    source = Path(source)
    destination = Path(destination)
    
    if not source.exists():
        raise OperationalError(
            f"Source file not found: {source}",
            user_message=f"File not found: {source.name}"
        )
    
    try:
        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        if verify:
            # Copy first
            shutil.copy2(source, destination)
            
            # Verify copy
            if destination.exists() and destination.stat().st_size == source.stat().st_size:
                # Delete source
                source.unlink()
                return True
            else:
                # Copy failed, don't delete source
                if destination.exists():
                    destination.unlink()
                raise OperationalError(
                    "File verification failed after copy",
                    user_message="File copy verification failed",
                    suggestion="Source file not deleted. Try again."
                )
        else:
            # Direct move
            shutil.move(str(source), str(destination))
            return True
    
    except Exception as e:
        if isinstance(e, OperationalError):
            raise
        raise OperationalError(
            f"Failed to move file: {e}",
            user_message=f"Could not move file: {source.name}",
            suggestion="Check file permissions and disk space"
        ) from e


def generate_timestamped_filename(original_name: str, extension: str) -> str:
    """
    Generate timestamped filename.
    
    Format: basename_YYYYMMDD_HHMMSS.ext
    
    Args:
        original_name: Original filename
        extension: File extension
    
    Returns:
        Timestamped filename
    """
    base = Path(original_name).stem
    base = sanitize_filename(base)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename = f"{base}_{timestamp}.{extension}"
    
    # Handle collisions with sequence number
    if Path(filename).exists():
        counter = 1
        while Path(f"{base}_{timestamp}_{counter:03d}.{extension}").exists():
            counter += 1
        filename = f"{base}_{timestamp}_{counter:03d}.{extension}"
    
    # Truncate if too long (Windows 260 char limit)
    if len(filename) > 200:
        max_base = 200 - len(timestamp) - len(extension) - 5
        base = base[:max_base]
        filename = f"{base}_{timestamp}.{extension}"
    
    return filename



