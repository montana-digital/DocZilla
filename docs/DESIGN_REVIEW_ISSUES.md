# DocZilla Design Review - Issues & Clarifications Needed

## Critical Clarifications Needed

### 1. File Format Support Matrix
**Issue**: Spec says "any other Data File that is popular" but doesn't define which formats are supported.

**Questions**:
- What are the exact data file formats supported? (CSV, JSON, XLSX, XLS, TXT, XML are mentioned, but what about Parquet, Feather, TSV, ODS?)
- What document formats are supported? (PDF, DOC, DOCX, RTF, TXT, ODT, HTML - any others?)
- What image formats are supported? (PNG, JPG, TIFF, WEBP, PDF - what about GIF, BMP, SVG, HEIC?)
- Need complete conversion matrix: which formats can convert to which?

**Recommendation**: Define explicit supported formats list and conversion matrix in design doc.

---

### 2. Conversion Matrix Details
**Issue**: Design mentions conversion registry but doesn't specify which conversions are actually possible.

**Questions**:
- Can PDF convert to DOCX? (Lossy - may lose formatting)
- Can DOCX convert to PDF? (Usually possible)
- Can XLSX convert to CSV? (Yes, but may lose formatting)
- Can CSV convert to XLSX? (Yes)
- What about edge cases: PDF→TXT (text extraction), HTML→PDF (requires rendering)?

**Recommendation**: Document full conversion matrix with success probability and known limitations.

---

### 3. Data File Splitter - Split Method
**Issue**: Spec mentions splitting by file size (10MB chunks) but doesn't address splitting by row count.

**Questions**:
- Should users be able to split by:
  - File size only (e.g., 10MB)?
  - Row count only (e.g., 100,000 rows per file)?
  - Both (size OR rows)?
- What happens if a single row exceeds target file size?
- Should header row be included in every split file?

**Recommendation**: Support both methods, with clear UI to choose. Always include headers in split files.

---

### 4. Large File Threshold Inconsistency
**Issue**: Spec says "over 10,000 rows OR 100 columns" triggers 10% view, but design doc says 5,000 rows.

**Questions**:
- Which threshold is correct?
- Should it be OR (10k rows OR 100 cols) or AND (both conditions)?
- Should column count have a separate threshold?

**Recommendation**: Clarify thresholds in design doc:
- Auto-sample if: rows > 5,000 OR columns > 100
- Show 10% preview by default, adjustable via slider

---

### 5. Data Editing UI & Capabilities
**Issue**: Spec mentions "edit the data file - add or remove columns and rows" but lacks detail on editing scope.

**Questions**:
- Can users edit individual cell values inline?
- Can users edit via a data grid widget (like st.data_editor)?
- Are edits applied immediately or require "Save" button?
- Can users undo edits?
- What about bulk editing (find/replace)?

**Recommendation**: Use Streamlit's `st.data_editor` for inline editing with "Save Changes" button. Support find/replace.

---

### 6. Merge Operations - Join Types
**Issue**: Spec mentions merge but doesn't specify join types.

**Questions**:
- Which join types supported? (inner, outer, left, right)
- Default join type?
- What happens with duplicate key values?
- Should merge preserve all columns or allow selection?

**Recommendation**: Support inner, outer, left, right joins. Default to inner. User selects columns to include.

---

### 7. Group By Aggregation Functions
**Issue**: Spec says "Count, Sum, etc" but doesn't list all available functions.

**Questions**:
- Which aggregation functions? (count, sum, mean, min, max, median, std, first, last, unique)
- Can users apply multiple aggregations to same column?
- Can users group by multiple columns?

**Recommendation**: Support standard pandas aggregations: count, sum, mean, min, max, median, std, first, last, nunique. Multi-column grouping and multi-aggregation.

---

### 8. Document Text Editing - Formatting Preservation
**Issue**: Spec says "text only editing" and "preserve structure" but unclear what's preserved.

**Questions**:
- Can users edit text while preserving:
  - Bold/italic formatting?
  - Paragraph structure?
  - Headers/tables/images?
- What happens to formatting if converting PDF→DOCX→edit→DOCX?
- Can users edit metadata (title, author, etc.)?

**Recommendation**: Text-only editing preserves structure but not formatting details. Editing creates plain text version, conversion may lose formatting.

---

### 9. Page Move Operations - Batch vs Sequential
**Issue**: Spec says user can "select another page to move" implying multiple moves, but workflow unclear.

**Questions**:
- Can user queue multiple page moves before executing?
- Is there a preview before final save?
- What if move conflicts (move page 5 to position 3, then move page 3 to position 5)?
- Can user undo moves before saving?

**Recommendation**: Allow batch moves with preview. Queue moves, validate no conflicts, show preview, then save.

---

### 10. Image Grid Layout Specifications
**Issue**: Spec says "Grid of 3" but ambiguous - 3 columns? 3x3? Also spacing details missing.

**Questions**:
- "Grid of 3" means 3 columns, variable rows?
- Or 3x3 fixed grid (9 images max confirmed)?
- What is "distinct white space between each row" - exact pixels?
- What about spacing between columns?
- How are labels positioned? (Above image, below, overlay?)

**Recommendation**: Clarify: 3-column grid, auto-fit rows. White space: 20px between rows, 10px between columns. Labels below images.

---

### 11. Image Compression - Algorithm & Format Support
**Issue**: Spec says "percentage to compress" but compression is format-dependent.

**Questions**:
- PNG: Lossless or lossy? (PNG is lossless, so compression limited)
- JPG: Quality setting? (0-100?)
- TIFF: Compression method? (LZW, ZIP, JPEG?)
- What about GIF, WEBP?
- Should compression preserve metadata (EXIF, etc.)?

**Recommendation**: 
- PNG: Use lossy conversion to JPG or use PNG optimization (limited savings)
- JPG: Quality slider (0-100, where 100=original)
- TIFF: LZW compression by default
- Preserve EXIF metadata where possible

---

### 12. Watchdog Directory Monitoring - Performance Concerns
**Issue**: Watching Input/Output directories could be resource-intensive.

**Questions**:
- Polling interval? (watchdog default or configurable?)
- What if thousands of files in directory?
- Should monitoring be optional (enable/disable)?
- What events to watch? (create, modify, delete, move)
- Should changes trigger auto-refresh of UI?

**Recommendation**: Default 1-second polling, configurable in Settings. Watch create/delete events. Optional auto-refresh toggle.

---

### 13. Session State & Cache Invalidation
**Issue**: Cache strategy needs more detail on invalidation.

**Questions**:
- If user edits a file in UI, does cache invalidate?
- If user deletes a file from Input dir, does cache clear?
- What if same file modified externally?
- Should cache keys include file modification time?

**Recommendation**: Cache keys include file hash + modification time. Invalidate on edit/delete. Clear on external modification detection.

---

### 14. File Naming - Timestamp Format & Conflicts
**Issue**: Spec defines format but doesn't address edge cases.

**Questions**:
- What if filename already has timestamp? (Avoid duplicate timestamps?)
- What if filename has special characters? (Sanitize? Escape?)
- What about very long filenames? (Windows 260 char limit)
- What if timestamp collision (same second)? (Add sequence number?)

**Recommendation**: Sanitize special characters. If collision, add sequence: `filename_20250121_143022_001.xlsx`. Truncate if > 200 chars.

---

### 15. Data Validation - Schema Checking
**Issue**: Spec mentions "valid file structure" but doesn't define validation rules.

**Questions**:
- For CSV: What if inconsistent columns?
- For JSON: What if malformed?
- For XLSX: What if corrupted?
- Should validation be strict (reject) or lenient (fix/warn)?

**Recommendation**: Try to auto-fix (warn user), but reject if unfixable. Log all validation issues.

---

### 16. Partial Conversion Failures - Recovery
**Issue**: In bulk conversions, what if some files fail?

**Questions**:
- Continue with successful files or abort all?
- Report failures immediately or batch at end?
- Allow retry of failed files?
- Should partial results be saved or discarded?

**Recommendation**: Continue with successful files, report failures in summary, allow retry, save partial results.

---

### 17. Document Structure Preservation
**Issue**: Spec says "preserve structure" but doesn't define scope.

**Questions**:
- What about embedded images in PDF/DOCX?
- What about tables, headers, footers?
- What about hyperlinks, bookmarks?
- Can structure be preserved in all conversion paths?

**Recommendation**: Document which conversions preserve structure vs. plain text only. Most conversions are text-only unless using advanced libraries.

---

### 18. Image Metadata Preservation
**Issue**: Image operations should preserve EXIF/metadata, but not specified.

**Questions**:
- Preserve EXIF data during conversion/compression?
- Preserve metadata during cropping?
- What about copyright, GPS, camera info?

**Recommendation**: Preserve metadata by default, with option to strip (for privacy).

---

### 19. Zip File Handling - Large Archives
**Issue**: Spec mentions zipping bulk outputs but doesn't address size limits.

**Questions**:
- What if zip file exceeds 4GB? (32-bit zip limit)
- Should use zip64 format?
- Progress indicator for zipping?
- What if zip creation fails partway through?

**Recommendation**: Use zip64 for large archives. Show progress. Continue even if zip fails (files still saved).

---

### 20. Progress Indicators - Accuracy & Performance
**Issue**: Time remaining estimates need implementation details.

**Questions**:
- How to calculate ETA? (Simple average? Exponential moving average?)
- What if operation time varies wildly?
- Should progress update frequency be throttled? (Every N seconds?)

**Recommendation**: Exponential moving average for ETA. Throttle updates to 1/second to avoid UI lag.

---

### 21. Group By & Merge - Output Format
**Issue**: Results of group-by/merge operations - where do they go?

**Questions**:
- Display in UI only or auto-save to Output?
- Can user export result to file?
- Should original files be preserved?

**Recommendation**: Display in UI, with "Save Result" button to export. Originals always preserved.

---

### 22. Crop Tool - Coordinate System
**Issue**: Spec mentions "custom crop using mouse" but lacks technical details.

**Questions**:
- Absolute coordinates (pixels) or relative (percentage)?
- What if crop exceeds image bounds?
- Can user resize crop box?
- Aspect ratio lock when using presets?

**Recommendation**: Use `st_cropper` library or build with absolute pixel coordinates. Lock aspect ratio when preset selected.

---

### 23. Metadata Display - Format & Completeness
**Issue**: Spec mentions metadata but doesn't specify what to show.

**Questions**:
- For data files: file size, rows, cols, dtypes, encoding, created/modified dates?
- For documents: page count, author, title, creation date, PDF version?
- For images: dimensions, DPI, color space, EXIF?
- How much detail? (Collapsible sections?)

**Recommendation**: Show core metadata (size, rows/cols/pages, dates). Full details in collapsible sections.

---

### 24. Load from Input Directory - Detection & UI
**Issue**: Spec says "detect compatible files" but workflow unclear.

**Questions**:
- On app start, scan Input dir and show "Load" button?
- Or user clicks "Load from Input Dir" and then shows files?
- How to handle files that were already loaded in session?
- Should there be file filtering (show only supported formats)?

**Recommendation**: Scan Input dir on page load. Show "Load from Input Dir" button that lists compatible files. Highlight already-loaded files.

---

### 25. Phone Number Formats - Specific Options
**Issue**: Spec says "select which format" but doesn't list format options.

**Questions**:
- E.164 format? (`+1234567890`)
- National format? (`(123) 456-7890`)
- International format? (`+1 234 567 8900`)
- Custom format support?
- How many format options should be provided?

**Recommendation**: Support common formats: E.164, National (US style), International (with spaces), (123) 456-7890, 123-456-7890.

---

### 26. URL Standardization - Component Selection UI
**Issue**: Spec mentions selecting components but UI unclear.

**Questions**:
- Checkboxes for each component? (protocol, domain, path, query, fragment)
- Or dropdown with presets? (Full URL, Base domain, Domain + path)
- What about URL normalization? (lowercase, remove default ports, etc.)

**Recommendation**: Checkboxes for components + presets (Full URL, Base Domain, Domain + Path). Normalize (lowercase domain, remove www, etc.).

---

### 27. Outlier Detection - Method Selection
**Issue**: Spec mentions outlier detection but doesn't specify methods.

**Questions**:
- Z-score threshold? (Default 3?)
- IQR method? (1.5 * IQR rule?)
- Can user choose method per column?
- What about categorical columns?

**Recommendation**: Support both methods, user selects. Z-score default=3, IQR default=1.5. Handle categorical (mode-based).

---

### 28. Empty Row/Column Removal - Definition
**Issue**: Spec says "remove empty rows/columns" but definition unclear.

**Questions**:
- All cells empty? Or any cell empty?
- What about rows with only whitespace?
- Should removal be undoable?

**Recommendation**: Remove rows/columns where ALL cells are empty or whitespace-only. Show preview before removal.

---

### 29. Character Removal - Input Method
**Issue**: Spec says "provide a list of characters in an input" but format unclear.

**Questions**:
- Comma-separated? (`a, b, c`)
- Space-separated?
- Regex support? (`[a-z]`)
- Special character escaping?

**Recommendation**: Comma or space-separated list. Support regex with toggle. Escape special chars (`, `, `[`, `]`, etc.).

---

### 30. Document Append - Format Handling
**Issue**: Spec says append documents but doesn't address format differences.

**Questions**:
- Can append PDF to DOCX? (Convert first?)
- What if page sizes differ?
- What if one document has headers/footers?
- Should append create section breaks?

**Recommendation**: Convert all to same format before appending, or reject if formats incompatible. Preserve page breaks as section breaks.

---

## Potential Implementation Issues

### A. Memory Management
**Issue**: Large files (200MB+, 900k rows) could cause memory issues.

**Recommendation**: Use chunked processing, stream where possible, warn user if memory constraints detected.

---

### B. Encoding Detection
**Issue**: CSV/TXT files may have various encodings (UTF-8, Latin-1, Windows-1252).

**Recommendation**: Use `chardet` library for auto-detection, allow manual override, default to UTF-8.

---

### C. PDF Text Extraction Quality
**Issue**: PDF text extraction varies by PDF structure (text-based vs scanned).

**Recommendation**: Try multiple libraries (PyPDF2, pdfminer.six), fallback gracefully, warn if extraction poor.

---

### D. Image Quality vs File Size Trade-off
**Issue**: 300 DPI for OCR may create very large files.

**Recommendation**: Allow user to choose DPI (150, 300, 600) with file size estimate.

---

### E. Concurrent File Operations
**Issue**: Multiple users or rapid operations could cause file locking on Windows.

**Recommendation**: Implement file locking checks, retry with backoff, clear error messages.

---

## Missing Technical Details

1. **Streamlit Fragment Implementation**: Which specific components wrapped? List explicitly.
2. **Error Recovery Mechanisms**: Retry logic for network operations? (Not applicable, but pattern needed)
3. **Configuration File Format**: JSON, YAML, INI? Where stored?
4. **Log Rotation Implementation**: Circular buffer? Archival strategy?
5. **Temp Index Cleanup**: Automatic (on app close) or manual only?
6. **File Hash Algorithm**: MD5, SHA256? For cache keys.
7. **Session ID Generation**: UUID? Format?
8. **Request ID Generation**: UUID? Correlation with session?

---

## Recommendations for Design Doc Update

1. Add "Supported File Formats" section with complete matrix.
2. Add "Conversion Matrix" section with success rates and limitations.
3. Add "Data Operations Reference" with all functions and options.
4. Add "UI Component Specifications" with exact widgets and layouts.
5. Add "Error Handling Patterns" with specific scenarios.
6. Add "Performance Considerations" section with optimization strategies.
7. Add "Edge Cases" section with handling approaches.

---

*Last Updated: Phase 0 Design Review*
*Priority: Address before Phase 1 implementation*

