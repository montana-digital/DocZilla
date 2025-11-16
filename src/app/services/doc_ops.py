"""
Document Operations Service

Handles document extraction, search indexing, and page operations (move, append, remove).
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple

# PDF and DOCX libraries
import io

try:
    from PyPDF2 import PdfReader, PdfWriter
except Exception:
    PdfReader = None
    PdfWriter = None

try:
    import docx  # python-docx
except Exception:
    docx = None

# Fallback for PDF text extraction
try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except Exception:
    pdfminer_extract_text = None


# -----------------------------
# Text Extraction
# -----------------------------

def extract_text(file_path: Path) -> str:
    """
    Extract text from a document (PDF, DOCX, TXT, RTF basic, ODT basic, HTML basic).

    Args:
        file_path: Path to document

    Returns:
        Extracted text (best effort)
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _extract_text_from_pdf(file_path)
    if suffix == ".docx" and docx is not None:
        return _extract_text_from_docx(file_path)
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    # Basic fallbacks for other formats
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF using PyPDF2 with pdfminer fallback."""
    # Try PyPDF2 first
    if PdfReader is not None:
        try:
            reader = PdfReader(str(file_path))
            texts = []
            for page in reader.pages:
                try:
                    texts.append(page.extract_text() or "")
                except Exception:
                    texts.append("")
            return "\n".join(texts)
        except Exception:
            pass

    # Fallback to pdfminer
    if pdfminer_extract_text is not None:
        try:
            return pdfminer_extract_text(str(file_path)) or ""
        except Exception:
            pass

    return ""


def _extract_text_from_docx(file_path: Path) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        document = docx.Document(str(file_path))
        return "\n".join([para.text for para in document.paragraphs])
    except Exception:
        return ""


# -----------------------------
# Search Index (simple)
# -----------------------------

class InMemorySearchIndex:
    """Simple in-memory index mapping filenames to text."""

    def __init__(self):
        self._index: Dict[str, str] = {}

    def add(self, file_name: str, text: str):
        self._index[file_name] = text or ""

    def clear(self):
        self._index.clear()

    def search(self, query: str) -> Dict[str, List[str]]:
        """
        Search for query in indexed documents.

        Returns mapping filename -> list of matched snippets.
        """
        results: Dict[str, List[str]] = {}
        q = (query or "").strip()
        if not q:
            return results

        for file_name, text in self._index.items():
            if not text:
                continue
            if q.lower() in text.lower():
                # Return up to 3 snippets around the first few matches
                snippets: List[str] = []
                lower_text = text.lower()
                start = 0
                while True:
                    idx = lower_text.find(q.lower(), start)
                    if idx == -1 or len(snippets) >= 3:
                        break
                    snippet_start = max(0, idx - 80)
                    snippet_end = min(len(text), idx + len(q) + 80)
                    snippets.append(text[snippet_start:snippet_end].replace("\n", " "))
                    start = idx + len(q)
                results[file_name] = snippets
        return results


# -----------------------------
# Page Operations (PDF)
# -----------------------------

def move_pages(pdf_path: Path, moves: List[Tuple[int, int]], output_path: Path) -> Path:
    """
    Move pages in a PDF.

    Args:
        pdf_path: Source PDF
        moves: List of (from_page_index, insert_before_index) zero-based
        output_path: Output PDF path

    Returns:
        Path to new PDF
    """
    if PdfWriter is None or PdfReader is None:
        raise RuntimeError("PyPDF2 is required for PDF page operations")

    reader = PdfReader(str(pdf_path))
    pages = list(range(len(reader.pages)))

    # Apply moves on index list
    for src_idx, dst_idx in moves:
        if src_idx < 0 or src_idx >= len(pages) or dst_idx < 0 or dst_idx > len(pages):
            continue
        pg = pages.pop(src_idx)
        if dst_idx > src_idx:
            dst_idx -= 1  # account for removal shift
        pages.insert(dst_idx, pg)

    writer = PdfWriter()
    for p in pages:
        writer.add_page(reader.pages[p])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def append_documents(first_pdf: Path, other_pdfs: List[Path], output_path: Path) -> Path:
    """Append multiple PDFs in order."""
    if PdfWriter is None or PdfReader is None:
        raise RuntimeError("PyPDF2 is required for PDF page operations")

    writer = PdfWriter()

    # Add pages from first PDF
    r1 = PdfReader(str(first_pdf))
    for page in r1.pages:
        writer.add_page(page)

    # Append others
    for p in other_pdfs:
        r = PdfReader(str(p))
        for page in r.pages:
            writer.add_page(page)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def remove_pages(pdf_path: Path, pages_to_remove: List[int], output_path: Path) -> Path:
    """Remove selected pages from PDF (zero-based indices)."""
    if PdfWriter is None or PdfReader is None:
        raise RuntimeError("PyPDF2 is required for PDF page operations")

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    to_remove = set(pages_to_remove)
    for i, page in enumerate(reader.pages):
        if i in to_remove:
            continue
        writer.add_page(page)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
