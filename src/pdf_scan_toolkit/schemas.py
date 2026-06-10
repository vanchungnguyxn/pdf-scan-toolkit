from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class SourceCitation(BaseModel):
    document_id: str
    page: int = Field(ge=1)
    evidence_text: str = Field(min_length=1)
    char_start: int | None = None
    char_end: int | None = None
    match_type: str | None = None
    confidence: float | None = None


class ClinicalItem(BaseModel):
    name: str
    value: str
    status: str = "unknown"
    source: SourceCitation


class LabItem(BaseModel):
    test_name: str
    value: str
    unit: str | None = None
    reference_range: str | None = None
    interpretation: Literal["high", "low", "normal", "abnormal", "unknown"] = "unknown"
    source: SourceCitation


class ClinicalSummary(BaseModel):
    allergies: list[ClinicalItem] = Field(default_factory=list)
    chronic_diseases: list[ClinicalItem] = Field(default_factory=list)
    active_medications: list[ClinicalItem] = Field(default_factory=list)
    abnormal_labs: list[LabItem] = Field(default_factory=list)


class Patient(BaseModel):
    patient_id: str = "UNKNOWN"
    name: str = "UNKNOWN"
    dob: str | None = None
    gender: str | None = None


class Document(BaseModel):
    document_id: str
    doc_type: str = "unknown"
    created_at: str | None = None
    source_pdf: str
    page: int = Field(ge=1)
    raw_text: str


class EMRRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient: Patient
    documents: list[Document]
    clinical_summary: ClinicalSummary
    metadata: dict[str, Any] = Field(default_factory=dict)


class PDFTypeReport(BaseModel):
    file_path: str
    pdf_type: Literal["text_pdf", "scanned_pdf", "mixed_pdf", "empty_pdf"]
    total_pages: int
    has_text_layer: bool
    page_char_counts: list[int]


class ToolComparisonRow(BaseModel):
    file: str
    detected_type: str
    pages: int
    pymupdf_chars: int
    pdfplumber_chars: int
    tables_found: int
    ocr_status: str
    json_status: str
    citation_coverage: str
