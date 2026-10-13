"""CRUD helpers for Invoice and LineItem models."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.invoice import Invoice, LineItem, ProcessingStatus
from app.schemas import InvoiceUpdate


def create_invoice(db: Session, filename: str, file_path: str) -> Invoice:
    """Insert a new invoice record with pending status."""
    invoice = Invoice(
        filename=filename,
        file_path=file_path,
        status=ProcessingStatus.pending,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice(db: Session, invoice_id: int) -> Optional[Invoice]:
    """Retrieve a single invoice by primary key."""
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def list_invoices(db: Session, skip: int = 0, limit: int = 100) -> List[Invoice]:
    """Return a paginated list of invoices ordered by creation date desc."""
    return (
        db.query(Invoice)
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_invoice(db: Session, invoice: Invoice, data: dict) -> Invoice:
    """Apply a dictionary of field updates to an existing invoice."""
    for key, value in data.items():
        if hasattr(invoice, key):
            setattr(invoice, key, value)
    db.commit()
    db.refresh(invoice)
    return invoice


def list_completed_invoices_with_supplier(db: Session) -> List[Invoice]:
    """Return all completed invoices that have a non-null supplier_name."""
    return (
        db.query(Invoice)
        .filter(
            Invoice.status == ProcessingStatus.completed,
            Invoice.supplier_name.isnot(None),
        )
        .all()
    )


def save_line_items(db: Session, invoice: Invoice, items: List[dict]) -> None:
    """Replace all line items for an invoice with the provided list."""
    db.query(LineItem).filter(LineItem.invoice_id == invoice.id).delete()
    for item in items:
        li = LineItem(invoice_id=invoice.id, **item)
        db.add(li)
    db.commit()
