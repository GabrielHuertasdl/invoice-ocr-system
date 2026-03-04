"""
Invoice REST API endpoints.

POST   /api/invoices/upload   Upload and process one or more invoice files.
GET    /api/invoices           List invoices (paginated).
GET    /api/invoices/{id}      Full invoice detail.
PUT    /api/invoices/{id}      Update invoice fields and/or line items.
"""

from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas import InvoiceDetail, InvoiceSummary, InvoiceUpdate, UploadResponse, UploadResult
from app.models.invoice import ProcessingStatus
from app.services.storage import get_db, create_invoice, get_invoice, list_invoices, update_invoice, save_line_items
from app.services.ingestion import save_upload, validate_file_type
from app.services.pipeline import run_pipeline

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


@router.post("/upload", response_model=UploadResponse, status_code=200)
async def upload_invoices(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Accept one or more PDF/image files, run the full processing pipeline
    on each, and return the resulting invoice IDs and statuses.
    """
    results: List[UploadResult] = []

    for upload in files:
        try:
            validate_file_type(upload.filename)
            saved_path = save_upload(upload, settings.upload_dir)
            invoice = create_invoice(db, filename=upload.filename, file_path=str(saved_path))
            invoice = run_pipeline(db, invoice)
            results.append(
                UploadResult(
                    filename=upload.filename,
                    invoice_id=invoice.id,
                    status=invoice.status,
                    message=invoice.error_message,
                )
            )
        except HTTPException as exc:
            results.append(
                UploadResult(
                    filename=upload.filename,
                    status=ProcessingStatus.failed,
                    message=exc.detail,
                )
            )
        except Exception as exc:
            results.append(
                UploadResult(
                    filename=upload.filename,
                    status=ProcessingStatus.failed,
                    message=str(exc),
                )
            )

    return UploadResponse(results=results)


@router.get("", response_model=List[InvoiceSummary])
def get_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return a paginated list of invoices with summary fields."""
    return list_invoices(db, skip=skip, limit=limit)


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice_detail(invoice_id: int, db: Session = Depends(get_db)):
    """Return full structured data for a single invoice."""
    invoice = get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceDetail)
def update_invoice_endpoint(
    invoice_id: int,
    payload: InvoiceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update invoice header fields and/or replace all line items.

    Only fields explicitly provided in the request body are modified.
    """
    invoice = get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    update_data = payload.model_dump(exclude_unset=True, exclude={"line_items"})
    if update_data:
        update_invoice(db, invoice, update_data)

    if payload.line_items is not None:
        items = [item.model_dump() for item in payload.line_items]
        save_line_items(db, invoice, items)

    db.refresh(invoice)
    return invoice
