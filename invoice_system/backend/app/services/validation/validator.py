"""
Business-rule validation for extracted invoice data.

Checks are intentionally lenient (warnings, not hard errors) so that
partially-extracted invoices are still stored and surfaced to the user
for manual correction.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import re
from datetime import datetime


_DATE_FORMATS = [
    "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d",
    "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d",
    "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
    "%d %b %y", "%b %d %Y",
]


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def validate_invoice(data: Dict[str, Any]) -> List[str]:
    """
    Run validation checks on extracted invoice data.

    Returns a list of human-readable warning strings.  An empty list
    indicates no issues were detected.
    """
    warnings: List[str] = []

    subtotal = data.get("subtotal")
    tax = data.get("tax_amount")
    total = data.get("total_amount")
    line_items = data.get("line_items", [])

    # Check 1: Total consistency (subtotal + tax ~ total)
    if subtotal is not None and tax is not None and total is not None:
        expected = round(subtotal + tax, 2)
        if abs(expected - total) > 0.10:
            warnings.append(
                f"Total mismatch: subtotal ({subtotal}) + tax ({tax}) = {expected}, "
                f"but extracted total is {total}."
            )

    # Check 2: Line items sum vs subtotal
    if line_items and subtotal is not None:
        li_sum = sum(
            li.get("line_total") or 0
            for li in line_items
            if li.get("line_total") is not None
        )
        if li_sum > 0 and abs(li_sum - subtotal) > 0.50:
            warnings.append(
                f"Line items sum ({li_sum:.2f}) differs from subtotal ({subtotal:.2f})."
            )

    # Check 3: Date logic
    inv_dt = _parse_date(data.get("invoice_date"))
    due_dt = _parse_date(data.get("due_date"))

    if inv_dt and inv_dt.year < 2000:
        warnings.append(f"Invoice date '{data.get('invoice_date')}' appears too old.")

    if inv_dt and due_dt and due_dt < inv_dt:
        warnings.append(
            f"Due date '{data.get('due_date')}' is earlier than invoice date "
            f"'{data.get('invoice_date')}'."
        )

    # Check 4: Required fields missing
    for field in ("invoice_number", "invoice_date", "total_amount", "supplier_name"):
        if not data.get(field):
            warnings.append(f"Required field '{field}' could not be extracted.")

    return warnings
