from __future__ import annotations

from pathlib import Path
from typing import Any
import fitz  # PyMuPDF


def extract_layout_blocks_pymupdf(pdf_path: str | Path) -> dict[str, Any]:
    """Extract text blocks with bounding boxes using PyMuPDF.

    This is useful for layout-aware debugging and future source highlighting.
    The current MVP still uses page-level citation, but this output can be used
    later to highlight exact source blocks in a PDF viewer.
    """
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    pages: list[dict[str, Any]] = []
    for page_index, page in enumerate(doc, start=1):
        blocks: list[dict[str, Any]] = []
        try:
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                text_parts: list[str] = []
                for line in block.get("lines", []):
                    line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                    if line_text.strip():
                        text_parts.append(line_text.strip())
                text = "\n".join(text_parts).strip()
                if text:
                    blocks.append({
                        "bbox": [round(float(x), 2) for x in block.get("bbox", [])],
                        "text": text,
                        "char_count": len(text),
                    })
        except Exception as exc:
            pages.append({"page": page_index, "blocks": [], "error": str(exc)})
            continue
        pages.append({
            "page": page_index,
            "blocks": blocks,
            "block_count": len(blocks),
            "char_count": sum(b["char_count"] for b in blocks),
        })
    return {"tool": "pymupdf_layout_blocks", "source_pdf": pdf_path.name, "pages": pages}
