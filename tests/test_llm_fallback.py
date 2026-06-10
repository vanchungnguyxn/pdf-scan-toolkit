from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.llm_structured_extractor import extract_emr_record
from pdf_scan_toolkit.schemas import EMRRecord
from pdf_scan_toolkit.validate_json import validate_record


SAMPLE_PAGES = [
    {
        "page": 1,
        "text": (
            "Patient ID: PT-001\n"
            "Name: John Doe\n"
            "DOB: 1968-03-12\n"
            "Gender: Male\n"
            "Allergy: Penicillin rash\n"
            "Hypertension since 2018\n"
            "Medication: Metformin 500mg\n"
            "Glucose: 11.2 mmol/L reference 3.9-5.6 high\n"
        ),
        "char_count": 200,
    }
]


def test_llm_fallback_without_api_key(capsys):
    env = {k: v for k, v in os.environ.items() if k not in {
        "OPENROUTER_API_KEY", "GEMINI_API_KEY", "LLM_PROVIDER", "LLM_MODEL"
    }}
    with patch.dict(os.environ, env, clear=True):
        record, mode, reason = extract_emr_record(
            SAMPLE_PAGES, [], source_pdf="test.pdf", use_llm=True,
        )
    captured = capsys.readouterr()
    assert "LLM structured extraction skipped" in captured.out
    assert mode == "llm_fallback_rule_based"
    assert "API key" in reason
    EMRRecord.model_validate(record.model_dump())
    validation = validate_record(record)
    assert validation["patient_id"] == "PT-001"


def test_rule_based_mode_no_api_call(capsys):
    with patch("pdf_scan_toolkit.llm_structured_extractor._call_llm") as mock_llm:
        record, mode, reason = extract_emr_record(
            SAMPLE_PAGES, [], source_pdf="test.pdf", use_llm=False,
        )
    mock_llm.assert_not_called()
    assert mode == "rule_based"
    assert reason == "LLM disabled"
    EMRRecord.model_validate(record.model_dump())


def test_use_llm_false_never_calls_network():
    with patch("urllib.request.urlopen") as mock_urlopen:
        extract_emr_record(SAMPLE_PAGES, [], source_pdf="test.pdf", use_llm=False)
    mock_urlopen.assert_not_called()
