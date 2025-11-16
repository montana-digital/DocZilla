import os
import time
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("DOCZILLA_BASE_URL", "http://localhost:8501")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = PROJECT_ROOT / "tests" / "fixtures"
OUTPUT_DIR = PROJECT_ROOT / "output"


def server_up(page) -> bool:
    try:
        page.goto(BASE_URL, timeout=10_000)
        return True
    except Exception:
        return False


@pytest.mark.e2e
def test_data_handler_load_from_input_and_preview():
    # Require fixtures present in input or skip
    inp = PROJECT_ROOT / "input"
    if not inp.exists() or not any(inp.iterdir()):
        pytest.skip("No files in input/. Run fixture generator with --copy-to-input")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        if not server_up(page):
            pytest.skip(f"Server not reachable at {BASE_URL}. Start with: python scripts/run_app.py")

        # Navigate to Data File Handler
        try:
            page.get_by_text("Data File Handler").click()
        except Exception:
            page.goto(f"{BASE_URL}/Data_File_Handler")

        # Click Load from Input Directory
        page.get_by_text("Load from Input Directory").click()
        # Wait for Loaded Files section
        page.wait_for_selector("text=Loaded Files", timeout=15_000)
        # Open first file analysis card by checking for 'Data Preview' text
        page.wait_for_selector("text=Data Preview", timeout=15_000)

        context.close()
        browser.close()


@pytest.mark.e2e
def test_document_handler_upload_and_convert_to_txt():
    docx = FIXTURES / "sample.docx"
    if not docx.exists():
        pytest.skip("fixtures/sample.docx missing. Run fixture generator.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Clean any prior output file
    expected = OUTPUT_DIR / f"{docx.stem}.txt"
    if expected.exists():
        try:
            expected.unlink()
        except Exception:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        if not server_up(page):
            pytest.skip(f"Server not reachable at {BASE_URL}. Start with: python scripts/run_app.py")

        # Navigate to Document Handler
        try:
            page.get_by_text("Document File Handler").click()
        except Exception:
            page.goto(f"{BASE_URL}/Document_File_Handler")

        # Upload DOCX via file input
        file_inputs = page.locator('input[type="file"]').all()
        if not file_inputs:
            pytest.skip("No file input found on page")
        file_inputs[0].set_input_files(str(docx))

        # Wait for success message
        page.wait_for_selector("text=Loaded 1 document(s)", timeout=15_000)

        # Go to Convert tab and select TXT (default)
        page.get_by_text("Convert").first.click()
        page.get_by_text("Convert Selected").click()

        # Allow some time for conversion and file write
        time.sleep(2)

        assert expected.exists(), f"Expected output not found: {expected}"

        context.close()
        browser.close()
