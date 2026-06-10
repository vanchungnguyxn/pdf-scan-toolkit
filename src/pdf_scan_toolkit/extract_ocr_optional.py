from __future__ import annotations

from pathlib import Path
import shutil
import fitz  # PyMuPDF
from PIL import Image


def extract_ocr_optional(pdf_path: str | Path, lang: str = "eng", dpi: int = 180) -> dict:
    """Optional OCR using pytesseract.

    This function never crashes the demo if OCR dependencies are missing.
    It returns status=OCR_SKIPPED with a reason instead.
    """
    pdf_path = Path(pdf_path)
    try:
        import pytesseract  # type: ignore
    except Exception:
        return {
            "tool": "pytesseract",
            "source_pdf": pdf_path.name,
            "status": "OCR_SKIPPED",
            "reason": "Python package pytesseract is not installed. Run: pip install -r requirements-ocr.txt",
            "pages": [],
        }

    if shutil.which("tesseract") is None:
        return {
            "tool": "pytesseract",
            "source_pdf": pdf_path.name,
            "status": "OCR_SKIPPED",
            "reason": "Tesseract binary is not installed or not in PATH.",
            "pages": [],
        }

    doc = fitz.open(pdf_path)
    pages = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    for idx, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        try:
            text = pytesseract.image_to_string(image, lang=lang, timeout=5) or ""
            status = "OCR_OK" if text.strip() else "OCR_EMPTY"
            pages.append({"page": idx, "text": text.strip(), "char_count": len(text.strip())})
        except Exception as exc:
            return {
                "tool": "pytesseract",
                "source_pdf": pdf_path.name,
                "status": "OCR_ERROR",
                "reason": str(exc),
                "pages": pages,
            }

    all_text = "\n".join(p["text"] for p in pages).strip()
    return {
        "tool": "pytesseract",
        "source_pdf": pdf_path.name,
        "status": "OCR_OK" if all_text else "OCR_EMPTY",
        "reason": None,
        "pages": pages,
    }
