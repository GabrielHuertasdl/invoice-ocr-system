"""
Compiled regular expressions used by the extraction layer.

All patterns are designed to be case-insensitive and tolerant of common
OCR artefacts (extra spaces, dot/comma decimal separators).
"""

import re

_F = re.IGNORECASE | re.MULTILINE

# ── Amount core (handles 4+ digit numbers without thousand separators) ────────
# Examples matched: 6500.00  6,500.00  6 500.00  135  1300.00
_AMOUNT = r"\d+(?:[,\s]\d{3})*(?:[.,]\d{1,4})?"

# ── Invoice number ────────────────────────────────────────────────────────────
# Labelled variants: "Invoice No:", "Invoice Number:", "Inv #:", etc.
# NOTE: "number" must come before "num" in the alternation so that the pattern
# does not match only the prefix "num" inside the word "number" and then
# capture the trailing "ber" as the invoice identifier.
INVOICE_NUMBER = re.compile(
    r"(?:invoice\s*(?:number|num|no|#)|inv\.?\s*(?:number|num|no|#))"
    r"[:\s#]*([A-Z0-9][A-Z0-9\-/]+)",
    _F,
)

# Fallback 1: "INVOICE <code>" on the same line (e.g. "INVOICE INV-2024-0283")
INVOICE_NUMBER_INLINE = re.compile(
    r"\bINVOICE\s+([A-Z0-9][A-Z0-9\-/]{3,})\b",
    _F,
)

# Fallback 2: bare structured reference code anywhere on a line
# Matches patterns like INV-2024-1856, REF-001, BILL-2024/03
INVOICE_NUMBER_BARE = re.compile(
    r"\b((?:INV|REF|BILL|REC|SI)[-/]\d{2,}[-/\w]*)\b",
    _F,
)

# ── Dates ─────────────────────────────────────────────────────────────────────
_DATE_CORE = (
    r"(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}"
    r"|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}"
    r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4})"
)
INVOICE_DATE = re.compile(
    r"(?:invoice\s*date|date\s*of\s*invoice|date\s*issued|^date)[:\s]*(" + _DATE_CORE + r")",
    _F,
)
DUE_DATE = re.compile(
    r"(?:due\s*date|payment\s*due|pay\s*by|due)[:\s]*(" + _DATE_CORE + r")",
    _F,
)
ANY_DATE = re.compile(_DATE_CORE, _F)

# ── Currency ──────────────────────────────────────────────────────────────────
CURRENCY = re.compile(r"\b(USD|EUR|GBP|CAD|AUD|CHF|JPY|CNY)\b|(\$|€|£|¥)", _F)

# ── Monetary amounts ──────────────────────────────────────────────────────────
# Labels may include parenthetical qualifiers, e.g. "Tax (20%):" or
# "Subtotal (exc. VAT):" — the (?:\([^)]*\))? group handles these.
_LABEL_SUFFIX = r"\s*(?:\([^)]*\))?\s*[:\s]*[£$€]?\s*"

SUBTOTAL = re.compile(
    r"(?:subtotal\s*(?:after\s+\w+)?|sub\s*total|net\s*(?:amount|total))"
    + _LABEL_SUFFIX
    + r"(-?" + _AMOUNT + r")",
    _F,
)
TAX_AMOUNT = re.compile(
    r"(?:tax|vat|gst|hst|sales\s*tax)" + _LABEL_SUFFIX + r"(-?" + _AMOUNT + r")",
    _F,
)
TOTAL_AMOUNT = re.compile(
    # (?<!sub) prevents matching "total" inside "subtotal".
    # re.IGNORECASE makes the lookbehind case-insensitive in Python 3.
    r"(?:"
    r"(?<!sub)total\s*(?:amount\s*)?(?:due|payable|owed)"  # TOTAL DUE / AMOUNT DUE
    r"|(?<!sub)total\s+amount"                              # TOTAL AMOUNT (no qualifier)
    r"|grand\s*total"                                       # GRAND TOTAL
    r"|balance\s*due"                                       # BALANCE DUE
    r"|amount\s*due"                                        # AMOUNT DUE
    r"|(?:^|\n)\s*(?<!sub)total\s*"                        # TOTAL: alone at line start
    r")"
    + _LABEL_SUFFIX
    + r"(" + _AMOUNT + r")",
    _F | re.MULTILINE,
)

# ── Supplier heuristics ───────────────────────────────────────────────────────
# Lines that contain a recognised company-type suffix
COMPANY_SUFFIX = re.compile(
    r"^(.{2,80}?\b(?:Inc\.?|Ltd\.?|LLC|L\.L\.C\.|Corp\.?|GmbH|S\.A\.|PLC|BV|NV|Pty|Group|Solutions|Systems|Services|Consulting))\b",
    _F | re.MULTILINE,
)
# "From:" label: at line start OR mid-line (two-column "Bill To: | From:" layout)
# Group 1 captures text on the same line after "From:"; group 2 captures the next line.
SUPPLIER_FROM = re.compile(
    r"From:\s*([^\n]{3,80})|From:\s*\n\s*([^\n]{3,80})",
    _F,
)
