# PDF Scan Toolkit Demo for Clinical RAG

Project độc lập để test pipeline **PDF → text/OCR/table/layout → EMR JSON có citation** phục vụ bài **Clinical RAG / EMR Summary**.

Project hỗ trợ hai mức pipeline:

| Pipeline | Mục đích |
|---|---|
| **Basic** | Baseline nhanh: PyMuPDF + pdfplumber + OCR optional |
| **Advanced** | PDF khó hơn: enhanced OCR, Camelot, layout blocks, patient normalization, span citation, LLM optional |

---

## Mục tiêu

```text
PDF mẫu nhiều loại (text / table / scan / mixed / public synthetic)
  → detect PDF type
  → extract text / table / layout bằng nhiều tool
  → optional OCR (Tesseract basic + enhanced)
  → normalize thông tin bệnh nhân
  → parse clinical summary (rule-based hoặc LLM)
  → gắn span-level citation cho từng claim
  → validate JSON bằng Pydantic
  → so sánh kết quả các tool
  → sinh report Markdown
```

Output JSON sẵn sàng đưa vào RAG pipeline (chunking, embedding, retrieval, citation verification).

---

## Kiến trúc

### Basic pipeline

```text
run_demo.py
  → detect_pdf_type()
  → extract_text_pymupdf()
  → extract_text_pdfplumber() + extract_tables_pdfplumber()
  → extract_ocr_optional()          # nếu scan/mixed
  → parse_emr_to_record()           # rule-based regex
  → validate_record()
  → pdf_scan_report.md
```

### Advanced pipeline

```text
run_advanced_compare.py
  → detect_pdf_type()
  → extract_text_pymupdf()
  → extract_text_pdfplumber() + extract_tables_pdfplumber()
  → extract_layout_blocks_pymupdf()
  → extract_tables_camelot()        # lattice + stream (selective)
  → extract_ocr_optional()        # basic
  → extract_ocr_enhanced()        # OpenCV preprocess + Tesseract
  → _select_best_pages()          # chọn text source tốt nhất mỗi page
  → _merge_tables()               # gộp bảng pdfplumber + camelot
  → extract_emr_record()          # rule-based hoặc LLM (--use-llm)
      ├── patient_normalizer.py
      ├── parse_emr_to_json.py
      ├── llm_structured_extractor.py   # optional
      └── span_citation.py
  → validate_record()
  → advanced_tool_comparison_report.md
```

---

## Cấu trúc thư mục

```text
pdf-scan-toolkit-demo-advanced/
├── README.md
├── .env.example                  # mẫu cấu hình LLM
├── requirements.txt              # dependencies cơ bản
├── requirements-ocr.txt          # pytesseract
├── requirements-advanced.txt     # OCR enhanced, Camelot, rapidfuzz
├── docs/
│   ├── ADVANCED_TOOLS_DEMO.md
│   └── PUBLIC_PDF_DATA.md
├── scripts/
│   ├── run_demo.py               # basic pipeline entrypoint
│   ├── run_advanced_compare.py   # advanced pipeline entrypoint
│   ├── run_public_pdf_compare.py # basic + public PDFs
│   ├── create_sample_pdfs.py
│   ├── create_advanced_sample_pdfs.py
│   └── download_public_pdfs.py
├── src/pdf_scan_toolkit/
│   ├── detect_pdf_type.py
│   ├── extract_text_pymupdf.py
│   ├── extract_pdfplumber.py
│   ├── extract_ocr_optional.py
│   ├── extract_ocr_enhanced.py
│   ├── extract_camelot.py
│   ├── extract_layout_pymupdf.py
│   ├── parse_emr_to_json.py
│   ├── patient_normalizer.py     # chuẩn hóa patient EN/VI
│   ├── span_citation.py          # citation span-level
│   ├── llm_structured_extractor.py
│   ├── validate_json.py
│   ├── schemas.py                # Pydantic models
│   ├── reporting.py
│   ├── run_pdf_scan_demo.py
│   └── run_advanced_compare.py
├── tests/
│   ├── test_pdf_scan_demo.py
│   ├── test_patient_normalizer.py
│   ├── test_span_citation.py
│   └── test_llm_fallback.py
└── data/
    ├── pdf_samples/              # 4 PDF basic demo
    ├── json_samples/
    ├── extracted_raw/
    ├── demo_outputs/
    ├── advanced_pdf_samples/     # 6 PDF advanced demo
    ├── advanced_json_samples/
    ├── advanced_extracted_raw/
    ├── advanced_demo_outputs/
    ├── public_pdf_samples/       # John Snow Labs synthetic PDFs
    ├── public_json_samples/
    ├── public_advanced_raw/
    └── public_advanced_outputs/
```

---

## Cài đặt

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Cài đặt advanced (khuyên dùng)

```bash
pip install -r requirements-advanced.txt
```

Bao gồm thêm: `pytesseract`, `opencv-python-headless`, `camelot-py`, `pandas`, `numpy`, `rapidfuzz`.

### OCR optional

```bash
pip install -r requirements-ocr.txt
```

Máy cần cài binary **Tesseract OCR** và có trong `PATH`. Nếu chưa cài, chương trình vẫn chạy, chỉ báo `OCR_SKIPPED`.

Camelot có thể cần **Ghostscript** trên một số máy.

---

## Dữ liệu mẫu

### Basic PDF (`data/pdf_samples/`)

| File | Loại | Mục đích |
|---|---|---|
| `patient_001_text.pdf` | PDF text layer | Test PyMuPDF / pdfplumber đọc text |
| `patient_002_table.pdf` | PDF có bảng | Test extract table / lab |
| `patient_003_scanned_image.pdf` | PDF ảnh/scan | Test detect scanned + OCR |
| `patient_004_mixed.pdf` | Mixed text + scan | Test file vừa text vừa ảnh |

### Advanced PDF (`data/advanced_pdf_samples/`)

| File | Mục đích |
|---|---|
| `advanced_001_text_dense.pdf` | Clinical note text dày đặc |
| `advanced_002_grid_table.pdf` | Bảng grid: thuốc + lab |
| `advanced_003_noisy_scan.pdf` | Scan nhiễu, không text layer |
| `advanced_004_rotated_scan.pdf` | Scan xoay |
| `advanced_005_two_column.pdf` | Layout 2 cột |
| `advanced_006_mixed_text_scan.pdf` | Page 1 text + page 2 scan |

Tạo lại:

```bash
python scripts/create_advanced_sample_pdfs.py
```

### Public synthetic PDF (`data/public_pdf_samples/`)

Nguồn: [JohnSnowLabs/pdf-deid-dataset](https://github.com/JohnSnowLabs/pdf-deid-dataset) — PDF y tế **fully synthetic**, 3 mức:

| Level | Ý nghĩa |
|---|---|
| Easy | Layout sạch |
| Medium | Formatting/noise đa dạng |
| Hard | Layout dày, stress test OCR |

Tải mẫu:

```bash
python scripts/download_public_pdfs.py --count 2
```

Chi tiết: `docs/PUBLIC_PDF_DATA.md`

---

## Chạy demo

### 1. Basic demo

```bash
python scripts/run_demo.py --input data/pdf_samples --output data/json_samples
```

Kết quả:

```text
data/extracted_raw/        raw text/table từng tool
data/json_samples/         JSON EMR parse được
data/demo_outputs/         report so sánh tool
```

Report: `data/demo_outputs/pdf_scan_report.md`

### 2. Advanced demo

```bash
python scripts/run_advanced_compare.py \
  --input data/advanced_pdf_samples \
  --output data/advanced_json_samples
```

Kết quả:

```text
data/advanced_extracted_raw/     9 file JSON raw mỗi PDF
data/advanced_json_samples/      EMR JSON đã parse
data/advanced_demo_outputs/      report + summary
```

Report: `data/advanced_demo_outputs/advanced_tool_comparison_report.md`

### 3. Advanced trên public PDFs

```bash
python scripts/run_advanced_compare.py \
  --input data/public_pdf_samples \
  --output data/public_json_samples \
  --raw data/public_advanced_raw \
  --report data/public_advanced_outputs
```

### 4. Public PDF — basic pipeline

```bash
python scripts/run_public_pdf_compare.py
# hoặc bỏ qua download nếu PDF đã có sẵn:
python scripts/run_public_pdf_compare.py --skip-download
```

Report: `data/public_demo_outputs/pdf_scan_report.md`

---

## CLI reference — `run_advanced_compare.py`

```bash
python scripts/run_advanced_compare.py [OPTIONS]
```

| Flag | Mặc định | Mô tả |
|---|---|---|
| `--input` | `data/advanced_pdf_samples` | Thư mục chứa `*.pdf` |
| `--output` | `data/advanced_json_samples` | Thư mục ghi EMR JSON |
| `--raw` | `data/advanced_extracted_raw` | Thư mục ghi raw tool outputs |
| `--report` | `data/advanced_demo_outputs` | Thư mục ghi report |
| `--use-llm` | tắt | Bật LLM structured extraction |

Ví dụ đầy đủ:

```bash
python scripts/run_advanced_compare.py \
  --input data/public_pdf_samples \
  --output data/public_json_samples \
  --raw data/public_advanced_raw \
  --report data/public_advanced_outputs \
  --use-llm
```

---

## Cấu hình LLM (tùy chọn)

LLM chỉ chạy khi dùng `--use-llm`. Nếu thiếu API key hoặc lỗi, pipeline **tự fallback** về rule-based, không crash.

### Bước 1 — Tạo `.env`

```powershell
# Windows
copy .env.example .env
```

```bash
# macOS/Linux
cp .env.example .env
```

### Bước 2 — Điền API key

```env
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4o-mini
OPENROUTER_API_KEY=your_key_here
```

Hoặc dùng Gemini trực tiếp:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_key_here
```

### Bước 3 — Chạy

```bash
python scripts/run_advanced_compare.py \
  --input data/public_pdf_samples \
  --output data/public_json_samples \
  --use-llm
```

**Lưu ý:**

- File `.env` được tự động nạp khi import module LLM.
- Biến môi trường đã set trong shell **không bị ghi đè** bởi `.env`.
- Không commit `.env` (đã có trong `.gitignore`).
- Khi thiếu key, in warning: `LLM structured extraction skipped: API key not configured. Using rule-based parser.`

### Guardrails LLM

Prompt LLM có các ràng buộc:

- Chỉ trích xuất thông tin có trong text, không suy đoán.
- Mỗi item phải có `evidence_text`.
- Không đưa lời khuyên điều trị, không chẩn đoán mới.
- Output chỉ là JSON hợp lệ, validate bằng Pydantic.
- Sau LLM, chạy span citation matcher map evidence về page/offset.

---

## Module mới (Advanced)

### A. Patient Normalization (`patient_normalizer.py`)

Trích xuất linh hoạt từ raw text / OCR:

| Field | Label hỗ trợ (EN / VI) |
|---|---|
| `patient_id` | Patient ID, MRN, Medical Record Number, Mã bệnh nhân |
| `name` | Patient Name, Name, Họ tên |
| `dob` | DOB, Date of Birth, Ngày sinh |
| `gender` | Gender, Sex, Giới tính → `male` / `female` / `other` / `unknown` |
| `age` | Age, Tuổi (nếu có) |

DOB được normalize về `YYYY-MM-DD`. Thiếu field → `UNKNOWN` hoặc `null`, không crash.

Metadata lưu trong `metadata.patient_normalization`:

```json
{
  "patient_id": "PT-001",
  "name": "Nguyen Van A",
  "dob": "1968-03-12",
  "gender": "male",
  "normalization_confidence": 0.85,
  "source_spans": {
    "patient_id": { "page": 1, "text": "Patient ID: PT-001", "start": 10, "end": 16 }
  }
}
```

### B. Span-Level Citation (`span_citation.py`)

Nâng cấp citation từ page-level lên span-level:

| Field | Mô tả |
|---|---|
| `page` | Số trang |
| `evidence_text` | Đoạn text evidence |
| `char_start` / `char_end` | Vị trí ký tự trong raw text của page |
| `match_type` | `exact` / `case_insensitive` / `fuzzy` / `table_page_level` / `not_found` |
| `confidence` | 0.0 – 1.0 |

Ví dụ:

```json
{
  "source": {
    "document_id": "DOC-001",
    "page": 1,
    "evidence_text": "Allergy: Penicillin - rash and facial swelling.",
    "char_start": 193,
    "char_end": 240,
    "match_type": "exact",
    "confidence": 1.0
  }
}
```

Fuzzy match dùng `rapidfuzz` nếu có, fallback `difflib` nếu không cài.

### C. LLM Structured Extraction (`llm_structured_extractor.py`)

- Nhận raw text từ PDF/OCR.
- Nếu có API key + `--use-llm` → gọi LLM extract JSON theo schema.
- Nếu không → rule-based parser.
- Output validate Pydantic, sau đó enrich citation spans.

Extraction mode lưu trong `metadata`:

| Mode | Ý nghĩa |
|---|---|
| `rule_based` | LLM tắt (mặc định) |
| `llm` | LLM thành công |
| `llm_fallback_rule_based` | Thiếu API key |
| `llm_fallback_invalid_schema` | LLM lỗi / schema sai |

---

## JSON output schema

Top-level model: `EMRRecord` (Pydantic, `extra="forbid"`).

```json
{
  "patient": {
    "patient_id": "ADV-001",
    "name": "Nguyen Van Advanced",
    "dob": "1962-06-22",
    "gender": "male"
  },
  "documents": [
    {
      "document_id": "DOC-001",
      "doc_type": "emr_pdf_page",
      "source_pdf": "advanced_001_text_dense.pdf",
      "page": 1,
      "raw_text": "..."
    }
  ],
  "clinical_summary": {
    "allergies": [
      {
        "name": "Allergy",
        "value": "Penicillin - rash and facial swelling.",
        "status": "active",
        "source": {
          "document_id": "DOC-001",
          "page": 1,
          "evidence_text": "Allergy: Penicillin - rash and facial swelling.",
          "char_start": 193,
          "char_end": 240,
          "match_type": "exact",
          "confidence": 1.0
        }
      }
    ],
    "chronic_diseases": [],
    "active_medications": [],
    "abnormal_labs": []
  },
  "metadata": {
    "source_pdf": "advanced_001_text_dense.pdf",
    "parser": "rule_regex_v1",
    "extraction_mode": "rule_based",
    "extraction_reason": "LLM disabled",
    "patient_normalization": { "...": "..." },
    "tools": ["PyMuPDF", "pdfplumber", "Camelot", "..."],
    "selected_pages": [{ "page": 1, "source_tool": "pymupdf", "char_count": 552 }],
    "tables_merged": 0
  }
}
```

### Clinical summary gồm 4 nhóm

| Nhóm | Nguồn extract |
|---|---|
| `allergies` | Dòng chứa allergy / dị ứng |
| `chronic_diseases` | Từ khóa bệnh mạn (hypertension, diabetes, …) |
| `active_medications` | Từ khóa thuốc (metformin, amlodipine, …) |
| `abnormal_labs` | Regex lab từ text + bảng pdfplumber/Camelot |

---

## Raw tool outputs (mỗi PDF)

Trong thư mục `--raw`, mỗi PDF sinh 9 file:

```text
{stem}.detect.json
{stem}.pymupdf.json
{stem}.pdfplumber_text.json
{stem}.pdfplumber_tables.json
{stem}.camelot_lattice.json
{stem}.camelot_stream.json
{stem}.basic_ocr.json
{stem}.enhanced_ocr.json
{stem}.layout_blocks.json
```

---

## Report

### Basic report (`pdf_scan_report.md`)

| Metric | Ý nghĩa |
|---|---|
| `detected_type` | `text_pdf` / `scanned_pdf` / `mixed_pdf` / `empty_pdf` |
| `pymupdf_chars` | Số ký tự PyMuPDF đọc được |
| `pdfplumber_chars` | Số ký tự pdfplumber đọc được |
| `tables_found` | Số bảng pdfplumber tìm thấy |
| `ocr_status` | `OCR_OK` / `OCR_SKIPPED` / `OCR_EMPTY` |
| `json_status` | `PARSED` / `SKIPPED` |
| `citation_coverage` | Tỷ lệ item clinical có citation |

### Advanced report (`advanced_tool_comparison_report.md`)

Ngoài bảng tool-level comparison, report advanced có thêm:

**Normalization and Citation Quality**

| Cột | Ý nghĩa |
|---|---|
| Patient ID / Name / DOB / Gender | Kết quả patient normalization |
| Patient Confidence | `normalization_confidence` (0–1) |
| Span Citation Rate | % item có exact/fuzzy span match |
| Page Citation Rate | % item chỉ có page-level (table, v.v.) |
| Not Found | Số citation không tìm được evidence |

**Extraction Mode**

| Cột | Ý nghĩa |
|---|---|
| Mode | `rule_based` / `llm` / `llm_fallback_*` |
| Reason | Lý do chọn mode |

Companion JSON: `advanced_summary.json` (metrics đầy đủ per file).

---

## Chạy test

```bash
pytest tests -v
```

| File test | Nội dung |
|---|---|
| `test_pdf_scan_demo.py` | Basic pipeline end-to-end |
| `test_patient_normalizer.py` | Parse EN/VI, missing fields |
| `test_span_citation.py` | exact / case_insensitive / fuzzy / not_found |
| `test_llm_fallback.py` | Fallback khi thiếu API key, không gọi network |

Chạy nhanh:

```bash
pytest -q
```

---

## Tool đang dùng

| Nhu cầu | Tool / Module |
|---|---|
| Detect PDF type | PyMuPDF (`detect_pdf_type.py`) |
| Extract text nhanh | PyMuPDF (`extract_text_pymupdf.py`) |
| Extract text / table / layout | pdfplumber (`extract_pdfplumber.py`) |
| OCR basic | pytesseract (`extract_ocr_optional.py`) |
| OCR enhanced + preprocess | OpenCV + Tesseract (`extract_ocr_enhanced.py`) |
| Table extraction thay thế | Camelot lattice/stream (`extract_camelot.py`) |
| Layout blocks + bbox | PyMuPDF (`extract_layout_pymupdf.py`) |
| Patient normalization | `patient_normalizer.py` |
| Span citation | `span_citation.py` (+ rapidfuzz optional) |
| LLM extraction | `llm_structured_extractor.py` (OpenRouter / Gemini) |
| Parse EMR JSON | `parse_emr_to_json.py` |
| Validate schema + citation | `validate_json.py` + Pydantic |
| Tạo PDF mẫu | reportlab + Pillow |
| Test tự động | pytest |

---

## Giới hạn hiện tại

1. **Parser rule-based** phụ thuộc label/keyword — PDF public không có label chuẩn có thể trả `UNKNOWN` cho `patient_id`.
2. **Patient name trên OCR** — regex có thể bắt thêm text thừa khi layout OCR không rõ.
3. **Fuzzy citation** — hiệu quả phụ thuộc chất lượng OCR, không đảm bảo 100%.
4. **LLM** — cần API key + mạng; output phụ thuộc model; có fallback an toàn.
5. **BBox citation** — layout blocks đã extract nhưng chưa map sang pixel highlight trên PDF.
6. **Table evidence** — có thể chỉ đạt `table_page_level` khi text không khớp verbatim.
7. **Chưa tích hợp RAG** — chưa index Qdrant / embedding; output JSON sẵn sàng cho bước tiếp theo.
8. **Không phải thiết bị y tế** — demo kỹ thuật, không cung cấp lời khuyên lâm sàng.

---

## Gợi ý nâng cấp tiếp

1. PaddleOCR cho PDF scan tiếng Việt.
2. Coordinate-level citation: page + bounding box từ layout blocks.
3. Golden answer evaluation cho JSON output.
4. RAGAS / custom RAG evaluation: context recall, citation accuracy, patient isolation.
5. Tích hợp Synthea / C-CDA để sinh bệnh án synthetic có ground truth.
6. Chunking + embedding pipeline (Qdrant, pgvector, …).

---

## Tài liệu thêm

- `docs/ADVANCED_TOOLS_DEMO.md` — chi tiết advanced tools
- `docs/PUBLIC_PDF_DATA.md` — nguồn PDF public synthetic

---

## Quick start (tóm tắt)

```bash
# 1. Cài đặt
python -m venv .venv && .\.venv\Scripts\activate   # Windows
pip install -r requirements-advanced.txt

# 2. Chạy advanced demo
python scripts/run_advanced_compare.py

# 3. Chạy trên public PDFs
python scripts/download_public_pdfs.py --count 2
python scripts/run_advanced_compare.py \
  --input data/public_pdf_samples \
  --output data/public_json_samples \
  --raw data/public_advanced_raw \
  --report data/public_advanced_outputs

# 4. (Tùy chọn) Bật LLM
copy .env.example .env    # sửa API key
python scripts/run_advanced_compare.py --input data/public_pdf_samples --output data/public_json_samples --use-llm

# 5. Test
pytest tests -v
```
