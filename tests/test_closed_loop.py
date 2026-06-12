from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.json_to_pdf import json_file_to_pdf
from pdf_scan_toolkit.run_closed_loop_demo import run_closed_loop
from pdf_scan_toolkit.synthesize_records import synthesize_from_templates


def test_synthesize_and_json_to_pdf(tmp_path):
    synth_dir = tmp_path / "synthetic_json"
    pdf_dir = tmp_path / "synthetic_pdf"
    paths = synthesize_from_templates(ROOT / "data/json_samples", synth_dir, count=1)
    assert len(paths) == 1
    pdf = json_file_to_pdf(paths[0], pdf_dir / "syn-001_emr.pdf")
    assert pdf.exists()
    assert pdf.stat().st_size > 500


def test_closed_loop_demo(tmp_path):
    summary = run_closed_loop(
        template_dir=ROOT / "data/json_samples",
        synthetic_json_dir=tmp_path / "synthetic_json_samples",
        synthetic_pdf_dir=tmp_path / "synthetic_pdf_samples",
        roundtrip_json_dir=tmp_path / "roundtrip_json_samples",
        roundtrip_raw_dir=tmp_path / "roundtrip_extracted_raw",
        report_dir=tmp_path / "roundtrip_outputs",
        count=2,
    )
    assert summary["synthetic_count"] == 2
    assert summary["roundtrip_json_count"] >= 2
    assert (tmp_path / "roundtrip_outputs/closed_loop_summary.json").exists()
