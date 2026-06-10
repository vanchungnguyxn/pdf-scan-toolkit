from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_tables_camelot(pdf_path: str | Path, flavor: str = "lattice") -> dict[str, Any]:
    """Extract tables with Camelot.

    Camelot is stronger for ruled/grid tables than pdfplumber in some PDFs.
    This function is defensive: it never crashes the demo if Ghostscript/Camelot
    dependencies are missing or if the PDF has no tables.
    """
    pdf_path = Path(pdf_path)
    try:
        import camelot  # type: ignore
    except Exception as exc:
        return {
            "tool": f"camelot_{flavor}",
            "source_pdf": pdf_path.name,
            "status": "CAMELOT_SKIPPED",
            "reason": f"camelot import failed: {exc}",
            "tables": [],
        }

    tables_out: list[dict[str, Any]] = []
    try:
        tables = camelot.read_pdf(str(pdf_path), pages="all", flavor=flavor)
    except Exception as exc:
        return {
            "tool": f"camelot_{flavor}",
            "source_pdf": pdf_path.name,
            "status": "CAMELOT_ERROR",
            "reason": str(exc),
            "tables": [],
        }

    for idx, table in enumerate(tables):
        try:
            rows = table.df.fillna("").astype(str).values.tolist()
            page = int(getattr(table, "page", 1) or 1)
            parsing_report = getattr(table, "parsing_report", {}) or {}
            tables_out.append({
                "page": page,
                "table_index": idx,
                "flavor": flavor,
                "accuracy": parsing_report.get("accuracy"),
                "whitespace": parsing_report.get("whitespace"),
                "rows": rows,
            })
        except Exception as exc:  # defensive for strange table objects
            tables_out.append({
                "page": 1,
                "table_index": idx,
                "flavor": flavor,
                "error": str(exc),
                "rows": [],
            })

    return {
        "tool": f"camelot_{flavor}",
        "source_pdf": pdf_path.name,
        "status": "CAMELOT_OK",
        "reason": None,
        "tables": tables_out,
    }
