# PDF Scan Demo Report

## Tool Comparison

| File | Type | Pages | PyMuPDF chars | pdfplumber chars | Tables | OCR | JSON | Citation coverage |
|---|---|---:|---:|---:|---:|---|---|---:|
| patient_001_text.pdf | text_pdf | 1 | 450 | 450 | 0 | OCR_OK | PARSED | 100.0% |
| patient_002_table.pdf | text_pdf | 1 | 492 | 492 | 2 | OCR_OK | PARSED | 100.0% |
| patient_003_scanned_image.pdf | scanned_pdf | 1 | 0 | 0 | 0 | OCR_OK | PARSED | 100.0% |
| patient_004_mixed.pdf | mixed_pdf | 2 | 245 | 245 | 0 | OCR_OK | PARSED | 100.0% |

## Parsed JSON Summary

| File | Patient | Allergies | Chronic | Medications | Abnormal Labs | Validation | Notes |
|---|---|---:|---:|---:|---:|---|---|
| patient_001_text.pdf | PT-001 | 1 | 2 | 2 | 2 | PASS |  |
| patient_002_table.pdf | PT-002 | 1 | 3 | 3 | 2 | PASS | Table evidence not verbatim in text, accepted by page-level source: Creatinine; Table evidence not verbatim in text, accepted by page-level source: eGFR |
| patient_003_scanned_image.pdf | PT-003 | 1 | 1 | 1 | 1 | PASS |  |
| patient_004_mixed.pdf | PT-004 | 1 | 1 | 1 | 1 | PASS |  |

## How to interpret

- `text_pdf`: PDF có text layer, PyMuPDF/pdfplumber đọc được trực tiếp.
- `scanned_pdf`: PDF là ảnh, cần OCR để lấy text.
- `mixed_pdf`: PDF có cả page text và page ảnh.
- `OCR_SKIPPED`: máy chưa cài OCR package hoặc binary Tesseract; demo vẫn chạy bình thường.
- `Citation coverage`: tỷ lệ clinical item có document/page/evidence_text.

## Next steps

1. Thêm OCR mạnh hơn như PaddleOCR cho tiếng Việt và bảng scan.
2. Thêm bounding box citation để highlight đúng dòng trong PDF viewer.
3. Đưa JSON output vào Qdrant/PostgreSQL để xây dựng RAG pipeline.
4. Tạo golden answer để đánh giá extraction và RAG.
