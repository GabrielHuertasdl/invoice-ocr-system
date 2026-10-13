"""
QA service.

Fetches a single invoice from the database, builds a rich text context
(structured fields + raw OCR text), and delegates the question to the
LLM wrapper.
"""

import logging
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.services.storage.crud import get_invoice
from app.services.ai.llm_wrapper import answer_question_about_document

logger = logging.getLogger(__name__)

# Maximum characters of raw OCR text to include in the LLM context.
# Keeps prompt size within typical model limits while preserving most detail.
_RAW_TEXT_LIMIT = 4000


def build_document_context(invoice: Invoice) -> str:
    """
    Assemble a structured text representation of an invoice for LLM context.

    Combines extracted header fields, line items, and raw OCR text so the
    model has both the clean parsed data and the full original content.
    """
    lines = [
        "=== INVOICE METADATA ===",
        f"Supplier:       {invoice.supplier_name or 'Unknown'}",
        f"Invoice Number: {invoice.invoice_number or 'Unknown'}",
        f"Invoice Date:   {invoice.invoice_date or 'Unknown'}",
        f"Due Date:       {invoice.due_date or 'Unknown'}",
        f"Currency:       {invoice.currency or 'Unknown'}",
        f"Subtotal:       {invoice.subtotal}",
        f"Tax Amount:     {invoice.tax_amount}",
        f"Total Amount:   {invoice.total_amount}",
    ]

    if invoice.line_items:
        lines.append("\n=== LINE ITEMS ===")
        for item in invoice.line_items:
            lines.append(
                f"  - {item.description or 'Item'}: "
                f"qty={item.quantity}, unit_price={item.unit_price}, "
                f"line_total={item.line_total}"
            )

    if invoice.raw_text:
        lines.append("\n=== RAW OCR TEXT ===")
        lines.append(invoice.raw_text[:_RAW_TEXT_LIMIT])

    return "\n".join(lines)


def answer_invoice_question(db: Session, invoice_id: int, question: str) -> str:
    """
    Fetch invoice *invoice_id*, build its context, and ask the LLM *question*.

    Args:
        db:         Active SQLAlchemy session.
        invoice_id: Primary key of the target invoice.
        question:   Free-text question from the user.

    Returns:
        The LLM's answer as a plain string.

    Raises:
        ValueError:   Invoice not found.
        RuntimeError: LLM call failed (propagated from llm_wrapper).
    """
    invoice = get_invoice(db, invoice_id)
    if not invoice:
        raise ValueError(f"Invoice with id={invoice_id} not found.")

    logger.info("QA request: invoice_id=%d, question=%r", invoice_id, question[:80])
    document_text = build_document_context(invoice)
    return answer_question_about_document(document_text, question)
