from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.span_citation import find_evidence_span, is_span_level


PAGES = [
    {
        "page": 1,
        "text": "Header\nPatient has type 2 diabetes and hypertension.\nFooter",
    }
]


def test_exact_match_returns_char_offsets():
    evidence = "type 2 diabetes and hypertension"
    result = find_evidence_span(evidence, PAGES)
    assert result["match_type"] == "exact"
    assert result["confidence"] == 1.0
    raw = PAGES[0]["text"]
    assert raw[result["char_start"]:result["char_end"]] == evidence


def test_case_insensitive_match():
    evidence = "PATIENT HAS TYPE 2 DIABETES"
    result = find_evidence_span(evidence, PAGES)
    assert result["match_type"] == "case_insensitive"
    assert result["char_start"] is not None
    assert is_span_level(result["match_type"])


def test_fuzzy_match_does_not_crash():
    evidence = "patient has type 2 diabetis and hypertensn"
    result = find_evidence_span(evidence, PAGES)
    assert result["match_type"] in {"fuzzy", "case_insensitive", "exact", "not_found"}
    assert "confidence" in result


def test_table_page_level_fallback():
    evidence = "Glucose | 11.2 | mmol/L"
    result = find_evidence_span(evidence, PAGES, from_table=True)
    assert result["match_type"] == "table_page_level"
    assert result["page"] == 1


def test_not_found():
    result = find_evidence_span("completely absent text xyz", PAGES)
    assert result["match_type"] == "not_found"
    assert result["confidence"] == 0.0
    assert result["char_start"] is None
