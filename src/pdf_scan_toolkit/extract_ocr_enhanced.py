from __future__ import annotations

from pathlib import Path
from typing import Any
import shutil
import fitz  # PyMuPDF
from PIL import Image


def _preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Lightweight OCR preprocessing: grayscale + contrast + threshold.

    Keeps dependencies small while improving scan/noisy image extraction.
    """
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    arr = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    # Reduce light noise without destroying printed text.
    gray = cv2.medianBlur(gray, 3)
    # Adaptive threshold helps with uneven backgrounds in scanned documents.
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )
    return Image.fromarray(thresh)


def extract_ocr_enhanced(pdf_path: str | Path, lang: str = "vie+eng", dpi: int = 300, preprocess: bool = True) -> dict[str, Any]:
    """Enhanced optional OCR using Tesseract + image preprocessing.

    Requires pytesseract and the tesseract binary. It returns a skipped/error
    status instead of crashing when dependencies are missing.
    """
    pdf_path = Path(pdf_path)
    try:
        import pytesseract  # type: ignore
    except Exception as exc:
        return {
            "tool": "tesseract_enhanced",
            "source_pdf": pdf_path.name,
            "status": "OCR_SKIPPED",
            "reason": f"pytesseract is not installed: {exc}",
            "pages": [],
        }
    if shutil.which("tesseract") is None:
        return {
            "tool": "tesseract_enhanced",
            "source_pdf": pdf_path.name,
            "status": "OCR_SKIPPED",
            "reason": "tesseract binary is not installed or not in PATH",
            "pages": [],
        }

    doc = fitz.open(pdf_path)
    pages: list[dict[str, Any]] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    config = "--oem 3 --psm 6"
    for idx, page in enumerate(doc, start=1):
        try:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            if preprocess:
                image = _preprocess_for_ocr(image)
            text = pytesseract.image_to_string(image, lang=lang, config=config, timeout=5) or ""
            pages.append({
                "page": idx,
                "text": text.strip(),
                "char_count": len(text.strip()),
                "dpi": dpi,
                "lang": lang,
                "preprocess": preprocess,
            })
        except Exception as exc:
            pages.append({
                "page": idx,
                "text": "",
                "char_count": 0,
                "error": str(exc),
                "dpi": dpi,
                "lang": lang,
                "preprocess": preprocess,
            })
    all_text = "\n".join(p.get("text", "") for p in pages).strip()
    return {
        "tool": "tesseract_enhanced",
        "source_pdf": pdf_path.name,
        "status": "OCR_OK" if all_text else "OCR_EMPTY",
        "reason": None if all_text else "No text recognized",
        "pages": pages,
    }
