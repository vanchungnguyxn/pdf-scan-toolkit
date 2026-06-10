from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from dateutil import parser as date_parser

GenderEnum = Literal["male", "female", "other", "unknown"]

_PATIENT_ID_PATTERNS: list[tuple[str, int]] = [
    (r"(?:Patient\s+ID)\s*[:\-]\s*([A-Za-z0-9\-]+)", 1),
    (r"(?:MRN|Medical\s+Record\s+Number)\s*[:\-]\s*([A-Za-z0-9\-]+)", 1),
    (r"(?:Mã\s+bệnh\s+nhân|Ma\s+benh\s+nhan)\s*[:\-]\s*([A-Za-z0-9\-]+)", 1),
]

_NAME_PATTERNS: list[tuple[str, int]] = [
    (r"(?:Patient\s+Name)\s*[:\-]\s*([^\n]+)", 1),
    (r"(?:Name)\s*[:\-]\s*([^\n]+)", 1),
    (r"(?:Họ\s+tên|Ho\s+ten)\s*[:\-]\s*([^\n]+)", 1),
]

_DOB_PATTERNS: list[tuple[str, int]] = [
    (r"(?:DOB|Date\s+of\s+Birth)\s*[:\-]\s*([0-9]{4}[\-/][0-9]{2}[\-/][0-9]{2}|[0-9]{2}[\-/][0-9]{2}[\-/][0-9]{4})", 1),
    (r"(?:Ngày\s+sinh|Ngay\s+sinh)\s*[:\-]\s*([0-9]{4}[\-/][0-9]{2}[\-/][0-9]{2}|[0-9]{2}[\-/][0-9]{2}[\-/][0-9]{4})", 1),
]

_GENDER_PATTERNS: list[tuple[str, int]] = [
    (r"(?:Gender|Sex)\s*[:\-]\s*([^\n]+)", 1),
    (r"(?:Giới\s+tính|Gioi\s+tinh)\s*[:\-]\s*([^\n]+)", 1),
]

_AGE_PATTERNS: list[tuple[str, int]] = [
    (r"(?:Age|Tuổi|Tuoi)\s*[:\-]\s*(\d{1,3})", 1),
]

_MALE_TERMS = {"male", "m", "nam", "man", "boy"}
_FEMALE_TERMS = {"female", "f", "nữ", "nu", "woman", "girl"}
_OTHER_TERMS = {"other", "non-binary", "nonbinary", "khác", "khac", "transgender"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _normalize_dob(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = _norm(raw)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    try:
        return date_parser.parse(raw, dayfirst=True).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def normalize_gender(raw: str | None) -> GenderEnum:
    if not raw:
        return "unknown"
    token = _norm(raw).lower().strip(".")
    if token in _MALE_TERMS or token.startswith("male"):
        return "male"
    if token in _FEMALE_TERMS or token.startswith("female"):
        return "female"
    if token in _OTHER_TERMS:
        return "other"
    return "unknown"


def _find_field(
    text: str,
    patterns: list[tuple[str, int]],
) -> tuple[str | None, dict[str, Any] | None]:
    for pattern, group in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            value = _norm(m.group(group))
            span = {
                "page": 1,
                "text": _norm(m.group(0)),
                "start": m.start(group),
                "end": m.end(group),
            }
            return value, span
    return None, None


def _find_field_with_pages(
    pages: list[dict] | None,
    patterns: list[tuple[str, int]],
    combined: str,
) -> tuple[str | None, dict[str, Any] | None]:
    if pages:
        for page in pages:
            page_no = int(page.get("page", 1))
            page_text = page.get("text", "") or ""
            for pattern, group in patterns:
                m = re.search(pattern, page_text, flags=re.IGNORECASE | re.MULTILINE)
                if m:
                    value = _norm(m.group(group))
                    span = {
                        "page": page_no,
                        "text": _norm(m.group(0)),
                        "start": m.start(group),
                        "end": m.end(group),
                    }
                    return value, span
    return _find_field(combined, patterns)


def _confidence_score(found: int, total: int = 4) -> float:
    if total == 0:
        return 0.0
    return round(found / total, 2)


def normalize_patient(text: str, pages: list[dict] | None = None) -> dict[str, Any]:
    """Extract and normalize patient demographics from raw PDF/OCR text."""
    combined = text or ""
    if pages and not combined.strip():
        combined = "\n".join(p.get("text", "") for p in pages)

    source_spans: dict[str, dict[str, Any]] = {}
    found_count = 0

    patient_id, pid_span = _find_field_with_pages(pages, _PATIENT_ID_PATTERNS, combined)
    if patient_id:
        found_count += 1
        source_spans["patient_id"] = pid_span  # type: ignore[assignment]

    name, name_span = _find_field_with_pages(pages, _NAME_PATTERNS, combined)
    if name:
        found_count += 1
        source_spans["name"] = name_span  # type: ignore[assignment]

    dob_raw, dob_span = _find_field_with_pages(pages, _DOB_PATTERNS, combined)
    dob = _normalize_dob(dob_raw)
    if dob:
        found_count += 1
        if dob_span:
            source_spans["dob"] = dob_span

    gender_raw, gender_span = _find_field_with_pages(pages, _GENDER_PATTERNS, combined)
    gender = normalize_gender(gender_raw)
    if gender != "unknown":
        found_count += 1
        if gender_span:
            source_spans["gender"] = gender_span

    age_raw, age_span = _find_field_with_pages(pages, _AGE_PATTERNS, combined)
    age: int | None = None
    if age_raw:
        try:
            age = int(age_raw)
            if age_span:
                source_spans["age"] = age_span
        except ValueError:
            age = None

    return {
        "patient_id": patient_id or "UNKNOWN",
        "name": name or "UNKNOWN",
        "dob": dob,
        "gender": gender,
        "age": age,
        "normalization_confidence": _confidence_score(found_count),
        "source_spans": source_spans,
    }
