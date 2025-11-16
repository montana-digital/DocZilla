"""
Document File Handler Page

Handles document operations: upload, viewing, editing (text-only), conversion, search, page manipulation.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.app.components.layout import render_page_header, render_sidebar, render_quick_start
from src.app.utils.config import get_config
from src.app.utils.logging import get_logger, generate_request_id
from src.app.utils.exceptions import OperationalError
from src.app.services.doc_ops import (
    extract_text, InMemorySearchIndex, move_pages, append_documents, remove_pages
)

# Streamlit multipage: Don't call st.set_page_config() here

# Initialize logger and config
config = get_config()
logger = get_logger()

# Initialize session state
if "docs" not in st.session_state:
    st.session_state.docs = {}  # {file_name: {path: Path, text: str}}

if "search_index" not in st.session_state:
    st.session_state.search_index = InMemorySearchIndex()

# Render sidebar
render_sidebar()

# Page header
render_page_header(
    title="📄 Document File Handler",
    subtitle="Convert, edit, search, and manipulate documents"
)

# Quick Start
render_quick_start([
    "Upload documents via drag-and-drop",
    "View and edit text (structure preserved, formatting may be lost)",
    "Search across documents",
    "Convert between formats and manipulate pages"
])

# Tabs
vtab, stab, ctab, ptab = st.tabs([
    "📤 Upload & View", "🔎 Search", "🔄 Convert", "📑 Page Ops"
])

# -----------------------------
# Upload & View
# -----------------------------
with vtab:
    st.markdown("### Upload Documents")
    uploaded = st.file_uploader(
        "Drag and drop documents here",
        type=["pdf", "docx", "txt", "rtf", "odt", "html"],
        accept_multiple_files=True
    )

    if uploaded:
        for uf in uploaded:
            temp_path = Path("temp") / uf.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uf.getbuffer())
            load_doc_to_session(temp_path)
        st.success(f"Loaded {len(uploaded)} document(s)")

    # Show loaded docs
    if st.session_state.docs:
        doc_names = list(st.session_state.docs.keys())
        selected = st.selectbox("Select document", doc_names)

        if selected:
            doc_info = st.session_state.docs[selected]
            st.markdown(f"#### {selected}")

            # Text view/edit
            with st.expander("📝 Text (editable)", expanded=True):
                text = doc_info.get("text", "")
                new_text = st.text_area("Text content", value=text, height=300, key=f"text_{selected}")
                if st.button("💾 Save As Copy", key=f"save_{selected}"):
                    save_text_copy(selected, new_text)
                    st.success("Saved edited copy to Output directory")

# -----------------------------
# Search
# -----------------------------
with stab:
    st.markdown("### Search Documents")
    if not st.session_state.docs:
        st.info("Upload documents in the Upload & View tab first")
    else:
        # Build or refresh index
        if st.button("🔄 Rebuild Index"):
            rebuild_index()
            st.success("Index rebuilt")

        query = st.text_input("Enter search query")
        if st.button("🔎 Search") and query:
            results = st.session_state.search_index.search(query)
            if not results:
                st.info("No matches found")
            else:
                for file_name, snippets in results.items():
                    with st.expander(file_name):
                        for snip in snippets:
                            st.write(f"… {snip} …")
                        # Optional: inline edit and save
                        if st.button("Edit & Save Copy", key=f"edit_{file_name}"):
                            doc_info = st.session_state.docs[file_name]
                            text = doc_info.get("text", "")
                            edited = st.text_area("Edit text", value=text, height=200, key=f"edit_area_{file_name}")
                            if st.button("Save Edited Copy", key=f"save_edited_{file_name}"):
                                save_text_copy(file_name, edited)
                                st.success("Saved edited copy")

# -----------------------------
# Convert (placeholder minimal)
# -----------------------------
with ctab:
    st.markdown("### Convert Documents")
    st.info("Basic conversions: DOCX→TXT, PDF→TXT. PDF→DOCX may lose formatting.")
    if not st.session_state.docs:
        st.info("Upload documents in the Upload & View tab first")
    else:
        file_name = st.selectbox("Select document", list(st.session_state.docs.keys()), key="conv_doc")
        target = st.selectbox("Convert to", ["txt"], key="conv_target")
        if st.button("🔄 Convert", key="conv_btn"):
            doc = st.session_state.docs[file_name]
            path = doc["path"]
            if target == "txt":
                text = doc.get("text") or extract_text(path)
                save_text_copy(file_name, text, ext="txt")
                st.success("Converted to TXT and saved")

# -----------------------------
# Page Operations (PDF)
# -----------------------------
with ptab:
    st.markdown("### PDF Page Operations")
    st.info("Move, append, and remove pages (PDF only)")

    pdf_docs = [n for n, d in st.session_state.docs.items() if d["path"].suffix.lower() == ".pdf"]
    if not pdf_docs:
        st.info("Upload at least one PDF document")
    else:
        subtab1, subtab2, subtab3 = st.tabs(["Move Pages", "Append Documents", "Remove Pages"])

        with subtab1:
            fname = st.selectbox("Select PDF", pdf_docs, key="mv_pdf")
            doc = st.session_state.docs[fname]
            page_count = get_pdf_page_count(doc["path"]) or 0
            st.caption(f"Pages: {page_count}")
            src = st.number_input("From page (0-based)", min_value=0, max_value=max(page_count - 1, 0), value=0)
            dst = st.number_input("Insert before index", min_value=0, max_value=max(page_count, 0), value=0)
            if st.button("▶️ Move", key="mv_btn"):
                out = get_output_dir() / f"{Path(fname).stem}_moved.pdf"
                move_pages(doc["path"], [(int(src), int(dst))], out)
                st.success(f"Saved: {out.name}")

        with subtab2:
            first = st.selectbox("First PDF", pdf_docs, key="ap_first")
            others = st.multiselect("Append these (in order)", [n for n in pdf_docs if n != first], key="ap_others")
            if st.button("▶️ Append", key="ap_btn") and others:
                out = get_output_dir() / f"{Path(first).stem}_appended.pdf"
                append_documents(st.session_state.docs[first]["path"], [st.session_state.docs[o]["path"] for o in others], out)
                st.success(f"Saved: {out.name}")

        with subtab3:
            fname = st.selectbox("Select PDF", pdf_docs, key="rm_pdf")
            doc = st.session_state.docs[fname]
            page_count = get_pdf_page_count(doc["path"]) or 0
            rm_pages_str = st.text_input("Pages to remove (comma-separated indices)", value="")
            if st.button("🗑️ Remove", key="rm_btn") and rm_pages_str:
                pages = [int(p.strip()) for p in rm_pages_str.split(',') if p.strip().isdigit()]
                out = get_output_dir() / f"{Path(fname).stem}_removed.pdf"
                remove_pages(doc["path"], pages, out)
                st.success(f"Saved: {out.name}")


# -----------------------------
# Helper functions
# -----------------------------

def load_doc_to_session(path: Path):
    text = extract_text(path)
    st.session_state.docs[path.name] = {"path": path, "text": text}
    # Index immediately
    st.session_state.search_index.add(path.name, text)


def rebuild_index():
    st.session_state.search_index.clear()
    for name, doc in st.session_state.docs.items():
        st.session_state.search_index.add(name, doc.get("text", ""))


def save_text_copy(file_name: str, text: str, ext: str = "txt"):
    out = get_output_dir()
    out.mkdir(parents=True, exist_ok=True)
    base = Path(file_name).stem
    new_name = f"{base}_{generate_request_id().split('-')[0]}.{ext}"
    (out / new_name).write_text(text or "", encoding="utf-8")


def get_output_dir() -> Path:
    return Path(config.get("directories.output", "./output"))


def get_pdf_page_count(pdf_path: Path) -> int:
    try:
        from PyPDF2 import PdfReader
        r = PdfReader(str(pdf_path))
        return len(r.pages)
    except Exception:
        return 0

