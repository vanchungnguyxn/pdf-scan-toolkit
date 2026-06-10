from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.patient_normalizer import normalize_gender, normalize_patient


def test_normalize_english_patient_fields():
    text = (
        "Patient ID: PT-001\n"
        "Patient Name: John Doe\n"
        "DOB: 1968-03-12\n"
        "Gender: Male\n"
        "Age: 57\n"
    )
    result = normalize_patient(text)
    assert result["patient_id"] == "PT-001"
    assert result["name"] == "John Doe"
    assert result["dob"] == "1968-03-12"
    assert result["gender"] == "male"
    assert result["age"] == 57
    assert result["normalization_confidence"] > 0
    assert "patient_id" in result["source_spans"]


def test_normalize_vietnamese_patient_fields():
    text = (
        "Mã bệnh nhân: BN001\n"
        "Họ tên: Nguyễn Văn A\n"
        "Ngày sinh: 12/03/1968\n"
        "Giới tính: Nam\n"
    )
    result = normalize_patient(text)
    assert result["patient_id"] == "BN001"
    assert result["name"] == "Nguyễn Văn A"
    assert result["dob"] == "1968-03-12"
    assert result["gender"] == "male"


def test_normalize_mrn_and_sex():
    text = "MRN: 123456\nName: Jane Doe\nDate of Birth: 03/12/1968\nSex: F\n"
    result = normalize_patient(text)
    assert result["patient_id"] == "123456"
    assert result["gender"] == "female"


def test_missing_fields_do_not_crash():
    result = normalize_patient("No patient info here.")
    assert result["patient_id"] == "UNKNOWN"
    assert result["name"] == "UNKNOWN"
    assert result["dob"] is None
    assert result["gender"] == "unknown"
    assert result["normalization_confidence"] == 0.0


def test_normalize_gender_variants():
    assert normalize_gender("Nam") == "male"
    assert normalize_gender("Nữ") == "female"
    assert normalize_gender("other") == "other"
    assert normalize_gender("") == "unknown"
