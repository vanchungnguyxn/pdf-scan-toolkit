from __future__ import annotations

from pathlib import Path
import fitz  # PyMuPDF


def extract_text_pymupdf(pdf_path: str | Path) -> dict:
    """Extract page-level text using PyMuPDF."""
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    pages = []
    for idx, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        pages.append({"page": idx, "text": text.strip(), "char_count": len(text.strip())})
    return {"tool": "pymupdf", "source_pdf": pdf_path.name, "pages": pages}
