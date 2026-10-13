"""
Document search service.

Extracts a supplier name from a free-text query and returns matching
invoices using fuzzy string matching (rapidfuzz, already a project dependency).

Design
------
1. `extract_supplier_from_query`  – lightweight regex heuristic; no LLM needed
   for common patterns like "facturas de Acme Corp" or "pdf de TechSupplies".
2. `find_invoices_by_supplier`    – fetches all completed invoices from the DB
   and scores each supplier_name against the extracted name with rapidfuzz's
   token_set_ratio (handles word-order differences and partial names well).
3. `search_documents`             – public entry point combining steps 1 + 2.
"""

import re
import logging
from typing import List

from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.services.storage.crud import list_completed_invoices_with_supplier

logger = logging.getLogger(__name__)

# Minimum fuzzy score (0–100) to consider a name a match.
FUZZY_THRESHOLD = 60


def extract_supplier_from_query(query: str) -> str:
    """
    Extract the supplier / person name from a natural-language query.

    Handles Spanish and English patterns, e.g.:
      "facturas de Acme Corp"         → "Acme Corp"
      "pdfs de TechSupplies Inc"      → "TechSupplies Inc"
      "documentos de Design Studio"   → "Design Studio"
      "Acme Corp invoices"            → "Acme Corp"
      "show invoices from GlobalTech" → "GlobalTech"

    Falls back to the raw query when no pattern matches.
    """
    query = query.strip()

    patterns = [
        # "facturas/pdfs/documentos/invoices de <name>"
        r"(?:facturas?|pdfs?|documentos?|invoices?|documents?)\s+de\s+(.+)",
        # "de/of/from <name>"  (optionally followed by document keyword)
        r"(?:^|\s)(?:de|of|from)\s+(.+?)(?:\s+(?:facturas?|pdfs?|documentos?|invoices?))?$",
        # "<name> facturas/invoices/…"
        r"^(.+?)\s+(?:facturas?|pdfs?|documentos?|invoices?|documents?)",
    ]
    for pattern in patterns:
        m = re.search(pattern, query, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return query


def find_invoices_by_supplier(db: Session, supplier_query: str) -> List[Invoice]:
    """
    Return all completed invoices whose supplier_name fuzzy-matches *supplier_query*.

    Uses token_set_ratio so that partial names and word-order differences still
    produce a hit (e.g. "Acme" matches "Acme Corp Ltd").
    """
    candidates = list_completed_invoices_with_supplier(db)
    if not candidates:
        return []

    # Map supplier name → list of invoices (multiple invoices per supplier)
    name_to_invoices: dict[str, List[Invoice]] = {}
    for inv in candidates:
        name_to_invoices.setdefault(inv.supplier_name, []).append(inv)

    unique_names = list(name_to_invoices.keys())

    matches = process.extract(
        supplier_query,
        unique_names,
        scorer=fuzz.token_set_ratio,
        limit=len(unique_names),
        score_cutoff=FUZZY_THRESHOLD,
    )

    logger.info(
        "Fuzzy search %r → %d match(es): %s",
        supplier_query,
        len(matches),
        [(name, score) for name, score, _ in matches],
    )

    result: List[Invoice] = []
    for name, _score, _idx in matches:
        result.extend(name_to_invoices[name])

    return result


def search_documents(db: Session, query: str) -> List[Invoice]:
    """
    High-level entry point: parse free-text query → extract supplier → fuzzy search.

    Args:
        db:    Active SQLAlchemy session.
        query: Natural-language query, e.g. "facturas de Acme Corp".

    Returns:
        List of matching Invoice ORM objects (may be empty).
    """
    supplier = extract_supplier_from_query(query)
    logger.info("search_documents: query=%r → supplier=%r", query, supplier)
    return find_invoices_by_supplier(db, supplier)
