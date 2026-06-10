from __future__ import annotations

import difflib
import re
from typing import Any, Literal

MatchType = Literal["exact", "case_insensitive", "fuzzy", "table_page_level", "not_found"]

try:
    from rapidfuzz import fuzz as _rapidfuzz

    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _fuzzy_ratio(a: str, b: str) -> float:
    if _HAS_RAPIDFUZZ:
        return _rapidfuzz.partial_ratio(a, b) / 100.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _best_fuzzy_window(haystack: str, needle: str, min_ratio: float = 0.75) -> tuple[int, int, float] | None:
    needle = _norm_ws(needle)
    if not needle:
        return None
    n_len = len(needle)
    if n_len > len(haystack):
        return None
    best: tuple[int, int, float] | None = None
    step = max(1, n_len // 4)
    for start in range(0, len(haystack) - n_len + 1, step):
        end = min(len(haystack), start + n_len + max(10, n_len // 5))
        window = haystack[start:end]
        ratio = _fuzzy_ratio(needle.lower(), window.lower())
        if ratio >= min_ratio and (best is None or ratio > best[2]):
            best = (start, end, ratio)
    if best:
        return best
    ratio = _fuzzy_ratio(needle.lower(), haystack.lower())
    if ratio >= min_ratio:
        return 0, len(haystack), ratio
    return None


def find_evidence_span(
    evidence_text: str,
    pages: list[dict],
    document_id: str | None = None,
    from_table: bool = False,
) -> dict[str, Any]:
    """Locate evidence_text within page raw text and return span-level citation metadata."""
    evidence = _norm_ws(evidence_text)
    if not evidence:
        page = int(pages[0].get("page", 1)) if pages else 1
        doc_id = document_id or f"DOC-{page:03d}"
        return {
            "document_id": doc_id,
            "page": page,
            "evidence_text": evidence_text or "",
            "char_start": None,
            "char_end": None,
            "match_type": "not_found",
            "confidence": 0.0,
        }

    for page_info in pages:
        page_no = int(page_info.get("page", 1))
        raw_text = page_info.get("text", "") or ""
        doc_id = document_id or f"DOC-{page_no:03d}"

        idx = raw_text.find(evidence)
        if idx >= 0:
            return {
                "document_id": doc_id,
                "page": page_no,
                "evidence_text": evidence,
                "char_start": idx,
                "char_end": idx + len(evidence),
                "match_type": "exact",
                "confidence": 1.0,
            }

        low_raw = raw_text.lower()
        low_ev = evidence.lower()
        idx_ci = low_raw.find(low_ev)
        if idx_ci >= 0:
            return {
                "document_id": doc_id,
                "page": page_no,
                "evidence_text": evidence,
                "char_start": idx_ci,
                "char_end": idx_ci + len(evidence),
                "match_type": "case_insensitive",
                "confidence": 0.95,
            }

        fuzzy = _best_fuzzy_window(raw_text, evidence)
        if fuzzy:
            start, end, ratio = fuzzy
            return {
                "document_id": doc_id,
                "page": page_no,
                "evidence_text": evidence,
                "char_start": start,
                "char_end": end,
                "match_type": "fuzzy",
                "confidence": round(ratio, 2),
            }

    if from_table and pages:
        page_no = int(pages[0].get("page", 1))
        doc_id = document_id or f"DOC-{page_no:03d}"
        return {
            "document_id": doc_id,
            "page": page_no,
            "evidence_text": evidence,
            "char_start": None,
            "char_end": None,
            "match_type": "table_page_level",
            "confidence": 0.5,
        }

    page = int(pages[0].get("page", 1)) if pages else 1
    doc_id = document_id or f"DOC-{page:03d}"
    return {
        "document_id": doc_id,
        "page": page,
        "evidence_text": evidence,
        "char_start": None,
        "char_end": None,
        "match_type": "not_found",
        "confidence": 0.0,
    }


def is_span_level(match_type: str | None) -> bool:
    return match_type in {"exact", "case_insensitive", "fuzzy"}


def is_page_level(match_type: str | None) -> bool:
    return match_type in {"table_page_level", "not_found"} or match_type is None
