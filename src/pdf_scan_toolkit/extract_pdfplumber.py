from __future__ import annotations

from pathlib import Path
import pdfplumber


def extract_text_pdfplumber(pdf_path: str | Path) -> dict:
    """Extract page-level text using pdfplumber."""
    pdf_path = Path(pdf_path)
    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page": idx, "text": text.strip(), "char_count": len(text.strip())})
    return {"tool": "pdfplumber", "source_pdf": pdf_path.name, "pages": pages}


def extract_tables_pdfplumber(pdf_path: str | Path) -> dict:
    """Extract tables using pdfplumber.

    It returns an empty list if no table is found, instead of raising errors.
    """
    pdf_path = Path(pdf_path)
    tables = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            try:
                page_tables = page.extract_tables() or []
            except Exception as exc:  # defensive: table extraction can be fragile on weird layouts
                tables.append({
                    "page": page_index,
                    "table_index": -1,
                    "error": str(exc),
                    "rows": [],
                })
                continue
            for table_index, rows in enumerate(page_tables):
                cleaned_rows = []
                for row in rows:
                    cleaned_rows.append(["" if cell is None else str(cell).strip() for cell in row])
                tables.append({
                    "page": page_index,
                    "table_index": table_index,
                    "rows": cleaned_rows,
                })
    return {"tool": "pdfplumber", "source_pdf": pdf_path.name, "tables": tables}
