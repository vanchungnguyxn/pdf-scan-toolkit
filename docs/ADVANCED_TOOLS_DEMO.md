# Advanced PDF Tools Demo

This demo extends the basic PDF → JSON pipeline with more advanced extraction tools:

- **Tesseract OCR enhanced**: renders pages at 300 DPI, applies grayscale/threshold preprocessing, and OCRs with `vie+eng`.
- **Camelot lattice/stream**: extracts grid/stream-style tables as an alternative to pdfplumber.
- **PyMuPDF layout blocks**: extracts text blocks with bounding boxes for future citation highlighting.
- **Best-page selector**: chooses the strongest text source per page, useful for mixed PDFs where one page has text and another page is scanned.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-advanced.txt
```

If OCR is needed on Windows, install Tesseract OCR and make sure `tesseract.exe` is in PATH.

## Create advanced sample PDFs

```powershell
python scripts/create_advanced_sample_pdfs.py
```

This creates:

| File | Purpose |
|---|---|
| `advanced_001_text_dense.pdf` | Dense text-layer clinical note |
| `advanced_002_grid_table.pdf` | Grid tables for medications and lab results |
| `advanced_003_noisy_scan.pdf` | Image-only noisy scanned PDF |
| `advanced_004_rotated_scan.pdf` | Rotated image-only scan |
| `advanced_005_two_column.pdf` | Two-column layout text PDF |
| `advanced_006_mixed_text_scan.pdf` | Page 1 text + page 2 scanned lab image |

## Run advanced comparison

```powershell
python scripts/run_advanced_compare.py --input data/advanced_pdf_samples --output data/advanced_json_samples
```

Report:

```text
data/advanced_demo_outputs/advanced_tool_comparison_report.md
```

Raw tool outputs:

```text
data/advanced_extracted_raw/
```

## Run on public PDFs you downloaded

After running:

```powershell
python scripts/download_public_pdfs.py --count 2
```

Run advanced comparison on the public dataset:

```powershell
python scripts/run_advanced_compare.py --input data/public_pdf_samples --output data/public_json_samples --raw data/public_advanced_raw --report data/public_advanced_outputs
```

## How to explain the result

Use this framing in your report:

> The basic pipeline establishes a deterministic PDF → JSON baseline. The advanced pipeline adds OCR preprocessing, Camelot table extraction, and layout block extraction to handle scanned PDFs, grid tables, mixed PDFs, and future source highlighting. Results are compared per tool using extracted character counts, tables found, selected text source, JSON parse status, and citation coverage.
