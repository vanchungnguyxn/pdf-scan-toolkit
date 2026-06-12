# PDF Scan Demo Report

## Tool Comparison

| File | Type | Pages | PyMuPDF chars | pdfplumber chars | Tables | OCR | JSON | Citation coverage |
|---|---|---:|---:|---:|---:|---|---|---:|
| syn-001_emr.pdf | text_pdf | 1 | 460 | 460 | 0 | OCR_OK | PARSED | 100.0% |
| syn-002_emr.pdf | text_pdf | 1 | 416 | 416 | 0 | OCR_OK | PARSED | 100.0% |
| syn-003_emr.pdf | text_pdf | 1 | 286 | 286 | 0 | OCR_OK | PARSED | 100.0% |

## Parsed JSON Summary

| File | Patient | Allergies | Chronic | Medications | Abnormal Labs | Validation | Notes |
|---|---|---:|---:|---:|---:|---|---|
| syn-001_emr.pdf | SYN-001 | 1 | 2 | 2 | 2 | PASS | Page-level citation only (no span offsets): Allergy; Page-level citation only (no span offsets): Chronic disease |
| syn-002_emr.pdf | SYN-002 | 1 | 3 | 2 | 2 | PASS | Page-level citation only (no span offsets): Allergy; Page-level citation only (no span offsets): Chronic disease |
| syn-003_emr.pdf | SYN-003 | 1 | 1 | 1 | 1 | PASS | Page-level citation only (no span offsets): Allergy; Page-level citation only (no span offsets): Chronic disease |

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
