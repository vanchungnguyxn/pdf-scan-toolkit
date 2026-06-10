from __future__ import annotations

from pathlib import Path
import re
from .patient_normalizer import normalize_patient
from .schemas import ClinicalItem, ClinicalSummary, Document, EMRRecord, LabItem, Patient, SourceCitation


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _line_iter(pages: list[dict]):
    for page in pages:
        page_no = int(page.get("page", 1))
        for line in (page.get("text") or "").splitlines():
            line = _norm(line)
            if line:
                yield page_no, line


def _make_source(page: int, evidence: str) -> SourceCitation:
    return SourceCitation(
        document_id=f"DOC-{page:03d}",
        page=page,
        evidence_text=_norm(evidence),
    )


def parse_emr_to_record(pages: list[dict], tables: list[dict], source_pdf: str) -> EMRRecord:
    """Rule-based parser from extracted PDF text/tables to EMR JSON.

    This is intentionally simple for demo purposes. It is deterministic and easy to evaluate.
    """
    combined = "\n".join(p.get("text", "") for p in pages)
    patient_norm = normalize_patient(combined, pages=pages)
    patient_id = patient_norm["patient_id"]
    name = patient_norm["name"]
    dob = patient_norm.get("dob")
    gender = patient_norm.get("gender")

    documents = [
        Document(
            document_id=f"DOC-{int(p.get('page', 1)):03d}",
            doc_type="emr_pdf_page",
            source_pdf=source_pdf,
            page=int(p.get("page", 1)),
            raw_text=p.get("text", ""),
        )
        for p in pages
    ]

    allergies: list[ClinicalItem] = []
    chronic_diseases: list[ClinicalItem] = []
    active_medications: list[ClinicalItem] = []
    abnormal_labs: list[LabItem] = []

    # Allergies: line-level evidence.
    allergy_patterns = [r"di ung", r"dị ứng", r"allerg"]
    for page_no, line in _line_iter(pages):
        low = line.lower()
        # Skip headings such as "Di ung:" without real content.
        if re.match(r"^(di ung|dị ứng|allerg(?:y|ies)?)\s*:?\s*$", low):
            continue
        if any(x in low for x in ["khong ghi nhan", "không ghi nhận", "khong co", "không có", "no known", "none recorded"]):
            continue
        if any(re.search(p, low, flags=re.IGNORECASE) for p in allergy_patterns):
            value = line
            # Try extracting after dash/colon if present.
            m = re.search(r"(?:di ung|dị ứng|allerg(?:y|ies)?)\s*[:\-]?\s*(.+)", line, re.I)
            if m:
                value = _norm(m.group(1))
                # OCR/sample text can contain "Di ung: Di ung Aspirin"; remove duplicate prefix.
                value = re.sub(r"^(di ung|dị ứng|allerg(?:y|ies)?)\s*", "", value, flags=re.I).strip()
            allergies.append(ClinicalItem(
                name="Allergy",
                value=value,
                status="active",
                source=_make_source(page_no, line),
            ))

    # Chronic disease dictionary.
    chronic_terms = [
        "tang huyet ap", "tăng huyết áp", "hypertension",
        "dai thao duong", "đái tháo đường", "diabetes",
        "hen phe quan", "hen phế quản", "asthma",
        "suy than", "suy thận", "chronic kidney disease", "ckd",
    ]
    seen_chronic = set()
    for page_no, line in _line_iter(pages):
        low = line.lower()
        for term in chronic_terms:
            if term in low and term not in seen_chronic:
                seen_chronic.add(term)
                chronic_diseases.append(ClinicalItem(
                    name="Chronic disease",
                    value=term,
                    status="active",
                    source=_make_source(page_no, line),
                ))

    # Active medications: simple line detection.
    med_keywords = ["metformin", "amlodipine", "insulin", "losartan", "atorvastatin", "thuoc dang dung", "thuốc đang dùng", "medication"]
    for page_no, line in _line_iter(pages):
        low = line.lower()
        if any(k in low for k in med_keywords):
            value = line.lstrip("-• ")
            heading_match = re.search(r"(?:thuoc dang dung|thuốc đang dùng|medication)\s*[:\-]\s*(.+)", line, re.I)
            if heading_match:
                value = _norm(heading_match.group(1))
            elif re.match(r"^(thuoc dang dung|thuốc đang dùng|medication)\s*:?\s*$", low):
                continue
            active_medications.append(ClinicalItem(
                name="Active medication",
                value=value,
                status="active",
                source=_make_source(page_no, line),
            ))

    # Labs from text lines.
    lab_names = ["glucose", "creatinine", "egfr", "hba1c", "hbaic", "hemoglobin"]
    lab_line_regex = re.compile(
        r"(?P<name>Glucose|Creatinine|eGFR|HbA1c|HbAIc|Hemoglobin)\s*[:\-]?\s*"
        r"(?P<value>[0-9]+(?:\.[0-9]+)?)\s*"
        r"(?P<unit>[A-Za-zµ/%]+(?:/[A-Za-z]+)?)?"
        r"(?:.*?(?:reference|tham chieu|tham chiếu|range)\s*[:\-]?\s*(?P<range>[0-9.]+\s*[-–]\s*[0-9.]+))?"
        r"(?P<flag>.*?(cao|thap|thấp|high|low|H|L))?",
        re.I,
    )
    seen_labs = set()
    for page_no, line in _line_iter(pages):
        low = line.lower()
        if not any(name in low for name in lab_names):
            continue
        m = lab_line_regex.search(line)
        if not m:
            continue
        test_name = m.group("name")
        value = m.group("value")
        unit = m.group("unit")
        ref_range = m.group("range")
        interpretation = _interpret_lab(value, ref_range, m.group("flag") or line)
        key = (test_name.lower(), value, page_no)
        if key in seen_labs:
            continue
        seen_labs.add(key)
        if interpretation in {"high", "low", "abnormal"}:
            abnormal_labs.append(LabItem(
                test_name=test_name,
                value=value,
                unit=unit,
                reference_range=ref_range,
                interpretation=interpretation,
                source=_make_source(page_no, line),
            ))

    # Labs from pdfplumber tables.
    abnormal_labs.extend(_parse_labs_from_tables(tables))
    abnormal_labs = _dedupe_labs(abnormal_labs)

    return EMRRecord(
        patient=Patient(patient_id=patient_id, name=name, dob=dob, gender=gender),
        documents=documents,
        clinical_summary=ClinicalSummary(
            allergies=_dedupe_items(allergies),
            chronic_diseases=_dedupe_items(chronic_diseases),
            active_medications=_dedupe_items(active_medications),
            abnormal_labs=abnormal_labs,
        ),
        metadata={
            "source_pdf": source_pdf,
            "parser": "rule_regex_v1",
            "patient_normalization": patient_norm,
        },
    )


def _interpret_lab(value: str | None, ref_range: str | None, flag_text: str | None) -> str:
    flag = (flag_text or "").lower()
    if any(x in flag for x in ["cao", "high", " h"]):
        return "high"
    if any(x in flag for x in ["thap", "thấp", "low", " l"]):
        return "low"
    if value and ref_range:
        try:
            v = float(value)
            parts = re.split(r"[-–]", ref_range)
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            if v < low:
                return "low"
            if v > high:
                return "high"
            return "normal"
        except Exception:
            return "unknown"
    return "unknown"


def _parse_labs_from_tables(tables: list[dict]) -> list[LabItem]:
    out: list[LabItem] = []
    lab_name_set = {"glucose", "creatinine", "egfr", "hba1c", "hbaic", "hemoglobin"}
    for table in tables:
        page = int(table.get("page", 1))
        rows = table.get("rows") or []
        for row in rows:
            cells = [_norm(str(c)) for c in row]
            joined = " | ".join(cells)
            if not any(name in joined.lower() for name in lab_name_set):
                continue
            name = cells[0] if cells else "Unknown"
            # Skip header rows.
            if name.lower() in {"test", "xet nghiem", "xét nghiệm"}:
                continue
            value = cells[1] if len(cells) > 1 else ""
            unit = cells[2] if len(cells) > 2 else None
            ref = cells[3] if len(cells) > 3 else None
            flag = cells[4] if len(cells) > 4 else joined
            interpretation = _interpret_lab(value, ref, flag)
            if interpretation in {"high", "low", "abnormal"}:
                out.append(LabItem(
                    test_name=name,
                    value=value,
                    unit=unit,
                    reference_range=ref,
                    interpretation=interpretation,
                    source=_make_source(page, joined),
                ))
    return out


def _dedupe_items(items: list[ClinicalItem]) -> list[ClinicalItem]:
    seen = set()
    out = []
    for item in items:
        key = (item.name.lower(), item.value.lower(), item.source.page)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _dedupe_labs(items: list[LabItem]) -> list[LabItem]:
    seen = set()
    out = []
    for item in items:
        key = (item.test_name.lower(), item.value, item.source.page)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out
