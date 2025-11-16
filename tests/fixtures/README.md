# DocZilla Test Fixtures

This folder contains generated sample files for UI testing:

- people.csv/json/xlsx/parquet/feather/jsonl/txt/xml: Mixed dataset with duplicates, missing values, phone numbers, URLs, and numeric outliers.
- people_large_12000.csv: Large CSV to trigger auto-sampling in the UI.
- sample.docx / sample.txt / sample.pdf: Documents for Document Handler testing.
- image_*.png/jpg/webp/tiff: Images for Image Handler testing.

Regenerate (from project root):

```powershell
python scripts/generate_fixtures.py --output tests/fixtures --include-large --copy-to-input
```
