# DocZilla - The File Conversion Specialist

DocZilla is a comprehensive document conversion and manipulation application built with Streamlit, designed to provide users with rich but simple document conversion and manipulation tools with advanced features and technical insight into documents.

## Features

### Data File Handler
- **Supported Formats**: CSV, JSON, XLSX, XLS, TXT, XML, Parquet, Feather, ODS
- **Analysis**: Quick file structure validation, row/column counts, file size analysis
- **Editing**: Add/remove rows and columns, inline cell editing, find/replace
- **Data Cleaning**: Remove empty rows/columns, handle missing values, remove duplicates, standardize formats
- **Advanced Operations**: Merge tables, group-by aggregations, outlier detection, phone/URL standardization
- **Conversion**: Convert between data formats with progress tracking
- **File Splitter**: Split large files into user-specified sizes (by size or row count)

### Document File Handler
- **Supported Formats**: PDF, DOCX, DOC, RTF, TXT, ODT, HTML
- **Viewing**: Text extraction and display with optional metadata
- **Editing**: Text-only editing while preserving document structure
- **Conversion**: Convert between document formats
- **Search**: Full-text search across uploaded documents
- **Page Operations**: Move, append, and remove pages with batch operations

### Image File Handler
- **Supported Formats**: PNG, JPG, TIFF, WEBP, PDF, GIF, BMP, SVG, HEIC
- **Conversion**: Convert between image formats
- **Compression**: Reduce file sizes with quality control
- **Cropping**: Interactive cropping with aspect ratio presets
- **Grid Combine**: Combine multiple images into a single grid layout (optimized for OCR)

### Settings & Configuration
- **Directory Management**: Configure input/output directories
- **Logo Management**: Upload logos for each tool page
- **Activity Logs**: View and download activity logs (CSV format)
- **Cache Management**: Monitor cache size and clear temp data
- **Dependency Check**: Health check for all required dependencies

## Installation

### Prerequisites
- Windows 10/11 (tested on Windows, may work on other platforms)
- Python 3.11 or higher
- At least 4GB RAM recommended
- Administrator rights (optional, for some directory operations)

### Setup

1. **Clone or download this repository**
   ```powershell
   git clone <repository-url>
   cd DocZilla
   ```

2. **Run the setup script**
   ```powershell
   python scripts/setup_app.py
   ```

   The setup script will:
   - Verify Windows compatibility
   - List available Python versions
   - Let you select Python version
   - Create virtual environment (`.venv_doczilla`)
   - Install dependencies (app only or app + tests)
   - Create necessary directories (logs, temp)

3. **Run the application**
   ```powershell
   python scripts/run_app.py
   ```

   Or manually:
   ```powershell
   .venv_doczilla\Scripts\activate
   streamlit run src/app/main.py
   ```

## Usage

### First Run

1. **Configure Directories**
   - Go to Settings page
   - Set Input and Output directories
   - These directories will be used for file operations

2. **Upload Files**
   - Use drag-and-drop on any handler page
   - Or copy files to Input directory and click "Load from Input Dir"

3. **Process Files**
   - Select files from the list
   - Choose operation (convert, clean, edit, etc.)
   - Files are saved to Output directory with timestamps (never overwrites originals)

### Tips

- **Large Files**: Files over 5,000 rows or 100 columns are automatically sampled (10% preview). Use slider to adjust.
- **Bulk Operations**: Progress bars show time remaining for large operations
- **Cache**: Cache persists during session for faster repeated operations. Clears on app restart.
- **Temp Data**: Search indexes stored in `temp/` folder for faster subsequent searches. Clear via Settings.

## Project Structure

```
DocZilla/
├── docs/                    # Documentation
├── src/app/                # Application source
│   ├── main.py            # Entry point
│   ├── pages/             # Streamlit pages
│   ├── components/        # Reusable UI components
│   ├── services/          # Business logic
│   ├── utils/             # Utilities
│   ├── assets/            # Static assets (logos, animations)
│   └── config/            # Configuration files
├── scripts/               # Setup and run scripts
├── tests/                 # Test suite
├── requirements/          # Dependency files
├── logs/                  # Activity logs (auto-created)
└── temp/                  # Temporary indexes (auto-created)
```

## Development

### Running Tests

```powershell
.venv_doczilla\Scripts\activate
pytest tests/
```

With coverage:
```powershell
pytest tests/ --cov=src/app --cov-report=html
```

### Code Style

This project uses:
- **black** for code formatting
- **flake8** for linting
- **mypy** for type checking
- **isort** for import sorting

Format code:
```powershell
black src/
isort src/
```

### Project Phases

- **Phase 0**: ✅ Design and documentation (completed)
- **Phase 1**: Repository scaffolding, base Streamlit skeleton
- **Phase 2**: Data Handler feature set
- **Phase 3**: Document Handler
- **Phase 4**: Image Handler
- **Phase 5**: Settings page, watchdog integration
- **Phase 6**: QA hardening, documentation

## Configuration

Configuration is stored in `src/app/config/app_config.json` (created from template on first run).

Key settings:
- Input/Output directory paths
- Cache settings (enable/disable, max size)
- Watchdog settings (enable/disable, polling interval)
- Logging settings (level, rotation, retention)

## Troubleshooting

### Common Issues

**"Feature unavailable: install X package"**
- Some optional features require additional packages
- Check Settings > Dependency Check for missing dependencies
- Install missing packages: `pip install package-name`

**File not found errors**
- Verify Input/Output directories exist and are accessible
- Check Settings > Directories configuration
- Ensure files are in correct format (check supported formats)

**Memory errors with large files**
- Files over 500MB may cause slowdowns
- Use Data File Splitter to split large files first
- Consider increasing system RAM

**Watchdog not detecting file changes**
- Check Settings > Watchdog settings
- Try manual refresh button
- Verify directory permissions

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support contact information here]

## Acknowledgments

Part of the SPEAR Toolkit

---

**Note**: DocZilla is currently in active development. Features are being added in phases. See `docs/DocZilla_design_overview.md` for complete specifications.

