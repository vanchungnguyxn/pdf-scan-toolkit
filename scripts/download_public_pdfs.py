from __future__ import annotations

"""Download public synthetic/de-identified medical-style PDF samples.

These files come from JohnSnowLabs/pdf-deid-dataset.
They are synthetic medical-style PDFs, not real patient records.

Usage:
    python scripts/download_public_pdfs.py
    python scripts/download_public_pdfs.py --levels easy medium hard --count 2
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "public_pdf_samples"
MANIFEST_PATH = ROOT / "data" / "public_sources_manifest.json"

BASE = "https://raw.githubusercontent.com/JohnSnowLabs/pdf-deid-dataset/main/PDF_Original"


def build_manifest(count: int = 2, levels: Iterable[str] = ("easy", "medium", "hard")) -> list[dict]:
    items: list[dict] = []
    levels = [x.lower() for x in levels]
    if "easy" in levels:
        for i in range(count):
            items.append({
                "source": "JohnSnowLabs/pdf-deid-dataset",
                "level": "easy",
                "filename": f"johnsnow_easy_{i}.pdf",
                "url": f"{BASE}/Easy/PDF_Deid_Deidentification_{i}.pdf",
                "notes": "Synthetic medical-style PDF, clean layout.",
            })
    if "medium" in levels:
        for i in range(count):
            items.append({
                "source": "JohnSnowLabs/pdf-deid-dataset",
                "level": "medium",
                "filename": f"johnsnow_medium_{i}.pdf",
                "url": f"{BASE}/Medium/PDF_Deid_Deidentification_Medium_{i}.pdf",
                "notes": "Synthetic medical-style PDF with varied formatting/noise.",
            })
    if "hard" in levels:
        for i in range(count):
            items.append({
                "source": "JohnSnowLabs/pdf-deid-dataset",
                "level": "hard",
                "filename": f"johnsnow_hard_{i}.pdf",
                "url": f"{BASE}/Hard/PDF_Deid_Deidentification_Hard_{i}.pdf",
                "notes": "Synthetic medical-style PDF with dense layout/noise; OCR/layout stress test.",
            })
    return items


def download_file(url: str, out_path: Path, timeout: int = 60) -> tuple[bool, str]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "pdf-scan-toolkit-demo/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read()
        if status >= 400:
            return False, f"HTTP {status}"
        if not data.startswith(b"%PDF"):
            # GitHub/raw failures may return HTML or text; make the problem obvious.
            preview = data[:80].decode("utf-8", errors="replace").replace("\n", " ")
            return False, f"Downloaded content is not a PDF. Content-Type={content_type!r}, preview={preview!r}"
        out_path.write_bytes(data)
        return True, f"OK ({len(data)} bytes)"
    except urllib.error.HTTPError as e:
        return False, f"HTTPError {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URLError: {e.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Download public synthetic medical-style PDF samples.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output folder for downloaded PDFs")
    parser.add_argument("--count", type=int, default=2, help="Number of files per level")
    parser.add_argument("--levels", nargs="+", default=["easy", "medium", "hard"], choices=["easy", "medium", "hard"], help="Difficulty levels to download")
    parser.add_argument("--manifest-only", action="store_true", help="Only write manifest JSON, do not download")
    args = parser.parse_args()

    out_dir = Path(args.out)
    manifest = build_manifest(count=args.count, levels=args.levels)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifest written: {MANIFEST_PATH}")

    if args.manifest_only:
        print("Manifest-only mode. No files downloaded.")
        return 0

    ok_count = 0
    for item in manifest:
        out_path = out_dir / item["filename"]
        print(f"Downloading {item['level']} -> {out_path.name}")
        ok, msg = download_file(item["url"], out_path)
        print(f"  {msg}")
        if ok:
            ok_count += 1

    print(f"Downloaded {ok_count}/{len(manifest)} PDF files to {out_dir}")
    if ok_count == 0:
        print("No PDFs downloaded. Check internet access or download manually from the URLs in data/public_sources_manifest.json.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
