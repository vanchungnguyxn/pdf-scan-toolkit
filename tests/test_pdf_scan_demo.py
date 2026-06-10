from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.detect_pdf_type import detect_pdf_type
from pdf_scan_toolkit.extract_text_pymupdf import extract_text_pymupdf
from pdf_scan_toolkit.extract_pdfplumber import extract_tables_pdfplumber
from pdf_scan_toolkit.parse_emr_to_json import parse_emr_to_record
from pdf_scan_toolkit.run_pdf_scan_demo import run_demo
from pdf_scan_toolkit.validate_json import validate_record


def test_detect_pdf_types():
    text_pdf = ROOT / "data/pdf_samples/patient_001_text.pdf"
    scanned_pdf = ROOT / "data/pdf_samples/patient_003_scanned_image.pdf"
    assert detect_pdf_type(text_pdf).pdf_type == "text_pdf"
    assert detect_pdf_type(scanned_pdf).pdf_type == "scanned_pdf"


def test_extract_text_and_parse_json():
    pdf = ROOT / "data/pdf_samples/patient_001_text.pdf"
    raw = extract_text_pymupdf(pdf)
    assert len(raw["pages"]) >= 1
    assert sum(p["char_count"] for p in raw["pages"]) > 100

    tables = extract_tables_pdfplumber(pdf)
    record = parse_emr_to_record(raw["pages"], tables.get("tables", []), pdf.name)
    assert record.patient.patient_id == "PT-001"
    assert len(record.clinical_summary.allergies) >= 1
    assert len(record.clinical_summary.chronic_diseases) >= 1
    assert len(record.clinical_summary.active_medications) >= 1
    assert len(record.clinical_summary.abnormal_labs) >= 1

    validation = validate_record(record)
    assert validation["citation_coverage"] == 100.0


def test_run_demo_end_to_end(tmp_path):
    summary = run_demo(
        input_dir=ROOT / "data/pdf_samples",
        output_dir=tmp_path / "json_samples",
        raw_dir=tmp_path / "extracted_raw",
        report_dir=tmp_path / "demo_outputs",
    )
    assert summary["pdf_count"] >= 4
    assert summary["json_count"] >= 2
    assert (tmp_path / "demo_outputs/pdf_scan_report.md").exists()
