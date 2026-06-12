from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.rag_pipeline import build_chunks, load_records, query_rag, retrieve


def test_rag_query_with_roundtrip_samples():
    input_dir = ROOT / "data/roundtrip_json_samples"
    if not input_dir.exists() or not list(input_dir.glob("*.json")):
        # Generate minimal closed-loop data if missing.
        from pdf_scan_toolkit.run_closed_loop_demo import run_closed_loop
        run_closed_loop(count=3)

    result = query_rag(
        input_dir=input_dir,
        question="Benh nhan SYN-001 co di ung gi?",
        patient_id="SYN-001",
    )
    assert result["patient_id"] == "SYN-001"
    assert "penicillin" in result["answer"].lower()
    assert len(result["citations"]) >= 1
    assert result["citations"][0]["document_id"]
    assert result["citations"][0]["page"] >= 1
    assert result["citations"][0]["evidence_text"]
    assert len(result["retrieved"]) >= 1


def test_retrieve_filters_by_patient():
    records = load_records(ROOT / "data/json_samples")
    chunks = build_chunks(records)
    retrieved = retrieve(chunks, "di ung", patient_id="PT-001", top_k=3)
    assert retrieved
    assert all(c.patient_id == "PT-001" for c in retrieved)
