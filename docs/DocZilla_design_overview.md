# DocZilla – Phase 0 Design Dossier

## 1. Vision and Scope
- **Goal**: Deliver a multipage Streamlit desktop app that centralizes advanced document/data/image conversions with intuitive controls for non-technical users.
- **Platforms/Stack**: Python 3.11+ (user selectable), Streamlit multipage, Pandas, NumPy, SciPy, PyPDF2, python-docx, Pillow, plotly, rapidfuzz, zipfile, watchdog, pytest.
- **Non-Goals**: No cloud services, no ML/OCR, avoid overwriting user originals, limit resource usage.

## 2. User Personas and Core Journeys
- **Ops Specialist**: High-volume CSV/XLSX cleaning, needs metadata, dedupe, merge logic, standardization.
- **Knowledge Worker**: Converts PDF/DOCX and reorganizes pages, needs search, append/move/remove actions.
- **Creative Analyst**: Manages images (convert/compress/crop/grid combine) for downstream OCR.

Journeys all begin with consistent sidebar (DocZilla summary + Input/Output shortcuts) and rely on same logging/activity feed.

## 3. Functional Requirements Snapshot
- **File ingest**: drag/drop + watch input/output directories, enforce allowed extensions.
- **Analysis**: quick stats (valid schema, row/column counts, file size) with optional metadata collapsibles.
- **Editing**: row/column add/drop, standard cleaners, merge/group-by, outlier detection, manual edits capped on large datasets (10% preview rule).
- **Conversion**: same-type combine+convert, mixed-type unify flow, timestamped copies, optional zipping for bulk.
- **Fragmentation**: split oversized datasets/images into size-bounded chunks with labeling.
- **Document tools**: textual display/edit, search, append/move/remove pages with previews.
- **Image tools**: convert, compress %, crop (mouse), single-image grid builder (<=9 items, layout heuristics).
- **Settings**: directory paths, logo uploads, cache/session stats, activity log viewer, dependency health check.
- **Packaging**: setup script builds venv, installs core/test deps, warns if not Windows; launcher validates env.

## 4. Proposed Directory Layout
```
DocZilla/
  docs/
    DocZilla_spec_v1.txt
    DocZilla_design_overview.md
    content_editor_guide.md
  src/
    app/
      main.py
      pages/
        data_handler.py
        document_handler.py
        image_handler.py
        settings.py
      components/
        layout.py
        tables.py
        metadata_panel.py
        activity_log.py
      services/
        file_io.py
        data_ops.py
        doc_ops.py
        image_ops.py
        conversions.py
        fragments.py
      utils/
        cache.py
        logging.py
        validators.py
        exceptions.py
      assets/
        logos/
        animations/
  scripts/
    setup_app.py
    run_app.py
  tests/
    unit/
    integration/
    e2e_smoke/
    fixtures/
  logs/              # Persistent activity logs (CSV format)
  temp/              # Temporary indexes and session data
  .venv_doczilla/    # Virtual environment (created by setup)
```

## 5. Page-Level Architecture
| Page | Streamlit Entry | Responsibility | Key Components/Fragments |
| --- | --- | --- | --- |
| Main dashboard | `main.py` | Welcome animation, global stats, quick links, activity feed snapshot | hero header fragment, summary cards, activity log fragment |
| Data File Handler | `pages/data_handler.py` | Ingest/analyze/edit/convert/tabulate tabular data | drag-drop uploader, stats grid, metadata collapsibles, data preview fragment, cleaner toolbox, converter wizard |
| Document File Handler | `pages/document_handler.py` | Display/edit/convert docs, search, page ops | document list manager, search fragment, editing modal, page manipulation wizard |
| Image File Handler | `pages/image_handler.py` | Convert/compress/crop/combine images | preview gallery, cropper fragment (st_cropper), compression estimator, grid composer |
| Settings | `pages/settings.py` | Paths/logos/config/log viewer/cache stats/health check | directory picker, logo uploader, cache chart, dependency status list, log table |

Fragments (Streamlit `@st.fragment`) wrap heavy widgets (data preview, metadata viewer, search results, image grid composer) to minimize reruns.

## 6. Shared Services and Utilities
- **`file_io.py`**: Input/output coordination, directory watch, safe copy/move, timestamped naming (`filename_20250121_143022.xlsx` format), OS shortcuts (PowerShell `Start-Process`), no file size caps (supports unlimited uploads). Always saves to Output directory; if permissions issue, user selects alternative location.
- **`data_ops.py`**: Pandas helpers (validation, profiling, sampling, editing, cleaning, merge, group-by, outlier detection using z-score/IQR with user-configurable thresholds in UI + rapidfuzz token_set_ratio for "merge on similar" at 80% threshold). Phone number standardization: international support with auto-detection of country code. URL standardization: full URL format `https://example.com/pathhere`, base domain `example.com`; user selects components to include (protocol, path, etc.).
- **`doc_ops.py`**: PyPDF2/python-docx/textract fallbacks, search indexing via in-memory dict by default; for large/many files, creates persistent index in `temp/` folder for faster subsequent searches. Page manipulation, text-only edits.
- **`image_ops.py`**: Pillow, numpy transforms, compression heuristics, cropping, grid layout solver (handles aspect ratios, auto-fits layout, ensures 300 DPI for OCR readability).
- **`conversions.py`**: Central conversion registry keyed by MIME, uses tablib, openpyxl, pdf2docx, img2pdf. Ensures Convert+Combine patterns and unify workflows. All outputs use timestamped naming in Output directory.
- **`fragments.py`**: Dataset/image splitting logic with user-specified file sizes (Data File Splitter feature), size estimation and optional zipping.
- **`cache.py`**: Streamlit caching (st.cache_data/st.cache_resource), clears on app stop, persists during session while served on localhost. TTL tied to file hash.
- **`validators.py`**: File type, schema, size, input sanitization. Auto-sampling above 5,000 rows (10% preview with slider adjustment).
- **`logging.py`**: Structured logging, activity feed persistence as CSV in `logs/` folder, correlation IDs, rotation strategy (size/time based).
- **`exceptions.py`**: Operational vs programmer error classes with user-friendly UI surfacing, optional "Show technical details" toggle for advanced users. Dependency errors shown as "Feature unavailable: install X package".

## 7. Dependency Strategy & Fallbacks
| Capability | Primary Lib | Fallback/Note |
| --- | --- | --- |
| Spreadsheet ingest | Pandas + pyarrow | csv/sniffer fallback if pandas fails |
| Large XLSX read | openpyxl | pyxlsb for binary |
| JSON/XML display | `json`, `xmltodict` | raw text fallback |
| Document read/write | python-docx, PyPDF2 | `docx2txt`, pdfminer.six |
| Image processing | Pillow | Wand (ImageMagick) optional |
| Similarity merge | rapidfuzz token_set_ratio | difflib if not installed |
| Phone number parsing | phonenumbers (international) | regex fallback with country code detection |
| URL parsing | `urllib.parse` | regex fallback |
| Compression | Pillow quality reduction | TinyPNG API hook placeholder (disabled by default) |
| Directory watcher | watchdog | Manual refresh button if watchdog unavailable |
| Search indexing | in-memory dict (default), Whoosh-like minimal index (temp fallback) | Simple string matching if index unavailable |

**Dependency philosophy**: Use libraries as needed (no artificial restrictions). All UI actions guard missing deps and surface "Feature unavailable: install X package" messages. Graceful degradation where possible.

## 8. UI/UX Blueprints
- **Grid spec**: Each tool page begins with 2-column table: Title + 2-line summary, Quick Start bullet list, right column merged for logo placeholder (user-supplied, 150x150px recommended).
- **Sidebar**: Persistent brand block "DocZilla – The file conversion specialist", logo (150x150px) at top, navigation (Streamlit multipage), Input/Output buttons (`subprocess.Popen(["explorer", path])`), status chips (cache size, session id).
- **Title animation**: Main page title animates app name (typewriter/fade-in effect) while preserving "Part of the SPEAR Toolkit" static text. Pattern matches example animation style.
- **Metadata toggles**: Checkbox per section to render collapsible container with file-specific details.
- **Large dataset guard**: Auto-sample above 5,000 rows (10% preview, min 100 rows), slider to adjust display range.
- **Activity log**: Running feed with filters (all/info/warn/error); errors display friendly message with optional "Show technical details" toggle; keeps UI responsive.
- **Progress indicators**: For bulk operations (converting 50+ files), show progress bar with time remaining estimate based on processing rate.

## 9. Workflow Specifications
### 9.1 Data Handler Flow
1. Upload/Load from Input dir ➜ validation (type, no size limit) ➜ caching (persists during session, clears on app stop).
2. File analysis fragment returns schema stats, file size, column profiling. Auto-sample above 5,000 rows (10% preview, adjustable via slider).
3. Data preview panel (capped) with editing toolbar (add/remove rows/columns, fill NA, dedupe, formatters, phone/url normalization with user-configurable options, trim spaces, char removal). Outlier detection with user-configurable threshold in UI (z-score, IQR).
4. Metadata optional: file properties, pandas dtypes, missingness (collapsible sections).
5. Merge/group-by/outlier detection use modal wizards. Merge "on similar" uses rapidfuzz token_set_ratio with 80% threshold; user can select columns to match.
6. Conversion branch:
   - Uniform types: choose Combine & Convert or Convert individually; outputs stored under Output dir with timestamp (`filename_20250121_143022.xlsx`) + optional zip. Progress bar for bulk operations.
   - Mixed types: unify step chooses target type; hetero files converted, existing ones copied/renamed with timestamp.
7. Data File Splitter (Fragmenter): User specifies target file size (e.g., 10MB); splits large source file into chunks, writes to subfolder with labeled filenames; optional zip. Shows progress with time remaining.
8. Output→Input mover: Delete from Output only after successful copy verification. If file exists in Input, adds conflict suffix. Always saves conversions to Output directory.

### 9.2 Document Handler Flow
1. Upload or load directories; metadata summarizer.
2. Document viewer: text extraction, read-only preview w/ optional inline edits (text only) saved as copy with timestamp (`filename_20250121_143022.pdf`). Always saves to Output directory.
3. Converter: format matrix (PDF⇄DOCX, RTF, TXT, ODT, HTML). For bulk operations, show progress bar with time remaining.
4. Search: In-memory index by default; for large/many files, creates persistent index in `temp/` folder. Query input, results grouped by file collapsibles (lazy-loaded); editing allowed inside each. Settings page includes "Clear temp data" to remove persistent indexes.
5. Page operations: move, append, remove with drag lists, preview images (PDF page render via pdf2image optional). Save as copy with timestamp.

### 9.3 Image Handler Flow
1. Upload/load; show gallery with key stats.
2. Converter: select formats (PNG, JPG, TIFF, WEBP, PDF) with timestamp rename (`filename_20250121_143022.png`). Always saves to Output directory. If already target format, copies with timestamp.
3. Compressor: slider for % reduction, estimate final size (current_size * factor), show progress with time remaining.
4. Cropper: interactive tool, aspect ratio presets, manual coordinates.
5. Single Image Combine: enforce 2-9 images, grid solver auto-fits layout (handles landscape/portrait mix), label strategy (filename/custom/autonum), ensures 300 DPI for OCR readability, saves PNG + metadata JSON to Output directory.

## 10. Data Management & Performance
- **File size**: No upload size cap; handles files of any size through chunked processing and streaming where applicable.
- **Caching**: `st.cache_data` for file stats, `st.cache_resource` for heavy libs; cache clears when Python app stops, persists during active session on localhost. TTL tied to file hash.
- **Fragments**: Wrap preview-heavy components; use `st.fragment` with session key to prevent rerun of unaffected fragments.
- **Chunked processing**: Process large files via `chunksize` (Pandas chunksize parameter); use progress bars with time remaining for long conversions (blocking UI with status updates).
- **Auto-sampling**: Datasets above 5,000 rows automatically show 10% preview; user can adjust via slider. No auto-sampling below 5k rows.
- **Data File Splitter**: Fragment large datasets into user-specified file sizes (e.g., 10MB chunks from 200MB source); creates labeled files in subfolder with optional zip.
- **Document search indexing**: In-memory dict by default; for large/many files, creates persistent Whoosh-like index in `temp/` folder. Settings page includes "Clear temp data" button.

## 11. Error Handling & Observability
- **Error classification**: Distinguish programmer vs operational errors (see structured logging strategy). Operational errors handled gracefully with user-friendly messages; programmer errors log as FATAL with full stack.
- **Error display**: Wrap every user-triggered action with try/except that surfaces friendly message + troubleshooting tips, logs detailed stack with `request_id`. Include optional "Show technical details" expandable section for advanced users.
- **Dependency errors**: If feature requires missing package, show "Feature unavailable: install X package" message instead of silent disable. Allow graceful degradation where possible.
- **Directory permissions**: If Input/Output directory requires admin rights or access denied, prompt user to select alternative location with clear messaging.
- **Activity log**: Persistent CSV logs in `logs/` folder storing `timestamp, level, message, module, requestId, userId, operation, duration, status`. Rotation strategy: size-based (max 50MB per file) and time-based (daily rotation). Settings page includes log viewer with download option.
- **Bulk operation verification**: Output→Input file mover deletes from Output only after successful copy verification. If file exists in Input, adds conflict suffix (`_conflict_20250121_143022`).

## 12. Packaging & Execution Plan
1. **`scripts/setup_app.py`**
   - Verify Windows (`platform.system()`), warn if not Windows (not tested on other systems).
   - List installed Python versions via `py -0p` (PowerShell-friendly).
   - User selects version; script builds venv (`python -m venv .venv_doczilla`).
   - Prompt for "app only" vs "app + tests" (installs dev dependencies if selected).
   - Install dependencies from pinned `requirements/` files (`base.txt`, `dev.txt`).
   - Create `logs/` and `temp/` directories.
   - Record config file with env path.
   - Tell user to run `run_app.py` now as installation is complete.
2. **`scripts/run_app.py`**
   - Check env exists & dependencies installed (import checks for core minimum requirements).
   - Run `streamlit run src/app/main.py`.

Distribute instructions in README for non-technical setup. Future cloud deployment: Streamlit Cloud (configurations deferred to later phase).

## 13. Testing Strategy
- **Comprehensive testing**: All functions, edge cases, UI components, error paths. MVP includes full test coverage.
- **Unit**: pandas cleaners, converters, file IO, utility functions, data operations (merge, group-by, outlier detection), phone/URL standardization, rapidfuzz similarity matching, fragment splitting logic (pytest + hypothesis where helpful).
- **Integration**: Simulate page flows using Streamlit testing utilities (streamlit-testing), verify conversions end-to-end with temp dirs, test caching behavior, test log persistence, test temp index creation/deletion.
- **E2E Smoke**: Use Playwright or Cypress component tests to ensure UI loads, upload workflow works (mock files), progress bars display correctly, bulk operations complete, error messages display properly.
- **Test data fixtures**: sample CSV/XLSX/PDF/image sets stored under `tests/fixtures`. Include large files (>5k rows) for auto-sampling tests, mixed file types for conversion tests, malformed files for error handling tests.
- **Edge cases**: Empty files, corrupted files, permission errors, missing dependencies, file conflicts, very large files, mixed encodings, special characters in filenames.
- CI (future): GitHub Actions matrix for Windows-latest + Python versions chosen by users.

## 14. Project Phasing
| Phase | Deliverables |
| --- | --- |
| Phase 0 (current) | Spec digestion, design dossier, repo scaffolding plan, project board setup, test data inventory definition. |
| Phase 1 | Repository scaffolding, setup/run scripts, base Streamlit skeleton (sidebar with 150x150 logo, multipage nav, title animation), logging/caching utilities (CSV logs, session-persistent cache), temp/logs directory structure. |
| Phase 2 | Data Handler feature set (ingest with no size cap, analysis with auto-sampling >5k rows, editing with user-configurable outlier thresholds, conversions with progress bars, Data File Splitter with user-specified sizes, phone/URL standardization with international support, rapidfuzz similarity merge) + comprehensive unit tests. |
| Phase 3 | Document Handler (viewer, in-memory search with temp index fallback, conversions with progress bars, page ops) + integration tests. |
| Phase 4 | Image Handler (convert/compress/crop/combine with 300 DPI grid, auto-fit layout) + performance tuning, progress indicators with time remaining. |
| Phase 5 | Settings page (directory selection with permission fallback, logo uploader, temp data cleanup, activity log viewer with CSV download, cache stats), watchdog integration, error handling with technical details toggle, dependency error messaging, packaging polish. |
| Phase 6 | QA hardening (comprehensive test coverage for all functions, edge cases, UI), Windows installer guide, documentation for content editors/end users, Streamlit Cloud preparation (deferred config). |

**MVP Scope**: All functions mentioned in spec, fully tested. No feature reduction—comprehensive implementation from start.

## 15. Supported File Formats & Conversion Matrix

### 15.1 Data File Formats
**Supported Formats**:
- **CSV** (Comma-separated, TSV tab-separated) - Full support
- **JSON** (JSON, JSONL) - Full support
- **XLSX** (Excel 2007+) - Full support
- **XLS** (Excel 97-2003) - Full support
- **TXT** (Plain text, delimited) - Full support
- **XML** - Full support (with xmltodict)
- **Parquet** - Read support (write via pandas)
- **Feather** - Read support (write via pandas)
- **ODS** (OpenDocument Spreadsheet) - Read support (write via pandas)

**Primary Library**: Pandas + pyarrow (Parquet/Feather)
**Fallback**: csv module, json module, openpyxl (XLSX/XLS)

### 15.2 Document File Formats
**Supported Formats**:
- **PDF** - Full support (text extraction, page manipulation)
- **DOCX** - Full support
- **DOC** - Read support (via docx2txt conversion)
- **RTF** - Read support (via pyth)
- **TXT** - Full support
- **ODT** - Read support (via python-docx or odfpy)
- **HTML** - Full support (read/write)

**Primary Libraries**: PyPDF2, python-docx, pdfminer.six, html2text
**Fallback**: docx2txt, pyth

### 15.3 Image File Formats
**Supported Formats**:
- **PNG** - Full support
- **JPG/JPEG** - Full support
- **TIFF** - Full support
- **WEBP** - Full support (Pillow 8.0+)
- **PDF** (as image container) - Full support (via img2pdf)
- **GIF** - Read support (write limited)
- **BMP** - Full support
- **SVG** - Read support (rendered to PNG for operations)
- **HEIC** - Read support (if pillow-heif installed)

**Primary Library**: Pillow (PIL)
**Fallback**: Wand (ImageMagick), cairosvg (SVG)

### 15.4 Conversion Matrix

#### Data File Conversions
| From → To | CSV | JSON | XLSX | XLS | TXT | XML | Parquet | Feather |
|-----------|-----|------|------|-----|-----|-----|---------|---------|
| **CSV** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **JSON** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **XLSX** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| **XLS** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| **TXT** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| **XML** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| **Parquet** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| **Feather** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |

**Note**: XLS format is write-only for newer Excel versions (XLSX preferred). All conversions preserve data; formatting (colors, fonts) may be lost.

#### Document Conversions
| From → To | PDF | DOCX | DOC | RTF | TXT | ODT | HTML |
|-----------|-----|------|-----|-----|-----|-----|------|
| **PDF** | ✓ | ⚠ | ✗ | ✗ | ✓ | ✗ | ✗ |
| **DOCX** | ✓ | ✓ | ✗ | ✗ | ✓ | ⚠ | ✓ |
| **DOC** | ✗ | ⚠ | ✓ | ✗ | ✓ | ✗ | ✗ |
| **RTF** | ✗ | ⚠ | ✗ | ✓ | ✓ | ✗ | ✗ |
| **TXT** | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ |
| **ODT** | ✗ | ⚠ | ✗ | ✗ | ✓ | ✓ | ✗ |
| **HTML** | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ |

**Legend**: ✓ = Full support, ⚠ = Partial support (formatting may be lost), ✗ = Not supported

**Limitations**:
- PDF→DOCX: Text-only, loses formatting/structure
- DOC/DOCX→RTF: May lose advanced formatting
- HTML→PDF: Requires rendering engine (limited support)

#### Image Conversions
| From → To | PNG | JPG | TIFF | WEBP | PDF | GIF | BMP |
|-----------|-----|-----|------|------|-----|-----|-----|
| **PNG** | ✓ | ✓ | ✓ | ✓ | ✓ | ⚠ | ✓ |
| **JPG** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| **TIFF** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| **WEBP** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| **GIF** | ✓ | ✓ | ✓ | ⚠ | ✓ | ✓ | ✓ |
| **BMP** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| **SVG** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |

**Note**: GIF→WEBP and WEBP→GIF have limitations. SVG is rendered to raster first.

## 16. Design Decisions & Specifications

### File Handling
- **No file size cap**: Users can upload files of any size; processing uses chunked/streaming where applicable.
- **Auto-sampling thresholds**: 
  - Auto-sample if: rows > 5,000 OR columns > 100 (spec reconciliation: use 5k rows OR 100 cols)
  - Show 10% preview by default (min 100 rows), adjustable via slider
  - Slider range: 1% to 100% of dataset
- **File naming**: Timestamp format `filename_20250121_143022.xlsx` (always saves to Output directory).
  - If timestamp collision (same second), add sequence: `filename_20250121_143022_001.xlsx`
  - Sanitize special characters (replace with underscore)
  - Truncate if filename > 200 characters (Windows compatibility)
- **File conflicts**: If file exists in Input, adds suffix `_conflict_20250121_143022`.
- **Output→Input mover**: Deletes from Output only after successful copy verification.
- **Encoding detection**: Auto-detect encoding using `chardet` library, default to UTF-8, allow manual override.

### Data Operations

#### Merge Operations
- **Join types**: Support inner, outer, left, right joins (default: inner)
- **Similarity matching**: rapidfuzz token_set_ratio with 80% threshold for "merge on similar"
  - User can select columns to match
  - Only applies to text data (string columns)
- **Column selection**: User selects columns to include in merged result
- **Column conflicts**: User chooses: add underscore prefix to original name, keep set 1 (original), or keep set 2 (incoming)
- **Duplicate keys**: Preserve all matches (no automatic deduplication)

#### Group By Operations
- **Aggregation functions**: count, sum, mean, min, max, median, std, first, last, nunique
- **Multi-column grouping**: Support grouping by multiple columns
- **Multi-aggregation**: Allow multiple aggregation functions on same column
- **Output**: Display in UI with "Save Result" button to export; originals preserved

#### Data Editing
- **UI**: Use Streamlit's `st.data_editor` for inline cell editing
- **Actions**: Add/remove rows and columns via toolbar buttons
- **Save workflow**: Edits staged in session state, "Save Changes" button commits to file
- **Find/Replace**: Support bulk find/replace across selected columns
- **Undo**: Single-level undo for last edit operation (session-based)

#### Data Cleaning
- **Remove empty rows/columns**: Remove where ALL cells are empty or whitespace-only
  - Show preview count before removal
- **Handling missing values**: User selects columns, choose fill strategy (N/A, 0, mean, forward fill, backward fill)
- **Remove duplicates**: User selects columns for matching; all selected columns must match to count as duplicate
  - Option: keep first or keep last occurrence
- **Standardize format**: Select numeric column, choose decimal places or scientific notation
- **Remove empty space**: Trim leading/trailing whitespace from selected columns
- **Remove characters**: User provides comma or space-separated list of characters
  - Support regex mode with toggle (escapes special characters)
  - Examples: `a, b, c` or `[0-9]` (regex)

#### Outlier Detection
- **Methods**: Z-score (default threshold 3.0) and IQR (default 1.5 × IQR)
- **User-configurable**: Threshold adjustable in UI via slider
- **Display**: Show rows with outliers, allow user to delete, edit, or keep
- **Categorical handling**: For non-numeric columns, use mode-based detection

#### Phone Number Standardization
- **Formats supported**: 
  - E.164: `+1234567890`
  - National (US): `(123) 456-7890`
  - International: `+1 234 567 8900`
  - Dashed: `123-456-7890`
  - Custom format (user-defined pattern)
- **Country code**: Auto-detect using `phonenumbers` library, allow manual override
- **Output**: Creates new column to right of selected column

#### URL Standardization
- **Component selection**: Checkboxes for protocol, domain, path, query, fragment
- **Presets**: 
  - Full URL: `https://example.com/pathhere?query=1`
  - Base domain: `example.com`
  - Domain + path: `example.com/pathhere`
- **Normalization**: Lowercase domain, remove default ports (80, 443), remove www prefix option
- **Output**: Creates new column to right of selected column

### Document Search
- **Default**: In-memory dict index (simple string matching per file)
- **Fallback**: For large/many files (threshold: >10 files OR total size >100MB), creates persistent Whoosh-like index in `temp/` folder
- **Search scope**: Search across all uploaded documents in current session
- **Results**: Grouped by file in collapsible sections (lazy-loaded)
- **Editing**: Allow inline text editing within search results, save as copy
- **Cleanup**: Settings page includes "Clear temp data" button (removes persistent indexes)
- **Auto-cleanup**: Temp indexes auto-deleted on app close (optional setting)

### Document Operations

#### Text Editing
- **Scope**: Text-only editing, preserves document structure (sections, paragraphs) but not formatting (bold, italic)
- **UI**: Plain text editor with syntax highlighting for structure markers
- **Preservation**: Paragraph breaks, headers, lists preserved
- **Metadata**: Allow editing document metadata (title, author) separately
- **Conversion impact**: Editing text-only; if converting PDF→DOCX→edit→DOCX, formatting may be lost

#### Page Operations
- **Move pages**: Batch operation mode
  - Queue multiple page moves before executing
  - Preview before final save
  - Validate no conflicts (e.g., moving page 5 to pos 3, then page 3 to pos 5)
  - Allow undo of queued moves before saving
  - Save creates copy with timestamp
- **Append documents**: 
  - User selects first document, then multi-select others in order
  - Convert all to same format if mixed formats (prompt user for target format)
  - Handle page size differences (standardize to first document or user choice)
  - Preserve page breaks as section breaks
- **Remove pages**: Multi-select pages to remove, preview result, save as copy

### Image Processing

#### Image Grid Combine
- **Layout**: 3-column grid with auto-fit rows (max 9 images total, confirms 3×3)
- **Spacing**: 20px white space between rows, 10px between columns
- **Labeling**: 
  - Position: Below each image
  - Options: Use filename, custom label (iterates: 1, 2, 3...), or no label
- **Aspect ratio handling**: Landscape images can span multiple cells (e.g., full row width)
- **DPI**: Default 300 DPI for OCR readability, allow user selection (150, 300, 600) with file size estimate
- **Output**: Single PNG file + metadata JSON (positions, labels) saved to Output directory
- **Quality vs size**: Warn user if output exceeds 100MB, offer lower DPI option

#### Image Compression
- **PNG**: Use lossy conversion to JPG (recommended) or PNG optimization (limited savings)
- **JPG**: Quality slider 0-100 (100 = original, 70 = good balance, 50 = smaller file)
- **TIFF**: LZW compression by default, option for ZIP compression
- **WEBP**: Quality slider 0-100
- **Metadata preservation**: Preserve EXIF data by default, option to strip (for privacy)
- **Output estimate**: Show combined file size estimate before compression

#### Image Cropping
- **Tool**: Use `st_cropper` library or custom implementation with absolute pixel coordinates
- **Aspect ratio presets**: Square (1:1), 4:3, 16:9, custom
- **Lock aspect ratio**: When preset selected, lock aspect ratio (resize box maintains ratio)
- **Resize**: User can drag corners/edges to resize crop box
- **Bounds**: Prevent crop exceeding image boundaries
- **Coordinates**: Display crop coordinates (x, y, width, height) for reference

### UI/UX
- **Logo**: 150x150px in sidebar (user-uploadable).
- **Title animation**: Typewriter/fade-in effect for app name, preserves "Part of the SPEAR Toolkit" static text.
- **Progress bars**: Show time remaining estimate for bulk operations.
- **Error display**: Friendly messages with optional "Show technical details" toggle; dependency errors: "Feature unavailable: install X package".
- **Directory permissions**: User selects alternative location if access denied.

### Caching & Logging
- **Cache**: Clears when Python app stops, persists during active session on localhost.
- **Logs**: Persistent CSV in `logs/` folder with rotation (50MB max per file, daily rotation).
- **Temp data**: Persistent indexes stored in `temp/` folder (clearable via Settings).

### Testing
- **Coverage**: Comprehensive testing of all functions, edge cases, UI components, error paths.
- **MVP**: All spec functions fully tested from Phase 1.

### Cloud Deployment
- **Target**: Streamlit Cloud (deferred to later phase, no cloud-specific configs in initial phases).

## 17. Technical Implementation Details

### 17.1 Streamlit Fragments
**Components wrapped in `@st.fragment`**:
- Data preview panel (`data_handler.py`)
- Metadata viewer (collapsible sections)
- Document search results (lazy-loaded collapsibles)
- Image grid composer (preview during layout)
- Large dataset statistics (file analysis results)

**Rationale**: Prevents full app rerun when user interacts with these heavy components, improving performance.

### 17.2 Cache Strategy
- **Cache keys**: Include file hash (SHA256) + modification time (mtime)
- **Invalidation triggers**: 
  - File edited in UI
  - File deleted from Input directory
  - External modification detected (mtime changed)
  - User manually clears cache
- **TTL**: Tied to file hash (infinite until invalidation triggers)
- **Storage**: `st.cache_data` for file contents, `st.cache_resource` for heavy library objects

### 17.3 File Hash Algorithm
- **Algorithm**: SHA256 (secure, collision-resistant)
- **Purpose**: Cache keys, duplicate detection, change tracking
- **Implementation**: `hashlib.sha256(file_content).hexdigest()`

### 17.4 Session & Request IDs
- **Session ID**: UUID v4 format (e.g., `550e8400-e29b-41d4-a716-446655440000`)
  - Generated on app start
  - Stored in `st.session_state.session_id`
- **Request ID**: UUID v4 format (correlation ID for each user action)
  - Generated per user-triggered operation
  - Included in all logs and error messages
  - Enables tracing request journey across services

### 17.5 Configuration File Format
- **Format**: JSON
- **Location**: `src/app/config/app_config.json` (user-editable)
- **Default location**: Create from `config_template.json` on first run
- **Settings**: 
  - Input/Output directory paths
  - Logo paths (per page)
  - Cache settings (enable/disable, TTL)
  - Watchdog settings (enable/disable, polling interval)
  - Log rotation settings

### 17.6 Log Rotation Implementation
- **Format**: CSV files with headers
- **Naming**: `activity_YYYYMMDD_HHMMSS.csv`
- **Rotation triggers**:
  - Size-based: When file exceeds 50MB, rotate to new file
  - Time-based: Daily rotation at midnight (keep last 30 days)
- **Archival**: Move old logs to `logs/archive/` folder (auto-delete after 90 days)
- **Fields**: `timestamp, level, message, module, requestId, userId, operation, duration, status, file_path, error_details`

### 17.7 Temp Index Cleanup
- **Cleanup strategy**: 
  - Manual: "Clear temp data" button in Settings (removes all `temp/` contents)
  - Auto on close: Optional setting (enabled by default)
  - Auto on stale: Remove indexes older than 7 days on app start
- **Index location**: `temp/search_indexes/` (organized by session ID or timestamp)

### 17.8 Watchdog Directory Monitoring
- **Library**: `watchdog` (Python file system events)
- **Polling interval**: Default 1 second (configurable in Settings: 0.5s to 5s)
- **Events watched**: File created, deleted, moved (ignore modifications to prevent loops)
- **Performance**: Limit to watching Input/Output directories only (not subdirectories)
- **Auto-refresh**: Optional toggle (enabled by default) - refresh UI when files detected
- **Manual refresh**: Always available via "Refresh" button

### 17.9 Error Recovery & Partial Failures
- **Bulk operations**: Continue processing if some files fail
  - Collect failed files and errors
  - Show summary at end with success/failure counts
  - Allow retry of failed files
  - Save successful results even if some fail
- **Conversion failures**: 
  - Log detailed error (file, reason, suggestion)
  - Skip failed file, continue with others
  - Report in summary with "Show technical details" option

### 17.10 Progress Indicator Implementation
- **ETA calculation**: Exponential moving average of processing rate
  - Formula: `new_eta = alpha * current_rate + (1 - alpha) * previous_eta`
  - Alpha: 0.3 (weighted toward recent rates)
- **Update frequency**: Throttled to 1 update per second (prevents UI lag)
- **Display**: Progress bar with percentage, items processed, ETA (e.g., "45% | 23/50 files | ~2 min remaining")

### 17.11 Encoding Detection
- **Library**: `chardet` (auto-detect encoding)
- **Fallback**: UTF-8 if detection confidence < 0.7
- **Manual override**: Allow user to select encoding if auto-detection fails
- **Common encodings**: UTF-8, Latin-1, Windows-1252, CP1252, ISO-8859-1

### 17.12 Zip File Handling
- **Format**: ZIP64 (supports files >4GB)
- **Library**: `zipfile` (Python standard library with ZIP64 support)
- **Progress**: Show progress bar during zip creation
- **Failure handling**: Continue even if zip creation fails (files still saved individually)
- **Compression level**: Default 6 (balanced), configurable (0-9)

### 17.13 PDF Text Extraction Strategy
- **Primary**: PyPDF2 (fast, handles text-based PDFs)
- **Fallback 1**: pdfminer.six (better for complex layouts, scanned PDFs)
- **Fallback 2**: pypdf (alternative library)
- **Quality detection**: If extraction yields <10% of expected text, warn user (may be scanned PDF)
- **OCR note**: Inform user that scanned PDFs may need external OCR tool

### 17.14 Memory Management for Large Files
- **Chunked reading**: Use `pandas.read_csv(chunksize=10000)` for large CSVs
- **Streaming**: Stream file content where possible (don't load entire file into memory)
- **Warning threshold**: Warn user if file size >500MB or rows >1M (may cause slowdown)
- **Memory monitoring**: Track memory usage, warn if >80% system RAM used
- **Cache limits**: Limit cache size to 2GB (FIFO eviction if exceeded)

## 18. Edge Cases & Error Handling

### 18.1 File Validation Edge Cases
- **Empty files**: Show warning, allow user to skip or process (may create empty output)
- **Corrupted files**: Attempt recovery, if fails show error with file name and suggestion
- **Unsupported format**: Check extension and MIME type, suggest conversion or rejection
- **Mixed encodings in same file**: Default to detected encoding, warn about potential issues
- **Special characters in filenames**: Sanitize but preserve original name in metadata

### 18.2 Data Operation Edge Cases
- **Merge with no matching keys**: 
  - Inner join: Return empty DataFrame with message
  - Outer/Left/Right: Return all rows with NaN for unmatched columns
- **Group by with all null values**: Return single group with NaN key
- **Outlier detection on empty column**: Skip column, warn user
- **Phone number parsing failure**: Leave original value, add new column with parse status

### 18.3 Document Operation Edge Cases
- **PDF with no extractable text**: Warn user, allow manual text entry or skip
- **Page move to same position**: Ignore move, no-op
- **Append documents with different page sizes**: Standardize to first document size (option to choose)
- **Remove all pages**: Prevent deletion (require at least 1 page)

### 18.4 Image Operation Edge Cases
- **Image too large for grid**: Warn user, suggest compression or cropping first
- **Crop outside image bounds**: Prevent crop, show error message
- **Compression results in larger file**: Warn user (rare with JPG), suggest different quality
- **Unsupported color space**: Convert to RGB before processing, warn user

### 18.5 System Edge Cases
- **Disk space full during save**: Check available space before operation, show error if insufficient
- **File locked by another process**: Retry with exponential backoff (3 attempts), then show error
- **Network timeout (if future cloud feature)**: Implement retry logic with exponential backoff
- **Watchdog events during file operation**: Queue events, process after current operation completes

## 19. Performance Optimization Strategies

### 19.1 Data Loading
- **Lazy loading**: Load files only when user selects them (not on page load)
- **Parallel processing**: Use multiprocessing for bulk operations (conversion, splitting)
- **Caching**: Cache file analysis results (stats, schema) to avoid recalculation

### 19.2 UI Rendering
- **Virtual scrolling**: For large DataFrames, render only visible rows (if >1000 rows)
- **Debouncing**: Debounce search input (500ms delay) to avoid excessive index queries
- **Pagination**: Paginate metadata display (show 20 items per page)

### 19.3 File I/O
- **Async operations**: Use asyncio for file I/O where possible (non-blocking)
- **Batch writes**: Buffer multiple small writes, flush in batches
- **Compression**: Compress temporary files to reduce I/O (uncompress on read)

## 20. Next Steps
1. Validate this design with stakeholders; capture approvals/changes.
2. Initialize git repo, add base README, requirements skeleton, project templates.
3. Prepare backlog issues aligned to phases and component breakdown above.
4. Create technical specification document (see `TECHNICAL_SPEC.md`).


