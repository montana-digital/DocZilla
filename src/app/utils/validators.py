"""
Validation Utilities

File and data validation functions.
"""

from pathlib import Path
from typing import Optional, List
import re
from .exceptions import ValidationError, FileNotFoundError as CustomFileNotFoundError


def validate_file_path(file_path: str | Path, allowed_dir: Path | None = None) -> Path:
    """
    Validate file path to prevent directory traversal.
    
    Args:
        file_path: Path to validate
        allowed_dir: Optional allowed directory (prevents traversal)
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If path is invalid or outside allowed directory
        CustomFileNotFoundError: If file doesn't exist
    """
    try:
        resolved = Path(file_path).resolve()
    except Exception as e:
        raise ValidationError(
            f"Invalid file path: {file_path}",
            user_message="Invalid file path specified",
            suggestion="Check the file path and try again"
        ) from e
    
    # Check if file exists
    if not resolved.exists():
        raise CustomFileNotFoundError(
            f"File not found: {resolved}",
            user_message=f"File not found: {resolved.name}",
            suggestion="Check the file path and ensure the file exists"
        )
    
    # Check directory traversal if allowed_dir specified
    if allowed_dir:
        allowed = Path(allowed_dir).resolve()
        try:
            resolved.relative_to(allowed)
        except ValueError:
            raise ValidationError(
                f"File path outside allowed directory: {file_path}",
                user_message="Access denied: File outside allowed directory",
                suggestion=f"Move file to {allowed_dir} directory"
            )
    
    return resolved


def validate_file_extension(
    file_path: str | Path,
    allowed_extensions: List[str]
) -> bool:
    """
    Validate file extension against allowed list.
    
    Args:
        file_path: Path to file
        allowed_extensions: List of allowed extensions (with or without dot)
    
    Returns:
        True if extension is allowed
    
    Raises:
        ValidationError: If extension not allowed
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    # Normalize extensions (add dot if missing)
    allowed = [ext if ext.startswith('.') else f'.{ext}' for ext in allowed_extensions]
    allowed = [ext.lower() for ext in allowed]
    
    if extension not in allowed:
        raise ValidationError(
            f"File extension not allowed: {extension}",
            user_message=f"File type not supported: {extension}",
            suggestion=f"Supported formats: {', '.join(allowed)}"
        )
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing special characters.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove special characters except alphanumeric, dash, underscore, dot
    sanitized = re.sub(r'[^\w\-_.]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Prevent empty filenames
    if not sanitized:
        sanitized = "file"
    
    return sanitized


def validate_file_size(
    file_path: str | Path,
    max_size_mb: Optional[float] = None,
    warn_threshold_mb: float = 500.0
) -> tuple[bool, Optional[str]]:
    """
    Validate file size.
    
    Args:
        file_path: Path to file
        max_size_mb: Optional maximum size in MB (None = no limit)
        warn_threshold_mb: Size threshold for warning (default: 500MB)
    
    Returns:
        Tuple of (is_valid, warning_message)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise CustomFileNotFoundError(
            f"File not found: {file_path}",
            user_message=f"File not found: {file_path.name}"
        )
    
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    warning = None
    
    # Check max size
    if max_size_mb and size_mb > max_size_mb:
        return False, f"File size ({size_mb:.2f}MB) exceeds maximum ({max_size_mb}MB)"
    
    # Check warning threshold
    if size_mb > warn_threshold_mb:
        warning = f"Large file detected ({size_mb:.2f}MB). Processing may be slow."
    
    return True, warning

