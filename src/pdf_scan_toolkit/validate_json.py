from __future__ import annotations

from pathlib import Path
import json
from .schemas import EMRRecord
from .span_citation import is_span_level


def validate_record_json(json_path: str | Path) -> dict:
    json_path = Path(json_path)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    record = EMRRecord.model_validate(data)
    return validate_record(record)


def validate_record(record: EMRRecord) -> dict:
    document_by_id = {d.document_id: d for d in record.documents}
    total_items = 0
    cited_items = 0
    verified_items = 0
    span_level_items = 0
    page_level_items = 0
    not_found_count = 0
    warnings: list[str] = []

    all_items = (
        list(record.clinical_summary.allergies)
        + list(record.clinical_summary.chronic_diseases)
        + list(record.clinical_summary.active_medications)
        + list(record.clinical_summary.abnormal_labs)
    )

    for item in all_items:
        source = item.source
        total_items += 1
        if source.document_id and source.page and source.evidence_text:
            cited_items += 1

        match_type = source.match_type
        if is_span_level(match_type):
            span_level_items += 1
            verified_items += 1
        elif match_type == "table_page_level":
            page_level_items += 1
            if source.document_id in document_by_id:
                verified_items += 1
                warnings.append(
                    f"Table evidence page-level only (no span match): {getattr(item, 'name', getattr(item, 'test_name', 'item'))}"
                )
            else:
                not_found_count += 1
                warnings.append(f"Evidence not found for {getattr(item, 'name', getattr(item, 'test_name', 'item'))}")
        elif match_type == "not_found":
            not_found_count += 1
            warnings.append(f"Evidence not found for {getattr(item, 'name', getattr(item, 'test_name', 'item'))}")
        elif _evidence_exists(source.document_id, source.evidence_text, document_by_id):
            verified_items += 1
            if source.char_start is not None and source.char_end is not None:
                span_level_items += 1
            else:
                page_level_items += 1
                warnings.append(
                    f"Page-level citation only (no span offsets): {getattr(item, 'name', getattr(item, 'test_name', 'item'))}"
                )
        else:
            if hasattr(item, "test_name") and source.document_id in document_by_id:
                page_level_items += 1
                verified_items += 1
                warnings.append(f"Table evidence not verbatim in text, accepted by page-level source: {item.test_name}")
            else:
                not_found_count += 1
                warnings.append(f"Evidence not found for {getattr(item, 'name', getattr(item, 'test_name', 'item'))}")

    citation_coverage = 100.0 if total_items == 0 else cited_items / total_items * 100
    citation_verified = 100.0 if total_items == 0 else verified_items / total_items * 100
    span_level_citation_rate = 100.0 if total_items == 0 else span_level_items / total_items * 100
    page_level_citation_rate = 100.0 if total_items == 0 else page_level_items / total_items * 100

    patient_meta = record.metadata.get("patient_normalization", {})

    return {
        "status": "PASS" if not_found_count == 0 else "WARN",
        "patient_id": record.patient.patient_id,
        "patient_name": record.patient.name,
        "patient_dob": record.patient.dob,
        "patient_gender": record.patient.gender,
        "patient_confidence": patient_meta.get("normalization_confidence"),
        "documents": len(record.documents),
        "allergies": len(record.clinical_summary.allergies),
        "chronic_diseases": len(record.clinical_summary.chronic_diseases),
        "active_medications": len(record.clinical_summary.active_medications),
        "abnormal_labs": len(record.clinical_summary.abnormal_labs),
        "total_items": total_items,
        "citation_coverage": round(citation_coverage, 2),
        "citation_verified": round(citation_verified, 2),
        "span_level_citation_rate": round(span_level_citation_rate, 2),
        "page_level_citation_rate": round(page_level_citation_rate, 2),
        "citation_not_found_count": not_found_count,
        "extraction_mode": record.metadata.get("extraction_mode", "rule_based"),
        "extraction_reason": record.metadata.get("extraction_reason", ""),
        "warnings": warnings,
    }


def _evidence_exists(document_id: str, evidence_text: str, document_by_id: dict) -> bool:
    doc = document_by_id.get(document_id)
    if not doc:
        return False
    evidence = " ".join(evidence_text.lower().split())
    raw = " ".join(doc.raw_text.lower().split())
    return evidence in raw
