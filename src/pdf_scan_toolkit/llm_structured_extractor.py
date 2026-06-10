from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from .parse_emr_to_json import parse_emr_to_record
from .patient_normalizer import normalize_patient
from .schemas import ClinicalItem, ClinicalSummary, Document, EMRRecord, LabItem, Patient, SourceCitation
from .span_citation import find_evidence_span

ExtractionMode = Literal[
    "rule_based",
    "llm",
    "llm_fallback_rule_based",
    "llm_fallback_invalid_schema",
]


class LLMPatientOut(BaseModel):
    patient_id: str = ""
    name: str = ""
    dob: str = ""
    gender: str = ""


class LLMClinicalItemOut(BaseModel):
    name: str = ""
    value: str = ""
    status: str = "unknown"
    evidence_text: str = ""


class LLMLabItemOut(BaseModel):
    test_name: str = ""
    value: str = ""
    unit: str | None = None
    reference_range: str | None = None
    interpretation: str = "unknown"
    evidence_text: str = ""


class LLMClinicalSummaryOut(BaseModel):
    allergies: list[LLMClinicalItemOut] = Field(default_factory=list)
    chronic_diseases: list[LLMClinicalItemOut] = Field(default_factory=list)
    active_medications: list[LLMClinicalItemOut] = Field(default_factory=list)
    abnormal_labs: list[LLMLabItemOut] = Field(default_factory=list)


class LLMExtractionOut(BaseModel):
    patient: LLMPatientOut = Field(default_factory=LLMPatientOut)
    clinical_summary: LLMClinicalSummaryOut = Field(default_factory=LLMClinicalSummaryOut)


_LLM_PROMPT = """You are a clinical document extraction assistant. Extract structured data ONLY from the provided text.

Rules:
- Extract ONLY information explicitly present in the text. Do not infer or speculate.
- If no evidence exists for a field, use empty string or empty array.
- Every clinical item MUST include evidence_text copied verbatim from the source text.
- Do NOT provide treatment advice.
- Do NOT make new diagnoses.
- Output ONLY valid JSON matching this schema (no markdown, no commentary):
{
  "patient": {"patient_id": "", "name": "", "dob": "", "gender": ""},
  "clinical_summary": {
    "allergies": [{"name": "", "value": "", "status": "", "evidence_text": ""}],
    "chronic_diseases": [],
    "active_medications": [],
    "abnormal_labs": []
  }
}

Document text:
"""


def _load_dotenv() -> None:
    """Load .env from project root; does not override existing environment variables."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return


_load_dotenv()


def _get_api_config() -> tuple[str | None, str, str]:
    provider = (os.environ.get("LLM_PROVIDER") or "").strip().lower()
    default_model = "openai/gpt-4o-mini" if provider == "openrouter" else "google/gemini-2.5-flash"
    model = (os.environ.get("LLM_MODEL") or default_model).strip()
    if provider == "openrouter":
        return os.environ.get("OPENROUTER_API_KEY"), model, "openrouter"
    if provider == "gemini":
        return os.environ.get("GEMINI_API_KEY"), model.replace("google/", ""), "gemini"
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if os.environ.get("OPENROUTER_API_KEY"):
        return key, model, "openrouter"
    if os.environ.get("GEMINI_API_KEY"):
        return key, model.replace("google/", ""), "gemini"
    return None, model, provider or "none"


def _extract_json_from_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _call_openrouter(api_key: str, model: str, prompt: str) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def _call_gemini(api_key: str, model: str, prompt: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_llm(text: str) -> dict[str, Any]:
    api_key, model, provider = _get_api_config()
    if not api_key:
        raise RuntimeError("API key not configured")
    prompt = _LLM_PROMPT + text[:50000]
    if provider == "gemini":
        raw = _call_gemini(api_key, model, prompt)
    else:
        raw = _call_openrouter(api_key, model, prompt)
    return _extract_json_from_response(raw)


def _make_source_from_evidence(
    evidence_text: str,
    pages: list[dict],
    from_table: bool = False,
) -> SourceCitation:
    span = find_evidence_span(evidence_text, pages, from_table=from_table)
    return SourceCitation(
        document_id=span["document_id"],
        page=span["page"],
        evidence_text=span["evidence_text"] or evidence_text or "unknown",
        char_start=span.get("char_start"),
        char_end=span.get("char_end"),
        match_type=span.get("match_type"),
        confidence=span.get("confidence"),
    )


def _llm_output_to_record(
    llm_data: LLMExtractionOut,
    pages: list[dict],
    source_pdf: str,
) -> EMRRecord:
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

    norm = normalize_patient("", pages=pages)
    patient = Patient(
        patient_id=llm_data.patient.patient_id or norm["patient_id"],
        name=llm_data.patient.name or norm["name"],
        dob=llm_data.patient.dob or norm.get("dob"),
        gender=llm_data.patient.gender or norm.get("gender"),
    )

    def to_clinical(items: list[LLMClinicalItemOut]) -> list[ClinicalItem]:
        out: list[ClinicalItem] = []
        for item in items:
            if not item.evidence_text and not item.value:
                continue
            evidence = item.evidence_text or item.value
            out.append(ClinicalItem(
                name=item.name or "Clinical item",
                value=item.value or item.name,
                status=item.status or "unknown",
                source=_make_source_from_evidence(evidence, pages),
            ))
        return out

    def to_labs(items: list[LLMLabItemOut]) -> list[LabItem]:
        out: list[LabItem] = []
        for item in items:
            if not item.evidence_text and not item.test_name:
                continue
            evidence = item.evidence_text or f"{item.test_name}: {item.value}"
            interp = item.interpretation if item.interpretation in {
                "high", "low", "normal", "abnormal", "unknown"
            } else "unknown"
            out.append(LabItem(
                test_name=item.test_name or "Unknown",
                value=item.value or "",
                unit=item.unit,
                reference_range=item.reference_range,
                interpretation=interp,  # type: ignore[arg-type]
                source=_make_source_from_evidence(evidence, pages, from_table=True),
            ))
        return out

    cs = llm_data.clinical_summary
    return EMRRecord(
        patient=patient,
        documents=documents,
        clinical_summary=ClinicalSummary(
            allergies=to_clinical(cs.allergies),
            chronic_diseases=to_clinical(cs.chronic_diseases),
            active_medications=to_clinical(cs.active_medications),
            abnormal_labs=to_labs(cs.abnormal_labs),
        ),
        metadata={"source_pdf": source_pdf, "parser": "llm_structured_v1"},
    )


def enrich_record_citations(record: EMRRecord, pages: list[dict], from_table_pages: set[int] | None = None) -> EMRRecord:
    """Apply span-level citation matching to all clinical items in a record."""
    table_pages = from_table_pages or set()

    def enrich_source(source: SourceCitation, from_table: bool = False) -> SourceCitation:
        span = find_evidence_span(
            source.evidence_text,
            pages,
            document_id=source.document_id,
            from_table=from_table,
        )
        return SourceCitation(
            document_id=span["document_id"],
            page=span["page"],
            evidence_text=span["evidence_text"] or source.evidence_text,
            char_start=span.get("char_start"),
            char_end=span.get("char_end"),
            match_type=span.get("match_type"),
            confidence=span.get("confidence"),
        )

    allergies = [
        ClinicalItem(**{**item.model_dump(), "source": enrich_source(item.source)})
        for item in record.clinical_summary.allergies
    ]
    chronic = [
        ClinicalItem(**{**item.model_dump(), "source": enrich_source(item.source)})
        for item in record.clinical_summary.chronic_diseases
    ]
    meds = [
        ClinicalItem(**{**item.model_dump(), "source": enrich_source(item.source)})
        for item in record.clinical_summary.active_medications
    ]
    labs = [
        LabItem(**{
            **item.model_dump(),
            "source": enrich_source(item.source, from_table=item.source.page in table_pages),
        })
        for item in record.clinical_summary.abnormal_labs
    ]

    return EMRRecord(
        patient=record.patient,
        documents=record.documents,
        clinical_summary=ClinicalSummary(
            allergies=allergies,
            chronic_diseases=chronic,
            active_medications=meds,
            abnormal_labs=labs,
        ),
        metadata=record.metadata,
    )


def extract_emr_record(
    pages: list[dict],
    tables: list[dict],
    source_pdf: str,
    use_llm: bool = False,
) -> tuple[EMRRecord, ExtractionMode, str]:
    """Extract EMR record using LLM when configured, otherwise rule-based parser."""
    combined = "\n".join(p.get("text", "") for p in pages)

    if not use_llm:
        record = parse_emr_to_record(pages, tables, source_pdf=source_pdf)
        table_pages = {int(t.get("page", 1)) for t in tables}
        record = enrich_record_citations(record, pages, table_pages)
        record.metadata["extraction_mode"] = "rule_based"
        record.metadata["extraction_reason"] = "LLM disabled"
        return record, "rule_based", "LLM disabled"

    api_key, _, _ = _get_api_config()
    if not api_key:
        print("LLM structured extraction skipped: API key not configured. Using rule-based parser.")
        record = parse_emr_to_record(pages, tables, source_pdf=source_pdf)
        table_pages = {int(t.get("page", 1)) for t in tables}
        record = enrich_record_citations(record, pages, table_pages)
        record.metadata["extraction_mode"] = "llm_fallback_rule_based"
        record.metadata["extraction_reason"] = "API key not configured"
        return record, "llm_fallback_rule_based", "API key not configured"

    try:
        llm_raw = _call_llm(combined)
        llm_data = LLMExtractionOut.model_validate(llm_raw)
        record = _llm_output_to_record(llm_data, pages, source_pdf)
        record.metadata["extraction_mode"] = "llm"
        record.metadata["extraction_reason"] = "LLM extraction succeeded"
        return record, "llm", "LLM extraction succeeded"
    except (ValidationError, json.JSONDecodeError, KeyError, urllib.error.URLError, RuntimeError) as exc:
        print(f"LLM structured extraction failed ({exc}). Using rule-based parser.")
        record = parse_emr_to_record(pages, tables, source_pdf=source_pdf)
        table_pages = {int(t.get("page", 1)) for t in tables}
        record = enrich_record_citations(record, pages, table_pages)
        reason = f"LLM failed: {exc}"
        record.metadata["extraction_mode"] = "llm_fallback_invalid_schema"
        record.metadata["extraction_reason"] = reason
        return record, "llm_fallback_invalid_schema", reason
