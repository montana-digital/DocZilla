# DocZilla Design Decisions Summary

This document captures all key design decisions made during Phase 0 design review.

## File Handling & Performance

### File Size
- **Decision**: No upload size cap; supports unlimited file sizes
- **Rationale**: Users need to process very large files (e.g., 900k row spreadsheets, 200MB files)
- **Implementation**: Chunked processing and streaming where applicable

### Auto-Sampling
- **Decision**: Auto-sample datasets above 5,000 rows (10% preview, adjustable via slider)
- **Rationale**: Prevents UI slowdown while allowing access to large datasets
- **Implementation**: Slider in UI to adjust preview range

### File Naming
- **Decision**: Timestamp format `filename_20250121_143022.xlsx`
- **Rationale**: Prevents overwrites, clear chronological ordering
- **Implementation**: All saved files (never overwrite originals)

### Save Location
- **Decision**: Always save to Output directory (never overwrite originals)
- **Rationale**: Data safety, prevents accidental loss
- **Implementation**: All conversions, edits, splits save with timestamp

### File Conflicts
- **Decision**: If file exists in Input, add suffix `_conflict_20250121_143022`
- **Rationale**: Allows file mover to work even if destination exists

## Data Operations

### Similarity Matching (Merge)
- **Decision**: rapidfuzz `token_set_ratio` with 80% threshold
- **Rationale**: Handles formatting differences while maintaining accuracy
- **Implementation**: User-selectable columns for matching

### Outlier Detection
- **Decision**: User-configurable threshold in UI (z-score, IQR methods)
- **Rationale**: Different datasets need different sensitivity
- **Implementation**: Slider/input in UI for threshold adjustment

### Phone Number Standardization
- **Decision**: International support with auto-detection of country code
- **Library**: `phonenumbers` package with regex fallback
- **Rationale**: Global user base needs international format support

### URL Standardization
- **Decision**: 
  - Full URL: `https://example.com/pathhere`
  - Base domain: `example.com`
  - User selects components (protocol, path, query, fragment)
- **Rationale**: Flexible URL formatting for different use cases

## Document Search

### Indexing Strategy
- **Decision**: In-memory dict by default; persistent index in `temp/` for large/many files
- **Rationale**: Fast for small sets, efficient for large document collections
- **Implementation**: Settings page includes "Clear temp data" button

## Image Processing

### Grid Combine
- **Decision**: 300 DPI output, auto-fit layout, max 9 images per grid
- **Rationale**: Optimized for OCR readability while maintaining reasonable file sizes
- **Implementation**: Handles landscape/portrait mix intelligently

## UI/UX

### Logo
- **Decision**: 150x150px in sidebar (user-uploadable)
- **Rationale**: Consistent branding, appropriate size for sidebar

### Title Animation
- **Decision**: Typewriter/fade-in effect for app name, preserves "Part of the SPEAR Toolkit" static text
- **Rationale**: Matches example style, maintains brand association

### Progress Indicators
- **Decision**: Show time remaining estimate for bulk operations
- **Rationale**: User needs visibility into long-running tasks
- **Implementation**: Progress bar with ETA calculation

### Error Display
- **Decision**: Friendly messages with optional "Show technical details" toggle
- **Rationale**: Accessible to non-technical users, helpful for troubleshooting
- **Implementation**: Expandable section with full stack traces

### Dependency Errors
- **Decision**: Show "Feature unavailable: install X package" instead of silent disable
- **Rationale**: Clear communication about missing features

### Directory Permissions
- **Decision**: User selects alternative location if access denied
- **Rationale**: Graceful handling of permission issues

## Caching & Logging

### Cache Persistence
- **Decision**: Clears when Python app stops, persists during active session on localhost
- **Rationale**: Balance between performance and resource usage

### Log Format
- **Decision**: Persistent CSV in `logs/` folder
- **Rationale**: Easy to parse, view in Excel, analyze
- **Rotation**: 50MB max per file, daily rotation

### Temp Data
- **Decision**: Persistent indexes in `temp/` folder (clearable via Settings)
- **Rationale**: Reuse indexes across sessions for large document sets

## Testing

### Coverage Scope
- **Decision**: Comprehensive testing of all functions, edge cases, UI components, error paths
- **MVP**: All spec functions fully tested from Phase 1
- **Rationale**: Quality from the start, prevents technical debt

## Data File Splitter

### Purpose
- **Decision**: User specifies target file size (e.g., 10MB); splits large source into chunks
- **Example**: 200MB file → 20 files of 10MB each
- **Rationale**: Some systems have file size limits; users need to split data

## Cloud Deployment

### Target Platform
- **Decision**: Streamlit Cloud (deferred to later phase)
- **Rationale**: Focus on desktop app first, cloud configs can be added later

## Dependencies

### Philosophy
- **Decision**: Use libraries as needed (no artificial restrictions)
- **Rationale**: Best tools for the job, leverage proven libraries

---

*Last Updated: Phase 0 Design Review*
*Next Review: Phase 1 Completion*

