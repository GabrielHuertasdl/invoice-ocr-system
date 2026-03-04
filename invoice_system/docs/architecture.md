# System Architecture

## Overview

The Invoice Processing System is a fully local, self-contained application composed of three independent layers:

1. **Backend** — Python/FastAPI service that owns the processing pipeline and the REST API.
2. **Frontend** — React single-page application that consumes the REST API.
3. **Database** — SQLite (default) or PostgreSQL via SQLAlchemy.

```
Browser
  |
  | HTTP (REST)
  v
FastAPI (port 8000)
  |
  +-- Ingestion      (file type validation, disk persistence)
  +-- Preprocessing  (PDF -> images, OpenCV enhancement)
  +-- OCR            (Tesseract / pytesseract)
  +-- Extraction     (regex rules, pattern matching)
  +-- Validation     (business rules: totals, dates)
  +-- Storage        (SQLAlchemy ORM -> SQLite / PostgreSQL)
```

---

## Backend

### Entry point: `app/main.py`

- Initialises the database schema on startup via SQLAlchemy's `create_all`.
- Registers CORS middleware (allows the Vite dev server on port 5173).
- Mounts two routers: `health` and `invoices`.

### Pipeline stages

| Stage | Module | Responsibility |
|---|---|---|
| Ingestion | `services/ingestion/file_handler.py` | Validates MIME-safe extension, copies file to `uploads/` with a UUID name. |
| Preprocessing | `services/preprocessing/image_processor.py` | Converts PDFs to 300 DPI PIL Images via `pdf2image`; applies grayscale, fast NL-means denoising, and Otsu threshold using OpenCV. |
| OCR | `services/ocr/tesseract_ocr.py` | Runs Tesseract with `--oem 3 --psm 6` on each page image; joins pages with a separator string. |
| Extraction | `services/extraction/extractor.py` | Applies compiled regular expressions (defined in `patterns.py`) to identify header fields and line items. |
| Validation | `services/validation/validator.py` | Checks total consistency (`subtotal + tax ~ total`), line-item sum, date plausibility, and required-field presence. |
| Storage | `services/storage/` | Persists Invoice and LineItem rows; exposes thin CRUD helpers used by both the API and the batch script. |

### Pipeline orchestration: `services/pipeline.py`

`run_pipeline(db, invoice)` is the single entry point used by both the REST API and the batch script.  It updates the `status` field at each stage so partial results survive a crash.

---

## Frontend

Built with React 18 and Vite.  All API calls go through a single client module (`src/api/invoiceApi.js`).  The Vite dev server proxies `/api/*` to the backend so no CORS issues arise in development.

| Page | Route | Description |
|---|---|---|
| Invoice List | `/` | Paginated table of invoices with sortable columns. |
| Upload | `/upload` | Drag-and-drop or file-picker upload; shows per-file processing results. |
| Invoice Detail | `/invoices/:id` | Full view with editable header fields, line-items table, and collapsible raw OCR text. |

---

## Database

Two ORM models are defined in `app/models/invoice.py`:

- **Invoice** — one row per uploaded file; holds all extracted header fields, raw text, validation notes, and processing status.
- **LineItem** — child rows linked to an Invoice via a cascade foreign key.

The default connection string points to a local SQLite file (`invoice_system.db`), which requires no installation.  Switching to PostgreSQL requires only changing `DATABASE_URL` in `.env`.

---

## Scalability Notes

The current design is intentionally single-process and local.  To scale:

- **Async processing**: Replace the synchronous pipeline call inside the upload endpoint with a task queue (Celery + Redis or ARQ).  The endpoint would return immediately with `status=pending`, and a worker would update the row when done.
- **Storage**: Replace SQLite with PostgreSQL for concurrent write access.
- **OCR**: Tesseract is single-threaded.  For high throughput, run multiple worker processes or switch to a cloud OCR API.
- **Extraction**: The regex engine can be augmented or replaced with a fine-tuned LayoutLM or Donut model (see `system_design.md`).
- **Horizontal scaling**: The API is stateless (files on disk, state in DB), so it can be deployed behind a load balancer once the shared database is migrated to a server instance.
