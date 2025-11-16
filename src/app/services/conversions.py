"""
Conversion Service

Central registry for format conversions between data file types.
"""

import pandas as pd
from pathlib import Path
from typing import Callable, Any, Dict
from io import StringIO

# Imports using proper package structure
from src.app.services.file_io import load_data_file, save_data_file
from src.app.utils.exceptions import ConversionError, OperationalError


class ConversionRegistry:
    """Registry for format conversions."""
    
    _converters: Dict[tuple[str, str], Callable] = {}
    
    @classmethod
    def register(cls, from_type: str, to_type: str):
        """
        Decorator to register conversion function.
        
        Args:
            from_type: Source format
            to_type: Target format
        """
        def decorator(func: Callable):
            cls._converters[(from_type.lower(), to_type.lower())] = func
            return func
        return decorator
    
    @classmethod
    def convert_file(cls, file_path: Path, from_type: str, to_type: str, output_dir: Path) -> Path:
        """
        Convert file from one format to another.
        
        Args:
            file_path: Path to source file
            from_type: Source format
            to_type: Target format
            output_dir: Output directory
        
        Returns:
            Path to converted file
        
        Raises:
            ConversionError: If conversion not supported or fails
        """
        from_type = from_type.lower().lstrip('.')
        to_type = to_type.lower().lstrip('.')
        
        # If same format, just copy with timestamp
        if from_type == to_type:
            from src.app.services.file_io import generate_timestamped_filename
            output_file = output_dir / generate_timestamped_filename(file_path.stem, to_type)
            import shutil
            shutil.copy2(file_path, output_file)
            return output_file
        
        # Check if conversion is registered
        key = (from_type, to_type)
        if key not in cls._converters:
            # Try generic conversion via DataFrame
            return cls._generic_convert(file_path, from_type, to_type, output_dir)
        
        # Use registered converter
        try:
            return cls._converters[key](file_path, output_dir)
        except Exception as e:
            raise ConversionError(
                f"Conversion failed: {e}",
                user_message=f"Failed to convert {file_path.name} from {from_type} to {to_type}",
                suggestion="Check file format and try again"
            ) from e
    
    @classmethod
    def _generic_convert(cls, file_path: Path, from_type: str, to_type: str, output_dir: Path) -> Path:
        """Generic conversion via DataFrame (works for most data formats)."""
        try:
            # Load to DataFrame
            df = load_data_file(file_path)
            
            # Save in target format
            output_file = save_data_file(df, output_dir, to_type)
            
            return output_file
        
        except Exception as e:
            raise ConversionError(
                f"Generic conversion failed: {e}",
                user_message=f"Could not convert {file_path.name}",
                suggestion="This conversion may not be supported"
            ) from e
    
    @classmethod
    def get_supported_conversions(cls, from_type: str) -> list[str]:
        """
        Get list of supported target formats for a source format.
        
        Args:
            from_type: Source format
        
        Returns:
            List of supported target formats
        """
        from_type = from_type.lower().lstrip('.')
        
        # Standard data formats can convert to each other via DataFrame
        data_formats = ['csv', 'json', 'xlsx', 'xls', 'txt', 'xml', 'parquet', 'feather']
        
        if from_type in data_formats:
            return data_formats
        
        # Check registered converters
        targets = [to_type for (fr, to_type) in cls._converters.keys() if fr == from_type]
        return list(set(targets))


# Register specific conversions if needed
@ConversionRegistry.register("csv", "xlsx")
def csv_to_xlsx(file_path: Path, output_dir: Path) -> Path:
    """Convert CSV to XLSX."""
    df = pd.read_csv(file_path, low_memory=False)
    return save_data_file(df, output_dir, "xlsx")


@ConversionRegistry.register("xlsx", "csv")
def xlsx_to_csv(file_path: Path, output_dir: Path) -> Path:
    """Convert XLSX to CSV."""
    df = pd.read_excel(file_path, engine='openpyxl')
    return save_data_file(df, output_dir, "csv")

