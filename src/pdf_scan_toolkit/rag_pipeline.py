from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schemas import EMRRecord


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w]+", (text or "").lower(), flags=re.UNICODE)


@dataclass
class Chunk:
    chunk_id: str
    patient_id: str
    document_id: str
    page: int
    chunk_type: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SimpleBM25:
    """Lightweight BM25 scorer (offline, no extra dependencies)."""

    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.N = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / self.N if self.N else 0.0
        self.df: dict[str, int] = {}
        for doc in corpus:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        n = self.df.get(term, 0)
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        doc = self.corpus[doc_idx]
        if not doc:
            return 0.0
        dl = len(doc)
        tf_map: dict[str, int] = {}
        for t in doc:
            tf_map[t] = tf_map.get(t, 0) + 1
        score = 0.0
        for term in query_tokens:
            if term not in tf_map:
                continue
            tf = tf_map[term]
            idf = self._idf(term)
            denom = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            score += idf * (tf * (self.k1 + 1)) / denom
        return score


def load_records(input_dir: str | Path) -> list[EMRRecord]:
    input_dir = Path(input_dir)
    records: list[EMRRecord] = []
    for path in sorted(input_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append(EMRRecord.model_validate(data))
    if not records:
        raise FileNotFoundError(f"No JSON records found in {input_dir}")
    return records


def build_chunks(records: list[EMRRecord]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for record in records:
        pid = record.patient.patient_id
        for doc in record.documents:
            chunks.append(Chunk(
                chunk_id=f"{pid}:doc:{doc.document_id}:raw",
                patient_id=pid,
                document_id=doc.document_id,
                page=doc.page,
                chunk_type="raw_text",
                text=doc.raw_text,
                metadata={"source_pdf": doc.source_pdf},
            ))
        cs = record.clinical_summary
        for i, item in enumerate(cs.allergies):
            chunks.append(Chunk(
                chunk_id=f"{pid}:allergy:{i}",
                patient_id=pid,
                document_id=item.source.document_id,
                page=item.source.page,
                chunk_type="allergies",
                text=f"Di ung: {item.value}",
                metadata={"value": item.value},
            ))
        for i, item in enumerate(cs.chronic_diseases):
            chunks.append(Chunk(
                chunk_id=f"{pid}:chronic:{i}",
                patient_id=pid,
                document_id=item.source.document_id,
                page=item.source.page,
                chunk_type="chronic_diseases",
                text=f"Tien su benh: {item.value}",
                metadata={"value": item.value},
            ))
        for i, item in enumerate(cs.active_medications):
            chunks.append(Chunk(
                chunk_id=f"{pid}:med:{i}",
                patient_id=pid,
                document_id=item.source.document_id,
                page=item.source.page,
                chunk_type="active_medications",
                text=f"Thuoc dang dung: {item.value}",
                metadata={"value": item.value},
            ))
        for i, item in enumerate(cs.abnormal_labs):
            flag = item.interpretation
            chunks.append(Chunk(
                chunk_id=f"{pid}:lab:{i}",
                patient_id=pid,
                document_id=item.source.document_id,
                page=item.source.page,
                chunk_type="abnormal_labs",
                text=(
                    f"Xet nghiem {item.test_name}: {item.value} {item.unit or ''} "
                    f"({flag}), tham chieu {item.reference_range or 'N/A'}"
                ),
                metadata={
                    "test_name": item.test_name,
                    "value": item.value,
                    "interpretation": item.interpretation,
                },
            ))
    return chunks


def _chunk_to_citation(chunk: Chunk) -> dict[str, Any]:
    return {
        "document_id": chunk.document_id,
        "page": chunk.page,
        "evidence_text": chunk.text[:500],
        "chunk_id": chunk.chunk_id,
        "chunk_type": chunk.chunk_type,
    }


def _infer_target_types(question: str) -> list[str]:
    q = question.lower()
    types: list[str] = []
    if any(k in q for k in ["di ung", "dị ứng", "allerg"]):
        types.append("allergies")
    if any(k in q for k in ["thuoc", "thuốc", "medication", "dang dung", "đang dùng"]):
        types.append("active_medications")
    if any(k in q for k in ["xet nghiem", "xét nghiệm", "lab", "chi so", "chỉ số", "bat thuong", "bất thường"]):
        types.append("abnormal_labs")
    if any(k in q for k in ["tien su", "tiền sử", "benh man", "bệnh mạn", "chronic"]):
        types.append("chronic_diseases")
    if not types:
        types = ["allergies", "active_medications", "abnormal_labs", "chronic_diseases", "raw_text"]
    return types


def _compose_answer(question: str, retrieved: list[Chunk]) -> str:
    if not retrieved:
        return "Khong tim thay thong tin lien quan trong ho so benh nhan."

    q = question.lower()
    primary = retrieved[0]

    if primary.chunk_type == "allergies" or any(k in q for k in ["di ung", "allerg"]):
        values = [c.metadata.get("value", c.text) for c in retrieved if c.chunk_type == "allergies"]
        if not values:
            values = [c.text for c in retrieved[:2]]
        pid = primary.patient_id
        joined = "; ".join(values)
        return f"Benh nhan {pid} co di ung: {joined}"

    if primary.chunk_type == "active_medications" or any(k in q for k in ["thuoc", "medication"]):
        values = [c.metadata.get("value", c.text) for c in retrieved if c.chunk_type == "active_medications"]
        if not values:
            values = [c.text for c in retrieved[:2]]
        pid = primary.patient_id
        joined = "; ".join(values)
        return f"Benh nhan {pid} dang dung: {joined}"

    if primary.chunk_type == "abnormal_labs" or any(k in q for k in ["xet nghiem", "lab", "chi so"]):
        parts = []
        for c in retrieved:
            if c.chunk_type == "abnormal_labs":
                tn = c.metadata.get("test_name", "")
                val = c.metadata.get("value", "")
                interp = c.metadata.get("interpretation", "")
                parts.append(f"{tn}={val} ({interp})")
        if not parts:
            parts = [c.text for c in retrieved[:3]]
        pid = primary.patient_id
        return f"Chi so xet nghiem bat thuong cua {pid}: " + "; ".join(parts)

    return retrieved[0].text[:400]


def retrieve(
    chunks: list[Chunk],
    question: str,
    patient_id: str | None = None,
    top_k: int = 5,
) -> list[Chunk]:
    filtered = [c for c in chunks if not patient_id or c.patient_id == patient_id]
    if not filtered:
        return []

    target_types = _infer_target_types(question)
    type_boosted = []
    for c in filtered:
        boost = 2.0 if c.chunk_type in target_types else 1.0
        type_boosted.append((c, boost))

    corpus = [_tokenize(c.text) for c, _ in type_boosted]
    bm25 = SimpleBM25(corpus)
    query_tokens = _tokenize(question)

    scored: list[tuple[Chunk, float]] = []
    for idx, (chunk, boost) in enumerate(type_boosted):
        s = bm25.score(query_tokens, idx) * boost
        scored.append((chunk, s))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, s in scored[:top_k] if s > 0] or [c for c, _ in scored[:top_k]]


def query_rag(
    input_dir: str | Path,
    question: str,
    patient_id: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    records = load_records(input_dir)
    chunks = build_chunks(records)
    retrieved = retrieve(chunks, question, patient_id=patient_id, top_k=top_k)
    answer = _compose_answer(question, retrieved)

    citations = [_chunk_to_citation(c) for c in retrieved[:3]]
    retrieved_out = [
        {
            "chunk_id": c.chunk_id,
            "chunk_type": c.chunk_type,
            "patient_id": c.patient_id,
            "document_id": c.document_id,
            "page": c.page,
            "text": c.text,
            "score_rank": i + 1,
        }
        for i, c in enumerate(retrieved)
    ]

    return {
        "question": question,
        "patient_id": patient_id or (retrieved[0].patient_id if retrieved else None),
        "answer": answer,
        "citations": citations,
        "retrieved": retrieved_out,
    }
