"""Pydantic schemas for request/response validation."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.invoice import ProcessingStatus


# ── Line Items ────────────────────────────────────────────────────────────────

class LineItemBase(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None


class LineItemCreate(LineItemBase):
    pass


class LineItemOut(LineItemBase):
    id: int
    invoice_id: int

    class Config:
        from_attributes = True


# ── Invoices ──────────────────────────────────────────────────────────────────

class InvoiceBase(BaseModel):
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None


class InvoiceUpdate(InvoiceBase):
    """Schema for PUT /api/invoices/{id}."""
    line_items: Optional[List[LineItemCreate]] = None
    validation_notes: Optional[str] = None


class InvoiceSummary(InvoiceBase):
    """Lightweight schema used in list responses."""
    id: int
    filename: str
    status: ProcessingStatus
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceDetail(InvoiceBase):
    """Full schema including raw text, notes, and line items."""
    id: int
    filename: str
    status: ProcessingStatus
    raw_text: Optional[str] = None
    validation_notes: Optional[str] = None
    error_message: Optional[str] = None
    line_items: List[LineItemOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Upload response ───────────────────────────────────────────────────────────

class UploadResult(BaseModel):
    filename: str
    invoice_id: Optional[int] = None
    status: ProcessingStatus
    message: Optional[str] = None


class UploadResponse(BaseModel):
    results: List[UploadResult]
