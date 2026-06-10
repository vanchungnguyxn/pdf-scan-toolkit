from __future__ import annotations

from pathlib import Path
import argparse
import json

from .detect_pdf_type import detect_pdf_type
from .extract_text_pymupdf import extract_text_pymupdf
from .extract_pdfplumber import extract_text_pdfplumber, extract_tables_pdfplumber
from .extract_ocr_optional import extract_ocr_optional
from .parse_emr_to_json import parse_emr_to_record
from .reporting import write_markdown_report
from .schemas import ToolComparisonRow
from .validate_json import validate_record


def run_demo(input_dir: str | Path, output_dir: str | Path, raw_dir: str | Path, report_dir: str | Path) -> dict:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    raw_dir = Path(raw_dir)
    report_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    rows: list[ToolComparisonRow] = []
    details: list[dict] = []

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {input_dir}")

    for pdf in pdf_files:
        detect = detect_pdf_type(pdf)
        pymupdf_raw = extract_text_pymupdf(pdf)
        pdfplumber_raw = extract_text_pdfplumber(pdf)
        tables_raw = extract_tables_pdfplumber(pdf)
        ocr_raw = extract_ocr_optional(pdf)

        stem = pdf.stem
        (raw_dir / f"{stem}.detect.json").write_text(detect.model_dump_json(indent=2), encoding="utf-8")
        (raw_dir / f"{stem}.pymupdf.json").write_text(json.dumps(pymupdf_raw, indent=2, ensure_ascii=False), encoding="utf-8")
        (raw_dir / f"{stem}.pdfplumber_text.json").write_text(json.dumps(pdfplumber_raw, indent=2, ensure_ascii=False), encoding="utf-8")
        (raw_dir / f"{stem}.pdfplumber_tables.json").write_text(json.dumps(tables_raw, indent=2, ensure_ascii=False), encoding="utf-8")
        (raw_dir / f"{stem}.ocr.json").write_text(json.dumps(ocr_raw, indent=2, ensure_ascii=False), encoding="utf-8")

        # Prefer PyMuPDF for pages that have a text layer.
        # For scanned-only or mixed PDFs, replace weak/empty pages with OCR text when OCR is available.
        selected_pages = _merge_text_and_ocr_pages(pymupdf_raw["pages"], ocr_raw.get("pages", []), ocr_raw.get("status"))
        json_status = "SKIPPED"
        citation_coverage = "0%"
        detail = {"file": pdf.name, "notes": ""}

        has_text = sum(p.get("char_count", 0) for p in selected_pages) >= 30

        if has_text:
            record = parse_emr_to_record(
                pages=selected_pages,
                tables=tables_raw.get("tables", []),
                source_pdf=pdf.name,
            )
            out_json = output_dir / f"{stem}.json"
            out_json.write_text(record.model_dump_json(indent=2), encoding="utf-8")
            validation = validate_record(record)
            json_status = "PARSED"
            citation_coverage = f"{validation['citation_coverage']}%"
            detail.update(validation)
            if validation.get("warnings"):
                detail["notes"] = "; ".join(validation["warnings"][:2])
        else:
            detail.update({
                "patient_id": "-",
                "status": "SKIPPED",
                "notes": "No usable text layer. Enable OCR to parse scanned PDF." if detect.pdf_type == "scanned_pdf" else "No usable text.",
            })

        rows.append(ToolComparisonRow(
            file=pdf.name,
            detected_type=detect.pdf_type,
            pages=detect.total_pages,
            pymupdf_chars=sum(p["char_count"] for p in pymupdf_raw["pages"]),
            pdfplumber_chars=sum(p["char_count"] for p in pdfplumber_raw["pages"]),
            tables_found=len(tables_raw.get("tables", [])),
            ocr_status=ocr_raw.get("status", "UNKNOWN"),
            json_status=json_status,
            citation_coverage=citation_coverage,
        ))
        details.append(detail)

    report_path = report_dir / "pdf_scan_report.md"
    write_markdown_report(rows, details, report_path)
    summary = {
        "pdf_count": len(pdf_files),
        "json_count": len(list(output_dir.glob("*.json"))),
        "report_path": str(report_path),
        "rows": [r.model_dump() for r in rows],
    }
    (report_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def _merge_text_and_ocr_pages(text_pages: list[dict], ocr_pages: list[dict], ocr_status: str | None) -> list[dict]:
    if ocr_status != "OCR_OK" or not ocr_pages:
        return text_pages
    ocr_by_page = {int(p.get("page", 1)): p for p in ocr_pages}
    merged = []
    for page in text_pages:
        page_no = int(page.get("page", 1))
        if int(page.get("char_count", 0)) < 30 and page_no in ocr_by_page:
            merged.append(ocr_by_page[page_no])
        else:
            merged.append(page)
    # If OCR returned extra pages, include them too.
    seen = {int(p.get("page", 1)) for p in merged}
    for page_no, page in sorted(ocr_by_page.items()):
        if page_no not in seen:
            merged.append(page)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PDF scan tool comparison demo.")
    parser.add_argument("--input", default="data/pdf_samples", help="Folder containing PDF samples")
    parser.add_argument("--output", default="data/json_samples", help="Folder to save final EMR JSON")
    parser.add_argument("--raw", default="data/extracted_raw", help="Folder to save raw extraction outputs")
    parser.add_argument("--report", default="data/demo_outputs", help="Folder to save markdown/json reports")
    args = parser.parse_args()
    summary = run_demo(args.input, args.output, args.raw, args.report)
    print("PDF scan demo completed.")
    print(f"PDF files: {summary['pdf_count']}")
    print(f"JSON outputs: {summary['json_count']}")
    print(f"Report: {summary['report_path']}")


if __name__ == "__main__":
    main()
