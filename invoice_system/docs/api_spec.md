# API Specification

Base URL: `http://localhost:8000`

All endpoints return JSON.  Error responses follow the FastAPI default format:

```json
{ "detail": "Human-readable error message" }
```

---

## GET /health

Health check — verifies the service is running and the database is reachable.

**Response 200**
```json
{
  "status": "ok",
  "database": true
}
```

`status` is `"degraded"` if the database cannot be reached.

---

## POST /api/invoices/upload

Upload one or more invoice files (PDF, PNG, JPEG).  The pipeline runs synchronously and returns results for every file.

**Request** — `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `files` | file[] | One or more invoice files. |

**Response 200**
```json
{
  "results": [
    {
      "filename": "invoice_001.pdf",
      "invoice_id": 3,
      "status": "completed",
      "message": null
    },
    {
      "filename": "bad.docx",
      "invoice_id": null,
      "status": "failed",
      "message": "Unsupported file type '.docx'. Allowed: {'.pdf', '.png', '.jpg', '.jpeg'}"
    }
  ]
}
```

`status` values: `pending` | `processing` | `completed` | `failed`

---

## GET /api/invoices

Return a paginated list of invoices sorted by creation date descending.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `skip` | integer | 0 | Number of records to skip. |
| `limit` | integer | 100 | Max records to return (max 500). |

**Response 200** — array of InvoiceSummary objects
```json
[
  {
    "id": 3,
    "filename": "invoice_001.pdf",
    "supplier_name": "Acme Corp Ltd",
    "invoice_number": "INV-2024-0042",
    "invoice_date": "15/03/2024",
    "due_date": "15/04/2024",
    "subtotal": 1000.00,
    "tax_amount": 200.00,
    "total_amount": 1200.00,
    "currency": "GBP",
    "status": "completed",
    "created_at": "2024-03-15T10:23:44.123456"
  }
]
```

---

## GET /api/invoices/{id}

Return full structured data for a single invoice.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Invoice primary key. |

**Response 200** — InvoiceDetail object
```json
{
  "id": 3,
  "filename": "invoice_001.pdf",
  "status": "completed",
  "supplier_name": "Acme Corp Ltd",
  "invoice_number": "INV-2024-0042",
  "invoice_date": "15/03/2024",
  "due_date": "15/04/2024",
  "subtotal": 1000.00,
  "tax_amount": 200.00,
  "total_amount": 1200.00,
  "currency": "GBP",
  "raw_text": "Acme Corp Ltd\n...",
  "validation_notes": null,
  "error_message": null,
  "line_items": [
    {
      "id": 7,
      "invoice_id": 3,
      "description": "Web Development Services",
      "quantity": 10.0,
      "unit_price": 100.00,
      "line_total": 1000.00
    }
  ],
  "created_at": "2024-03-15T10:23:44.123456",
  "updated_at": "2024-03-15T10:23:44.987654"
}
```

**Response 404**
```json
{ "detail": "Invoice not found." }
```

---

## PUT /api/invoices/{id}

Update invoice header fields and/or replace the full set of line items.
Only fields present in the request body are modified.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Invoice primary key. |

**Request body** (all fields optional)
```json
{
  "supplier_name": "Acme Corp Ltd",
  "invoice_number": "INV-2024-0042",
  "invoice_date": "15/03/2024",
  "due_date": "15/04/2024",
  "subtotal": 1000.00,
  "tax_amount": 200.00,
  "total_amount": 1200.00,
  "currency": "GBP",
  "validation_notes": "Manually verified",
  "line_items": [
    {
      "description": "Web Development Services",
      "quantity": 10.0,
      "unit_price": 100.00,
      "line_total": 1000.00
    }
  ]
}
```

When `line_items` is provided, all existing line items for that invoice are replaced.

**Response 200** — Updated InvoiceDetail (same schema as GET /api/invoices/{id})

**Response 404**
```json
{ "detail": "Invoice not found." }
```

---

## Field Glossary

| Field | Description |
|---|---|
| `supplier_name` | Name of the issuing company |
| `invoice_number` | Unique invoice reference string |
| `invoice_date` | Date the invoice was issued (string as extracted) |
| `due_date` | Payment due date (string as extracted) |
| `subtotal` | Pre-tax amount |
| `tax_amount` | Tax / VAT / GST amount |
| `total_amount` | Grand total |
| `currency` | ISO 4217 code or symbol (USD, EUR, GBP, ...) |
| `line_items` | Array of individual invoice line entries |
