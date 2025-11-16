"""
File Fragmentation Service

Handles splitting large data files into smaller chunks by size or row count.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
import zipfile
from datetime import datetime

# Import utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.app.services.file_io import load_data_file, save_data_file, generate_timestamped_filename
from src.app.utils.exceptions import OperationalError


def split_data_file(
    file_path: Path,
    split_method: str,  # "size" or "rows"
    target_size_mb: Optional[float] = None,
    target_rows: Optional[int] = None,
    output_dir: Path | None = None,
    create_zip: bool = False
) -> Tuple[list[Path], Path | None]:
    """
    Split large data file into smaller chunks.
    
    Args:
        file_path: Path to source file
        split_method: "size" or "rows"
        target_size_mb: Target file size in MB (for size method)
        target_rows: Target rows per file (for rows method)
        output_dir: Output directory (default: same as source)
        create_zip: Whether to zip output folder
    
    Returns:
        Tuple of (list of output file paths, zip file path if created)
    
    Raises:
        OperationalError: If split fails
    """
    if not file_path.exists():
        raise OperationalError(
            f"File not found: {file_path}",
            user_message=f"File not found: {file_path.name}"
        )
    
    # Determine output directory
    if output_dir is None:
        output_dir = file_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subfolder for split files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    split_folder = output_dir / f"{file_path.stem}_split_{timestamp}"
    split_folder.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load file
        df = load_data_file(file_path)
        
        total_rows = len(df)
        
        if split_method == "rows" and target_rows:
            # Split by row count
            output_files = _split_by_rows(df, split_folder, file_path, target_rows)
        
        elif split_method == "size" and target_size_mb:
            # Split by file size
            output_files = _split_by_size(df, split_folder, file_path, target_size_mb)
        
        else:
            raise OperationalError(
                "Invalid split method or parameters",
                user_message="Invalid split configuration",
                suggestion="Specify either size (MB) or row count"
            )
        
        # Create zip if requested
        zip_path = None
        if create_zip:
            zip_path = split_folder.parent / f"{split_folder.name}.zip"
            _create_zip(split_folder, zip_path)
        
        return output_files, zip_path
    
    except Exception as e:
        if isinstance(e, OperationalError):
            raise
        raise OperationalError(
            f"File split failed: {e}",
            user_message=f"Failed to split file: {file_path.name}",
            suggestion="Check file format and available disk space"
        ) from e


def _split_by_rows(
    df: pd.DataFrame,
    output_dir: Path,
    original_file: Path,
    rows_per_file: int
) -> list[Path]:
    """Split DataFrame by row count."""
    output_files = []
    total_chunks = (len(df) + rows_per_file - 1) // rows_per_file  # Ceiling division
    
    for i in range(total_chunks):
        start_idx = i * rows_per_file
        end_idx = min(start_idx + rows_per_file, len(df))
        
        chunk = df.iloc[start_idx:end_idx]
        
        # Generate filename with part number
        extension = original_file.suffix.lstrip('.')
        filename = f"{original_file.stem}_part{i+1:03d}.{extension}"
        output_path = output_dir / filename
        
        # Save chunk
        output_file = save_data_file(chunk, output_path, extension)
        output_files.append(output_file)
    
    return output_files


def _split_by_size(
    df: pd.DataFrame,
    output_dir: Path,
    original_file: Path,
    target_size_mb: float
) -> list[Path]:
    """Split DataFrame by estimated file size."""
    output_files = []
    target_size_bytes = target_size_mb * 1024 * 1024
    
    # Estimate bytes per row (rough estimate)
    sample_size = min(1000, len(df))
    sample_df = df.head(sample_size)
    
    # Save sample to get size estimate
    temp_file = output_dir / ".temp_sample"
    extension = original_file.suffix.lstrip('.')
    sample_path = save_data_file(sample_df, temp_file, extension)
    sample_size_bytes = sample_path.stat().st_size
    bytes_per_row = sample_size_bytes / sample_size
    temp_file.unlink()  # Clean up
    
    # Calculate rows per file
    rows_per_file = int(target_size_bytes / bytes_per_row) if bytes_per_row > 0 else 10000
    rows_per_file = max(1, rows_per_file)  # At least 1 row
    
    # Split into chunks
    chunk_num = 1
    current_chunk = []
    current_size = 0
    
    for idx, row in df.iterrows():
        row_df = pd.DataFrame([row])
        row_size = bytes_per_row
        
        if current_size + row_size > target_size_bytes and current_chunk:
            # Save current chunk
            chunk_df = pd.DataFrame(current_chunk)
            filename = f"{original_file.stem}_part{chunk_num:03d}.{extension}"
            output_path = output_dir / filename
            output_file = save_data_file(chunk_df, output_path, extension)
            output_files.append(output_file)
            
            # Start new chunk
            current_chunk = [row.to_dict()]
            current_size = row_size
            chunk_num += 1
        else:
            current_chunk.append(row.to_dict())
            current_size += row_size
    
    # Save final chunk
    if current_chunk:
        chunk_df = pd.DataFrame(current_chunk)
        filename = f"{original_file.stem}_part{chunk_num:03d}.{extension}"
        output_path = output_dir / filename
        output_file = save_data_file(chunk_df, output_path, extension)
        output_files.append(output_file)
    
    return output_files


def _create_zip(source_dir: Path, zip_path: Path):
    """Create zip file from directory."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(source_dir)
                zipf.write(file_path, arcname)

