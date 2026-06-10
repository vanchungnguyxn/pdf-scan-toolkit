# Advanced PDF Tool Comparison Report

This report compares basic text extraction with advanced OCR, table, and layout tools.

## Tool-Level Comparison

| File | Type | Pages | PyMuPDF | pdfplumber | OCR basic | OCR enhanced | pdfplumber tables | Camelot lattice | Camelot stream | Layout blocks | Selected source | JSON | Citation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| johnsnow_easy_0.pdf | text_pdf | 3 | 3090 | 3002 | 0 | 0 | 3 | 0 | 0 | 65 | pymupdf | PARSED | 100.0% |
| johnsnow_easy_1.pdf | text_pdf | 3 | 2979 | 2889 | 0 | 0 | 1 | 0 | 0 | 64 | pymupdf | PARSED | 100.0% |
| johnsnow_hard_0.pdf | scanned_pdf | 2 | 0 | 0 | 2289 | 0 | 0 | 0 | 0 | 0 | tesseract_basic | PARSED | 100.0% |
| johnsnow_hard_1.pdf | scanned_pdf | 2 | 0 | 0 | 2701 | 0 | 0 | 0 | 0 | 0 | tesseract_basic | PARSED | 100.0% |
| johnsnow_medium_0.pdf | scanned_pdf | 4 | 0 | 0 | 3101 | 0 | 0 | 0 | 0 | 0 | tesseract_basic | PARSED | 100.0% |
| johnsnow_medium_1.pdf | scanned_pdf | 4 | 0 | 0 | 2818 | 0 | 0 | 0 | 0 | 0 | tesseract_basic | PARSED | 100.0% |

## Parsed Clinical Summary

| File | Patient | Allergies | Chronic | Medications | Abnormal Labs | Validation | Notes |
|---|---|---:|---:|---:|---:|---|---|
| johnsnow_easy_0.pdf | UNKNOWN | 0 | 1 | 8 | 0 | PASS |  |
| johnsnow_easy_1.pdf | UNKNOWN | 0 | 1 | 9 | 0 | PASS |  |
| johnsnow_hard_0.pdf | 4829746 | 0 | 1 | 4 | 0 | PASS |  |
| johnsnow_hard_1.pdf | 9509645 | 0 | 0 | 4 | 0 | PASS |  |
| johnsnow_medium_0.pdf | UNKNOWN | 0 | 0 | 9 | 0 | PASS |  |
| johnsnow_medium_1.pdf | UNKNOWN | 0 | 1 | 10 | 0 | PASS |  |

## Normalization and Citation Quality

| File | Patient ID | Name | DOB | Gender | Patient Confidence | Span Citation Rate | Page Citation Rate | Not Found |
|---|---|---|---|---|---:|---:|---:|---:|
| johnsnow_easy_0.pdf | UNKNOWN | Kimberly | 1977-05-24 | female | 0.75 | 100.0% | 0.0% | 0 |
| johnsnow_easy_1.pdf | UNKNOWN | Elizabeth | 1949-06-07 | female | 0.75 | 100.0% | 0.0% | 0 |
| johnsnow_hard_0.pdf | 4829746 | Jonathan Mi MRN: 4829746 | 2005-07-15 | unknown | 0.75 | 100.0% | 0.0% | 0 |
| johnsnow_hard_1.pdf | 9509645 | Beth Barber Diagnostic Form: DF-196 | 1981-10-22 | unknown | 0.75 | 100.0% | 0.0% | 0 |
| johnsnow_medium_0.pdf | UNKNOWN | Susan Frances Martin Date Of Birth : 09/03/1951 | 1951-03-09 | female | 0.75 | 100.0% | 0.0% | 0 |
| johnsnow_medium_1.pdf | UNKNOWN | Justin Norman Date Of Birth : 28/12/1965. | 1965-12-28 | male | 0.75 | 100.0% | 0.0% | 0 |

## Extraction Mode

| File | Mode | Reason |
|---|---|---|
| johnsnow_easy_0.pdf | rule_based | LLM disabled |
| johnsnow_easy_1.pdf | rule_based | LLM disabled |
| johnsnow_hard_0.pdf | rule_based | LLM disabled |
| johnsnow_hard_1.pdf | rule_based | LLM disabled |
| johnsnow_medium_0.pdf | rule_based | LLM disabled |
| johnsnow_medium_1.pdf | rule_based | LLM disabled |

Compared with the previous advanced version, this version improves patient normalization and distinguishes span-level citations from page-level citations. LLM structured extraction is optional and safely falls back to rule-based extraction when API keys are not configured.

## What improved compared with the basic demo

- `Tesseract enhanced` renders pages at higher DPI and applies preprocessing before OCR.
- `Camelot lattice/stream` gives an alternative table extractor when pdfplumber misses grid tables.
- `PyMuPDF layout blocks` records bounding boxes for future PDF source highlighting.
- The advanced selector chooses the best text source per page, so mixed text/scan PDFs can still produce JSON.

## Limitations

- OCR may still fail on rotated, blurred, handwritten, or very noisy scans.
- Rule-based clinical extraction is deterministic but limited; optional LLM extraction (`--use-llm`) improves flexible documents when API keys are configured.
- This demo is not a medical device and does not provide clinical advice.
