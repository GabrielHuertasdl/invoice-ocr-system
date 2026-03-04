"""
End-to-end invoice processing pipeline.

Orchestrates: preprocessing -> OCR -> extraction -> validation -> storage.
Designed to be called from both the REST API and the batch script.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models.invoice import Invoice, ProcessingStatus
from app.services.preprocessing import prepare_images
from app.services.ocr import run_ocr
from app.services.extraction import extract_fields
from app.services.validation import validate_invoice
from app.services.storage import crud

logger = logging.getLogger(__name__)


def run_pipeline(db: Session, invoice: Invoice) -> Invoice:
    """
    Execute the full processing pipeline for a single Invoice record.

    Updates the invoice row in the database at each stage so that
    partial results are visible even if a later stage fails.

    Args:
        db:      An active SQLAlchemy session.
        invoice: An Invoice ORM object already persisted (status=pending).

    Returns:
        The updated Invoice object.
    """
    invoice_id = invoice.id
    file_path = Path(invoice.file_path)

    try:
        # 1. Mark as processing
        crud.update_invoice(db, invoice, {"status": ProcessingStatus.processing})

        # 2. Preprocessing
        logger.info("Invoice %d: preprocessing '%s'", invoice_id, file_path.name)
        images = prepare_images(file_path)

        # 3. OCR
        logger.info("Invoice %d: running OCR", invoice_id)
        raw_text = run_ocr(images)

        # 4. Extraction
        logger.info("Invoice %d: extracting fields", invoice_id)
        extracted = extract_fields(raw_text)
        line_items = extracted.pop("line_items", [])

        # 5. Validation
        logger.info("Invoice %d: validating", invoice_id)
        warnings = validate_invoice({**extracted, "line_items": line_items})
        notes = "; ".join(warnings) if warnings else None

        # 6. Persist results
        crud.update_invoice(
            db,
            invoice,
            {
                "raw_text": raw_text,
                "validation_notes": notes,
                "status": ProcessingStatus.completed,
                **extracted,
            },
        )
        crud.save_line_items(db, invoice, line_items)

        logger.info(
            "Invoice %d: completed (warnings: %d)", invoice_id, len(warnings)
        )

    except Exception as exc:
        logger.exception("Invoice %d: pipeline failed", invoice_id)
        crud.update_invoice(
            db,
            invoice,
            {
                "status": ProcessingStatus.failed,
                "error_message": str(exc),
            },
        )

    db.refresh(invoice)
    return invoice
