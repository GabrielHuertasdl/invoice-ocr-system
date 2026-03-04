"""
Structured data extraction from raw OCR text.

Uses compiled regex patterns to identify invoice fields and line items.
The approach is intentionally rule-based so it runs entirely offline
without any ML runtime dependency, while remaining easy to extend with
a lightweight NLP model (e.g. a fine-tuned LayoutLM) at the
`extract_fields` interface level.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from . import patterns as P


# ── Amount normalisation ──────────────────────────────────────────────────────

def _clean_amount(raw: str) -> Optional[float]:
    """Normalise a raw amount string to float, handling comma/period variants."""
    if not raw:
        return None
    cleaned = raw.strip().replace(" ", "")
    # Leading minus for discounts
    negative = cleaned.startswith("-")
    if negative:
        cleaned = cleaned[1:]
    # If both comma and period are present, the last one is the decimal separator
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        value = float(cleaned)
        return -value if negative else value
    except ValueError:
        return None


# ── Generic match helpers ─────────────────────────────────────────────────────

def _first_match(pattern: re.Pattern, text: str) -> Optional[str]:
    """Return the first capture group of the first match, stripped."""
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def _all_matches(pattern: re.Pattern, text: str) -> List[str]:
    """Return all non-empty first-group captures."""
    return [m.group(1).strip() for m in pattern.finditer(text) if m.group(1).strip()]


# ── Field-specific extractors ─────────────────────────────────────────────────

def _extract_invoice_number(text: str) -> Optional[str]:
    """
    Try multiple strategies to extract the invoice number:
    1. Labelled field  (Invoice No: INV-001)
    2. Inline after INVOICE keyword  (INVOICE INV-2024-0283)
    3. Bare structured reference code  (INV-2024-1856)
    4. Exclude false positives from free-text sentences.
    """
    # Strategy 1 — labelled
    m = P.INVOICE_NUMBER.search(text)
    if m:
        candidate = m.group(1).strip()
        # Reject very short or plain-word captures (e.g. "H", "in")
        if len(candidate) >= 4 and re.search(r"\d", candidate):
            return candidate

    # Strategy 2 — inline: "INVOICE <CODE>"
    m = P.INVOICE_NUMBER_INLINE.search(text)
    if m:
        candidate = m.group(1).strip()
        if re.search(r"\d", candidate):
            return candidate

    # Strategy 3 — bare structured code (INV-XXXX, REF-XXXX, …)
    m = P.INVOICE_NUMBER_BARE.search(text)
    if m:
        return m.group(1).strip()

    return None


def _extract_supplier(text: str) -> Optional[str]:
    """
    Heuristically identify the issuing company name.

    Priority:
    1. "From:" label.
    2. First line of the document, stripping trailing " INVOICE" / " SOLUTIONS INVOICE".
    3. First line that contains a recognised company-type suffix.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Strategy 1 — "From:" label (handles both line-start and mid-line two-column layouts)
    m = P.SUPPLIER_FROM.search(text)
    if m:
        # group 1: same line as "From:"; group 2: next line
        raw = (m.group(1) or m.group(2) or "").strip()
        # For two-column OCR "Bill To company   From company" on the same line,
        # attempt to split on 2+ spaces and take the rightmost segment.
        parts = re.split(r"\s{2,}", raw)
        candidate = parts[-1].strip() if len(parts) > 1 else raw
        if (
            len(candidate) >= 4
            and not re.search(r"\b(?:director|manager|street|avenue|road|blvd)\b", candidate, re.I)
            and not re.search(r"[|@]", candidate)
        ):
            return candidate

    # Strategy 2 — first line, clean up common suffixes
    if lines:
        first = lines[0]
        # Strip trailing "INVOICE" or "SOLUTIONS INVOICE" from letterhead lines
        first_clean = re.sub(r"\s+INVOICE\s*$", "", first, flags=re.I).strip()
        # Only use this if it looks like a company name (not an address or date)
        if (
            len(first_clean) >= 4
            and not re.search(r"\d{2,}", first_clean)          # no dates/street numbers
            and not re.search(r"[|@]", first_clean)             # no contact lines
        ):
            return first_clean

    # Strategy 3 — company suffix scan
    m = P.COMPANY_SUFFIX.search(text)
    if m:
        return m.group(1).strip()

    # Fallback — first non-trivial non-keyword line
    for line in lines:
        if (
            len(line) > 3
            and not any(kw in line.lower() for kw in ("invoice", "bill", "page", "date", "due"))
        ):
            return line

    return None


def _extract_amount_last(pattern: re.Pattern, text: str) -> Optional[float]:
    """
    Return the LAST match of a monetary pattern.

    Using the last match is important for invoices that show both a
    pre-discount subtotal and an after-discount subtotal — we want the
    final figure.
    """
    matches = _all_matches(pattern, text)
    for raw in reversed(matches):
        value = _clean_amount(raw)
        if value is not None and value >= 0:
            return value
    return None


def _extract_amount_first(pattern: re.Pattern, text: str) -> Optional[float]:
    """Return the first positive monetary match."""
    for raw in _all_matches(pattern, text):
        value = _clean_amount(raw)
        if value is not None and value >= 0:
            return value
    return None


def _detect_currency(text: str) -> Optional[str]:
    """Return the most frequently occurring currency symbol/code."""
    symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
    freq: Dict[str, int] = {}
    for m in P.CURRENCY.finditer(text):
        token = (m.group(1) or m.group(2) or "").upper().strip()
        if token:
            freq[token] = freq.get(token, 0) + 1
    if not freq:
        return None
    best = max(freq, key=lambda k: freq[k])
    return symbol_map.get(best, best)


# ── Line item extraction ──────────────────────────────────────────────────────

_NUM_RE  = re.compile(r"^\d+(?:[,. ]\d+)*$")
_PCT_RE  = re.compile(r"^\d+(?:[.,]\d+)?%$")

_SKIP_LINE_KEYWORDS = {
    "subtotal", "sub-total", "total", "tax", "vat", "gst", "discount",
    "grand", "balance", "amount due", "net total", "description",
    "item", "service", "qty", "quantity", "unit price", "payment",
    "invoice", "bill to", "ship to", "notes", "bank", "account",
    "sort code", "swift", "iban",
}


def _is_numeric_token(token: str) -> bool:
    """Return True if token represents a plain number (not a percentage)."""
    cleaned = token.replace(",", "").replace(" ", "")
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _extract_line_items(text: str) -> List[Dict[str, Any]]:
    """
    Extract tabular line items using a token-based approach.

    For each text line, scan trailing tokens right-to-left.  Percentage
    tokens (e.g. "20%") are skipped.  Lines with at least two trailing
    numeric tokens and a non-trivial description are treated as line items.
    """
    items: List[Dict[str, Any]] = []

    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) < 8:
            continue

        low = stripped.lower()
        if any(kw in low for kw in _SKIP_LINE_KEYWORDS):
            continue
        # Skip lines with obvious non-item markers
        if stripped.startswith(("-", "=", "_", ".", "*")):
            continue
        # Skip contact/address lines
        if re.search(r"[@|+]\d|www\.", stripped, re.I):
            continue

        tokens = stripped.split()
        if len(tokens) < 3:
            continue

        # Collect trailing numeric indices (skip percentages)
        num_indices: List[int] = []
        for i in range(len(tokens) - 1, -1, -1):
            t = tokens[i]
            if _PCT_RE.match(t):
                continue          # percentage column — skip without breaking
            if _is_numeric_token(t):
                num_indices.insert(0, i)
            else:
                break             # non-numeric ends the trailing number run

        if len(num_indices) < 2:
            continue

        num_values = [_clean_amount(tokens[i]) for i in num_indices]

        # The first trailing number may be quantity (small whole number)
        # if there are at least 3 numbers (qty, unit_price, line_total).
        qty: Optional[float] = None
        if len(num_values) >= 3:
            first_val = num_values[0]
            if (
                first_val is not None
                and first_val == int(first_val)
                and 1 <= first_val <= 9999
            ):
                qty = first_val
                unit_price = num_values[1]
                line_total  = num_values[-1]
                desc_end    = num_indices[0]
            else:
                unit_price = num_values[-2]
                line_total  = num_values[-1]
                desc_end    = num_indices[0]
        else:
            unit_price = num_values[-2]
            line_total  = num_values[-1]
            desc_end    = num_indices[0]

        description = " ".join(tokens[:desc_end]).strip()
        if len(description) < 3:
            continue

        # Reject lines where description looks like a table header
        if re.search(
            r"\b(description|item|service|hours|qty|quantity|rate|price|amount)\b",
            description, re.I
        ):
            continue

        items.append(
            {
                "description": description,
                "quantity":    qty,
                "unit_price":  unit_price,
                "line_total":  line_total,
            }
        )

    return items


# ── Public interface ──────────────────────────────────────────────────────────

def extract_fields(raw_text: str) -> Dict[str, Any]:
    """
    Parse structured invoice fields from raw OCR text.

    Returns a dict with keys matching the Invoice model fields plus a
    'line_items' list of dicts.
    """
    result: Dict[str, Any] = {
        "supplier_name":  _extract_supplier(raw_text),
        "invoice_number": _extract_invoice_number(raw_text),
        "invoice_date":   _first_match(P.INVOICE_DATE, raw_text),
        "due_date":       _first_match(P.DUE_DATE, raw_text),
        "currency":       _detect_currency(raw_text),
        # Use last match for subtotal to prefer "after discount" figures
        "subtotal":       _extract_amount_last(P.SUBTOTAL, raw_text),
        "tax_amount":     _extract_amount_first(P.TAX_AMOUNT, raw_text),
        "total_amount":   _extract_amount_first(P.TOTAL_AMOUNT, raw_text),
        "line_items":     _extract_line_items(raw_text),
    }

    # Fallback date: first date-like string in the document
    if not result["invoice_date"]:
        m = P.ANY_DATE.search(raw_text)
        if m:
            result["invoice_date"] = m.group(0).strip()

    return result
