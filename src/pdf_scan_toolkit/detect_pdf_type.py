from __future__ import annotations

from pathlib import Path
import fitz  # PyMuPDF

from .schemas import PDFTypeReport


def detect_pdf_type(pdf_path: str | Path, min_text_chars_per_page: int = 30) -> PDFTypeReport:
    """Detect whether a PDF has a usable text layer or is image-only/scanned.

    Heuristic:
    - text_pdf: most pages have enough text
    - scanned_pdf: no pages have enough text
    - mixed_pdf: some pages have text, some look scanned
    """
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    counts: list[int] = []
    for page in doc:
        text = page.get_text("text") or ""
        counts.append(len(text.strip()))

    total = len(counts)
    text_pages = sum(c >= min_text_chars_per_page for c in counts)

    if total == 0:
        pdf_type = "empty_pdf"
    elif text_pages == 0:
        pdf_type = "scanned_pdf"
    elif text_pages == total:
        pdf_type = "text_pdf"
    else:
        pdf_type = "mixed_pdf"

    return PDFTypeReport(
        file_path=str(pdf_path),
        pdf_type=pdf_type,
        total_pages=total,
        has_text_layer=text_pages > 0,
        page_char_counts=counts,
    )
