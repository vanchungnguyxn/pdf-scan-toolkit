from __future__ import annotations

from pathlib import Path
import argparse
import json
from typing import Any

from .detect_pdf_type import detect_pdf_type
from .extract_text_pymupdf import extract_text_pymupdf
from .extract_pdfplumber import extract_text_pdfplumber, extract_tables_pdfplumber
from .extract_ocr_optional import extract_ocr_optional
from .extract_ocr_enhanced import extract_ocr_enhanced
from .extract_camelot import extract_tables_camelot
from .extract_layout_pymupdf import extract_layout_blocks_pymupdf
from .llm_structured_extractor import extract_emr_record
from .validate_json import validate_record


def run_advanced_compare(
    input_dir: str | Path,
    output_dir: str | Path,
    raw_dir: str | Path,
    report_dir: str | Path,
    use_llm: bool = False,
) -> dict[str, Any]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    raw_dir = Path(raw_dir)
    report_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {input_dir}")

    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []

    for pdf in pdf_files:
        stem = pdf.stem
        detect = detect_pdf_type(pdf)
        pymupdf_raw = extract_text_pymupdf(pdf)
        pdfplumber_raw = extract_text_pdfplumber(pdf)
        pdfplumber_tables = extract_tables_pdfplumber(pdf)
        text_probe = "\n".join(p.get("text", "") for p in pymupdf_raw.get("pages", []))
        should_try_tables = detect.pdf_type == "text_pdf" and any(
            key in text_probe.lower() for key in ["table", "laboratory results", "test", "medication", "xet nghiem", "ket qua"]
        )
        if should_try_tables:
            camelot_lattice = extract_tables_camelot(pdf, flavor="lattice")
            camelot_stream = extract_tables_camelot(pdf, flavor="stream")
        else:
            camelot_lattice = {"tool": "camelot_lattice", "source_pdf": pdf.name, "status": "CAMELOT_SKIPPED", "reason": "Selective skip: no table-like text detected or scanned PDF", "tables": []}
            camelot_stream = {"tool": "camelot_stream", "source_pdf": pdf.name, "status": "CAMELOT_SKIPPED", "reason": "Selective skip: no table-like text detected or scanned PDF", "tables": []}

        needs_ocr = detect.pdf_type in {"scanned_pdf", "mixed_pdf"} or any(int(p.get("char_count", 0)) < 50 for p in pymupdf_raw.get("pages", []))
        if needs_ocr:
            basic_ocr = extract_ocr_optional(pdf, lang="eng", dpi=90)
            enhanced_ocr = extract_ocr_enhanced(pdf, lang="eng", dpi=90, preprocess=True)
        else:
            basic_ocr = {"tool": "pytesseract", "source_pdf": pdf.name, "status": "OCR_SKIPPED", "reason": "Selective skip: text layer is sufficient", "pages": []}
            enhanced_ocr = {"tool": "tesseract_enhanced", "source_pdf": pdf.name, "status": "OCR_SKIPPED", "reason": "Selective skip: text layer is sufficient", "pages": []}
        layout_blocks = extract_layout_blocks_pymupdf(pdf)

        raw_outputs = {
            "detect": detect.model_dump(),
            "pymupdf": pymupdf_raw,
            "pdfplumber_text": pdfplumber_raw,
            "pdfplumber_tables": pdfplumber_tables,
            "camelot_lattice": camelot_lattice,
            "camelot_stream": camelot_stream,
            "basic_ocr": basic_ocr,
            "enhanced_ocr": enhanced_ocr,
            "layout_blocks": layout_blocks,
        }
        for name, data in raw_outputs.items():
            suffix = "detect" if name == "detect" else name
            (raw_dir / f"{stem}.{suffix}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        selected_pages = _select_best_pages(
            pymupdf_pages=pymupdf_raw.get("pages", []),
            pdfplumber_pages=pdfplumber_raw.get("pages", []),
            basic_ocr_pages=basic_ocr.get("pages", []),
            enhanced_ocr_pages=enhanced_ocr.get("pages", []),
        )
        merged_tables = _merge_tables(pdfplumber_tables, camelot_lattice, camelot_stream)

        json_status = "SKIPPED"
        citation_coverage = "0%"
        validation: dict[str, Any] = {}
        notes = []

        extraction_mode = "rule_based"
        extraction_reason = "LLM disabled"

        if sum(int(p.get("char_count", 0)) for p in selected_pages) >= 30:
            record, extraction_mode, extraction_reason = extract_emr_record(
                selected_pages, merged_tables, source_pdf=pdf.name, use_llm=use_llm,
            )
            record.metadata.update({
                "tools": ["PyMuPDF", "pdfplumber", "Camelot", "Tesseract OCR enhanced", "PyMuPDF layout blocks"],
                "selected_pages": [
                    {"page": p.get("page"), "source_tool": p.get("source_tool"), "char_count": p.get("char_count", 0)}
                    for p in selected_pages
                ],
                "tables_merged": len(merged_tables),
                "extraction_mode": extraction_mode,
                "extraction_reason": extraction_reason,
            })
            out_json = output_dir / f"{stem}.json"
            out_json.write_text(record.model_dump_json(indent=2), encoding="utf-8")
            validation = validate_record(record)
            json_status = "PARSED"
            citation_coverage = f"{validation.get('citation_coverage', 0)}%"
            if validation.get("warnings"):
                notes.extend(validation["warnings"][:2])
        else:
            notes.append("No usable text even after enhanced OCR")

        row = {
            "file": pdf.name,
            "type": detect.pdf_type,
            "pages": detect.total_pages,
            "pymupdf_chars": _char_count(pymupdf_raw.get("pages", [])),
            "pdfplumber_chars": _char_count(pdfplumber_raw.get("pages", [])),
            "basic_ocr_status": basic_ocr.get("status"),
            "basic_ocr_chars": _char_count(basic_ocr.get("pages", [])),
            "enhanced_ocr_status": enhanced_ocr.get("status"),
            "enhanced_ocr_chars": _char_count(enhanced_ocr.get("pages", [])),
            "pdfplumber_tables": len(pdfplumber_tables.get("tables", [])),
            "camelot_lattice_tables": len(camelot_lattice.get("tables", [])),
            "camelot_stream_tables": len(camelot_stream.get("tables", [])),
            "layout_blocks": sum(len(p.get("blocks", [])) for p in layout_blocks.get("pages", [])),
            "selected_chars": _char_count(selected_pages),
            "selected_sources": ", ".join(sorted({str(p.get("source_tool")) for p in selected_pages if p.get("source_tool")})),
            "json_status": json_status,
            "citation_coverage": citation_coverage,
            "notes": "; ".join(notes),
        }
        rows.append(row)
        details.append({
            "file": pdf.name,
            **validation,
            "extraction_mode": extraction_mode,
            "extraction_reason": extraction_reason,
            "notes": "; ".join(notes),
        })

    report_path = report_dir / "advanced_tool_comparison_report.md"
    _write_advanced_report(rows, details, report_path)
    summary = {
        "pdf_count": len(pdf_files),
        "json_count": len(list(output_dir.glob("*.json"))),
        "report_path": str(report_path),
        "rows": rows,
    }
    (report_dir / "advanced_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def _char_count(pages: list[dict[str, Any]]) -> int:
    return sum(int(p.get("char_count", 0)) for p in pages)


def _by_page(pages: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    out = {}
    for p in pages:
        try:
            out[int(p.get("page", 1))] = p
        except Exception:
            pass
    return out


def _select_best_pages(
    pymupdf_pages: list[dict[str, Any]],
    pdfplumber_pages: list[dict[str, Any]],
    basic_ocr_pages: list[dict[str, Any]],
    enhanced_ocr_pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sources = [
        ("pymupdf", _by_page(pymupdf_pages)),
        ("pdfplumber", _by_page(pdfplumber_pages)),
        ("tesseract_basic", _by_page(basic_ocr_pages)),
        ("tesseract_enhanced", _by_page(enhanced_ocr_pages)),
    ]
    all_pages = sorted({page for _, mapping in sources for page in mapping})
    selected: list[dict[str, Any]] = []
    for page_no in all_pages:
        candidates = []
        for name, mapping in sources:
            page = mapping.get(page_no)
            if not page:
                continue
            text = page.get("text", "") or ""
            char_count = len(text.strip())
            # Prefer text layer when comparable; prefer OCR when text layer is empty/weak.
            score = char_count
            if name.startswith("tesseract") and char_count < 30:
                score -= 1000
            candidates.append((score, name, text, page))
        if not candidates:
            continue
        _, name, text, page = max(candidates, key=lambda x: x[0])
        selected.append({
            "page": page_no,
            "text": text.strip(),
            "char_count": len(text.strip()),
            "source_tool": name,
        })
    return selected


def _merge_tables(*table_payloads: dict[str, Any]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen = set()
    for payload in table_payloads:
        tool = payload.get("tool", "unknown_table_tool")
        for table in payload.get("tables", []) or []:
            rows = table.get("rows", []) or []
            if not rows:
                continue
            signature = (int(table.get("page", 1)), tuple(tuple(str(c) for c in row) for row in rows[:3]))
            if signature in seen:
                continue
            seen.add(signature)
            merged.append({**table, "source_tool": tool})
    return merged


def _write_advanced_report(rows: list[dict[str, Any]], details: list[dict[str, Any]], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Advanced PDF Tool Comparison Report")
    lines.append("")
    lines.append("This report compares basic text extraction with advanced OCR, table, and layout tools.")
    lines.append("")
    lines.append("## Tool-Level Comparison")
    lines.append("")
    lines.append("| File | Type | Pages | PyMuPDF | pdfplumber | OCR basic | OCR enhanced | pdfplumber tables | Camelot lattice | Camelot stream | Layout blocks | Selected source | JSON | Citation |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|")
    for r in rows:
        lines.append(
            f"| {r['file']} | {r['type']} | {r['pages']} | {r['pymupdf_chars']} | {r['pdfplumber_chars']} | "
            f"{r['basic_ocr_chars']} | {r['enhanced_ocr_chars']} | {r['pdfplumber_tables']} | "
            f"{r['camelot_lattice_tables']} | {r['camelot_stream_tables']} | {r['layout_blocks']} | "
            f"{r['selected_sources']} | {r['json_status']} | {r['citation_coverage']} |"
        )
    lines.append("")
    lines.append("## Parsed Clinical Summary")
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
    lines.append("## Normalization and Citation Quality")
    lines.append("")
    lines.append(
        "| File | Patient ID | Name | DOB | Gender | Patient Confidence | "
        "Span Citation Rate | Page Citation Rate | Not Found |"
    )
    lines.append("|---|---|---|---|---|---:|---:|---:|---:|")
    for d in details:
        conf = d.get("patient_confidence")
        conf_str = f"{conf:.2f}" if conf is not None else "-"
        lines.append(
            f"| {d.get('file')} | {d.get('patient_id', '-')} | {d.get('patient_name', '-')} | "
            f"{d.get('patient_dob') or '-'} | {d.get('patient_gender') or '-'} | {conf_str} | "
            f"{d.get('span_level_citation_rate', 0):.1f}% | {d.get('page_level_citation_rate', 0):.1f}% | "
            f"{d.get('citation_not_found_count', 0)} |"
        )
    lines.append("")
    lines.append("## Extraction Mode")
    lines.append("")
    lines.append("| File | Mode | Reason |")
    lines.append("|---|---|---|")
    for d in details:
        lines.append(
            f"| {d.get('file')} | {d.get('extraction_mode', 'rule_based')} | "
            f"{d.get('extraction_reason', '-')} |"
        )
    lines.append("")
    lines.append(
        "Compared with the previous advanced version, this version improves patient normalization "
        "and distinguishes span-level citations from page-level citations. LLM structured extraction "
        "is optional and safely falls back to rule-based extraction when API keys are not configured."
    )
    lines.append("")
    lines.append("## What improved compared with the basic demo")
    lines.append("")
    lines.append("- `Tesseract enhanced` renders pages at higher DPI and applies preprocessing before OCR.")
    lines.append("- `Camelot lattice/stream` gives an alternative table extractor when pdfplumber misses grid tables.")
    lines.append("- `PyMuPDF layout blocks` records bounding boxes for future PDF source highlighting.")
    lines.append("- The advanced selector chooses the best text source per page, so mixed text/scan PDFs can still produce JSON.")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- OCR may still fail on rotated, blurred, handwritten, or very noisy scans.")
    lines.append("- Rule-based clinical extraction is deterministic but limited; optional LLM extraction (`--use-llm`) improves flexible documents when API keys are configured.")
    lines.append("- This demo is not a medical device and does not provide clinical advice.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run advanced PDF extraction comparison.")
    parser.add_argument("--input", default="data/advanced_pdf_samples")
    parser.add_argument("--output", default="data/advanced_json_samples")
    parser.add_argument("--raw", default="data/advanced_extracted_raw")
    parser.add_argument("--report", default="data/advanced_demo_outputs")
    parser.add_argument("--use-llm", action="store_true", help="Enable optional LLM structured extraction (falls back if no API key)")
    args = parser.parse_args()
    summary = run_advanced_compare(args.input, args.output, args.raw, args.report, use_llm=args.use_llm)
    print("Advanced PDF comparison completed.")
    print(f"PDF files: {summary['pdf_count']}")
    print(f"JSON outputs: {summary['json_count']}")
    print(f"Report: {summary['report_path']}")


if __name__ == "__main__":
    main()
