# Verification Report

Generated after running the priority pipeline end-to-end (offline).

## Commands executed

```bash
python scripts/run_demo.py --input data/pdf_samples --output data/json_samples
python scripts/run_closed_loop_demo.py --count 3
python scripts/run_rag_query.py --input data/roundtrip_json_samples --patient-id SYN-001 --question "Benh nhan SYN-001 co di ung gi?"
python scripts/evaluate_extraction.py
python scripts/evaluate_rag.py
python -m pytest tests -q
```

## Part 1: PDF → JSON

| Metric | Result |
|--------|--------|
| PDF files processed | 4 |
| JSON outputs | 4 |
| Report | `data/demo_outputs/pdf_scan_report.md` |
| Status | PASS |

## Part 2: Closed-loop (JSON → PDF → JSON)

| Metric | Result |
|--------|--------|
| Synthetic JSON | 3 |
| Synthetic PDF | 3 |
| Roundtrip JSON | 3 |
| Comparisons PASS | 3/3 |
| Summary | `data/roundtrip_outputs/closed_loop_summary.json` |
| Status | PASS |

## Part 3: RAG baseline

| Query | Patient | Answer contains | Citations |
|-------|---------|-----------------|-----------|
| Benh nhan SYN-001 co di ung gi? | SYN-001 | Penicillin | 3 |
| SYN-003 dang dung thuoc nao? | SYN-003 | Insulin | 2 |
| Chi so xet nghiem bat thuong cua SYN-002 la gi? | SYN-002 | Creatinine, eGFR | 3 |

Status: PASS (all queries returned answer + citations with document_id, page, evidence_text)

## Part 4: Evaluation

| Metric | Passed | Total | Rate |
|--------|--------|-------|------|
| Extraction | 3 | 3 | 100% |
| RAG | 3 | 3 | 100% |

Reports: `eval/results/extraction_eval.json`, `eval/results/rag_eval.json`

## Part 5: Pytest

```
20 passed in ~4s
```

## Notes

- OCR/Tesseract: optional; scanned PDFs skip JSON parse with clear warning if OCR unavailable.
- RAG baseline uses offline BM25/keyword retrieval (no Qdrant, no LLM/API required).
- All outputs live under `data/` or `eval/` — no hardcoded personal paths.
