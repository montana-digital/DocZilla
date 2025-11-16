"""
Unit tests for Conversion Service
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.app.services.conversions import ConversionRegistry
from src.app.utils.exceptions import ConversionError


class TestConversionRegistry:
    """Tests for ConversionRegistry."""
    
    def test_register_conversion(self):
        """Test registering a conversion."""
        @ConversionRegistry.register("test_from", "test_to")
        def test_converter(file_path, output_dir):
            return output_dir / "test_output.txt"
        
        # Check if conversion is registered
        supported = ConversionRegistry.get_supported_conversions("test_from")
        assert "test_to" in supported or "test_from" in supported
    
    def test_convert_csv_to_xlsx(self):
        """Test CSV to XLSX conversion."""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                result = ConversionRegistry.convert_file(
                    Path(f.name),
                    "csv",
                    "xlsx",
                    output_dir
                )
                assert result.exists()
                assert result.suffix == '.xlsx'
                
                # Verify content
                loaded = pd.read_excel(result, engine='openpyxl')
                assert len(loaded) == 2
                assert 'a' in loaded.columns
    
    def test_convert_same_format(self):
        """Test converting to same format (should copy with timestamp)."""
        df = pd.DataFrame({'a': [1, 2]})
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                result = ConversionRegistry.convert_file(
                    Path(f.name),
                    "csv",
                    "csv",
                    output_dir
                )
                assert result.exists()
                assert result != Path(f.name)  # Should be different file
    
    def test_convert_unsupported(self):
        """Test converting unsupported format raises error."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"test")
            f.flush()
            
            with tempfile.TemporaryDirectory() as tmp:
                with pytest.raises(ConversionError):
                    ConversionRegistry.convert_file(
                        Path(f.name),
                        "xyz",
                        "csv",
                        Path(tmp)
                    )
    
    def test_get_supported_conversions(self):
        """Test getting supported conversions."""
        # CSV should support many formats
        supported = ConversionRegistry.get_supported_conversions("csv")
        assert len(supported) > 0
        assert "csv" in supported or "xlsx" in supported

