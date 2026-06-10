from __future__ import annotations

from pathlib import Path
from .schemas import ToolComparisonRow


def write_markdown_report(rows: list[ToolComparisonRow], details: list[dict], out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# PDF Scan Demo Report")
    lines.append("")
    lines.append("## Tool Comparison")
    lines.append("")
    lines.append("| File | Type | Pages | PyMuPDF chars | pdfplumber chars | Tables | OCR | JSON | Citation coverage |")
    lines.append("|---|---|---:|---:|---:|---:|---|---|---:|")
    for row in rows:
        lines.append(
            f"| {row.file} | {row.detected_type} | {row.pages} | {row.pymupdf_chars} | "
            f"{row.pdfplumber_chars} | {row.tables_found} | {row.ocr_status} | {row.json_status} | {row.citation_coverage} |"
        )
    lines.append("")
    lines.append("## Parsed JSON Summary")
    lines.append("")
    lines.append("| File | Patient | Allergies | Chronic | Medications | Abnormal Labs | Validation | Notes |")
    lines.append("|---|---|---:|---:|---:|---:|---|---|")
    for d in details:
        lines.append(
            f"| {d.get('file')} | {d.get('patient_id', '-')} | {d.get('allergies', 0)} | "
            f"{d.get('chronic_diseases', 0)} | {d.get('active_medications', 0)} | "
            f"{d.get('abnormal_labs', 0)} | {d.get('status', '-')} | {d.get('notes', '')} |"
        )
    lines.append("")
    lines.append("## How to interpret")
    lines.append("")
    lines.append("- `text_pdf`: PDF có text layer, PyMuPDF/pdfplumber đọc được trực tiếp.")
    lines.append("- `scanned_pdf`: PDF là ảnh, cần OCR để lấy text.")
    lines.append("- `mixed_pdf`: PDF có cả page text và page ảnh.")
    lines.append("- `OCR_SKIPPED`: máy chưa cài OCR package hoặc binary Tesseract; demo vẫn chạy bình thường.")
    lines.append("- `Citation coverage`: tỷ lệ clinical item có document/page/evidence_text.")
    lines.append("")
    lines.append("## Next steps")
    lines.append("")
    lines.append("1. Thêm OCR mạnh hơn như PaddleOCR cho tiếng Việt và bảng scan.")
    lines.append("2. Thêm bounding box citation để highlight đúng dòng trong PDF viewer.")
    lines.append("3. Đưa JSON output vào Qdrant/PostgreSQL để xây dựng RAG pipeline.")
    lines.append("4. Tạo golden answer để đánh giá extraction và RAG.")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
