# Public PDF Data for More Realistic Testing

Dữ liệu thật của bệnh nhân không nên dùng cho demo nếu chưa có phê duyệt/ẩn danh rõ ràng. Với project Clinical RAG, nên dùng **synthetic** hoặc **fictional/de-identified** data.

## Nguồn khuyên dùng

### 1. JohnSnowLabs/pdf-deid-dataset

Repo: `JohnSnowLabs/pdf-deid-dataset`

Đây là bộ PDF y tế **fully synthetic**, chia 3 mức:

| Level | Ý nghĩa test |
|---|---|
| Easy | Layout sạch, dễ đọc |
| Medium | Formatting/noise đa dạng hơn |
| Hard | Layout dày, nhiễu, phù hợp stress test OCR/layout |

Nội dung có các section giống hồ sơ y tế:

- Patient Summary
- Patient Demographics
- Patient Vitals
- Doctor Notes
- Past Hospital Visits
- Current Medications
- Medical Tests

Chạy tải mẫu:

```bash
python scripts/download_public_pdfs.py --count 2
```

Chạy so sánh tool trên bộ public PDF:

```bash
python scripts/run_public_pdf_compare.py
```

Nếu mạng GitHub/raw bị chặn, tải thủ công các file PDF từ repo rồi đặt vào:

```text
data/public_pdf_samples/
```

Sau đó chạy:

```bash
python scripts/run_public_pdf_compare.py --skip-download
```

## So sánh với PDF tự sinh

Chạy bộ PDF tự sinh:

```bash
python scripts/run_demo.py --input data/pdf_samples --output data/json_samples
```

Chạy bộ PDF public:

```bash
python scripts/run_public_pdf_compare.py --skip-download
```

So sánh 2 report:

```text
data/demo_outputs/pdf_scan_report.md
data/public_demo_outputs/pdf_scan_report.md
```

## Gợi ý cách đưa vào báo cáo

- PDF tự sinh giúp chứng minh luồng end-to-end có ground truth rõ.
- PDF public synthetic giúp chứng minh tool không chỉ chạy trên dữ liệu do nhóm tự tạo.
- Easy/Medium/Hard giúp so sánh độ bền của PyMuPDF, pdfplumber và OCR.
- Nếu PDF public không parse đủ 4 nhóm Clinical RAG thì vẫn hợp lý: mục tiêu của nó là stress test extraction/layout/OCR, còn golden clinical summary nên tạo từ sample JSON/Synthea/C-CDA.

## Nguồn nâng cấp tiếp

### Synthea

Synthea sinh dữ liệu bệnh nhân synthetic ở các format FHIR, C-CDA, CSV. Phù hợp để tạo bộ bệnh án có bệnh nền, thuốc, dị ứng, xét nghiệm rồi render ngược ra PDF.

### HL7 C-CDA Examples

HL7 có các C-CDA example như Discharge Summary với dữ liệu fictional. Có thể dùng làm nguồn structured clinical content rồi convert thành PDF text để test parser/RAG.
