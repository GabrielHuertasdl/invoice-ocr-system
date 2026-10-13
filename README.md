# Invoice Processing System

A full-stack invoice processing system that uses OCR (Tesseract) and pattern-based extraction to automatically parse invoice data from PDF and image files.

**Stack**: FastAPI · React 18 + Vite · SQLite · Tesseract OCR · OpenCV

---

## System Requirements

Before running, install the following system packages:

```bash
sudo apt install tesseract-ocr poppler-utils
```

---

## Quick Start

```bash
./start.sh        # starts backend + frontend
./start.sh stop   # stops both
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs

---

## Manual Setup

### Backend

```bash
cd invoice_system/backend
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # edit if needed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd invoice_system/frontend
npm install
npm run dev
```

The Vite dev server proxies all `/api/*` requests to the backend automatically.

---

## Project Structure

```
FYP_FinalVersion/
├── start.sh                        # One-command startup script
├── sample_invoices/                # Sample PDFs for testing
└── invoice_system/
    ├── backend/
    │   ├── app/
    │   │   ├── main.py             # FastAPI entry point
    │   │   ├── api/                # Route handlers
    │   │   ├── models/             # SQLAlchemy models
    │   │   └── services/           # Pipeline: ingestion → OCR → extraction → storage
    │   ├── scripts/                # Batch processing & evaluation scripts
    │   ├── ground_truth_text/      # Ground truth OCR text (evaluation)
    │   ├── gt_json/                # Ground truth extraction JSON (evaluation)
    │   ├── requirements.txt
    │   └── .env.example
    ├── frontend/
    │   ├── src/
    │   │   ├── pages/              # InvoiceList, InvoiceDetail, UploadPage
    │   │   ├── components/         # Reusable UI components
    │   │   └── api/                # Backend API client
    │   └── package.json
    └── docs/                       # Architecture, API spec, usage guide
```

---

## Utility Scripts

Run all commands from `invoice_system/backend/` with the venv active.

```bash
# Batch process a folder of invoices
python scripts/run_pipeline_on_folder.py --input ./sample_invoices --csv ./out/report.csv

# Evaluate OCR accuracy
python scripts/evaluate_ocr_metrics.py \
    --ocr-dir ./ocr_outputs --gt-dir ./ground_truth_text --output ./out/ocr_metrics.tsv

# Evaluate extraction field accuracy
python scripts/evaluate_extraction_metrics.py \
    --pred-dir ./pred_json --gt-dir ./gt_json --tol 0.01 --output ./out/extraction_metrics.tsv
```

---

## AI Layer (Search + QA)

Two new endpoints sit under `/api/ai/` and require no additional infrastructure.

### Search invoices by natural language

```bash
# All invoices from "Acme Corp" (fuzzy match on supplier_name)
curl "http://localhost:8000/api/ai/search?q=facturas+de+Acme+Corp"

# Works in English too
curl "http://localhost:8000/api/ai/search?q=Acme+Corp+invoices"
```

Response: array of `InvoiceSummary` objects (same shape as `GET /api/invoices`).

### Ask a question about a specific invoice

```bash
# Ask a free-text question about invoice id=3
curl -X POST http://localhost:8000/api/ai/qa \
  -H "Content-Type: application/json" \
  -d '{"invoice_id": 3, "question": "What is the total amount and which currency?"}'

# Another example
curl -X POST http://localhost:8000/api/ai/qa \
  -H "Content-Type: application/json" \
  -d '{"invoice_id": 3, "question": "List all line items and their prices."}'
```

Response:
```json
{
  "invoice_id": 3,
  "question": "What is the total amount and which currency?",
  "answer": "The total amount is 1,920.00 GBP (British Pounds)."
}
```

### Configuring the LLM

Edit `invoice_system/backend/.env`:

```ini
LLM_PROVIDER=claude   # or "openai"
LLM_API_KEY=sk-ant-...
```

Install the matching SDK:

```bash
pip install anthropic   # for LLM_PROVIDER=claude
pip install openai      # for LLM_PROVIDER=openai
```

The `/api/ai/search` endpoint works **without** an LLM key (pure fuzzy matching).
The `/api/ai/qa` endpoint requires a valid key and will return HTTP 503 if not set.

---

## Synthetic Invoice Data

Generate 200+ realistic but fictional invoices for testing:

```bash
cd invoice_system/backend

# Generate JSON files only (no DB changes)
python scripts/generar_facturas_sinteticas.py

# Generate and insert directly into the database
python scripts/generar_facturas_sinteticas.py --insert-db

# Custom count and output directory
python scripts/generar_facturas_sinteticas.py --count 500 --out-dir /tmp/test_invoices
```

Generated files are saved to `invoice_system/backend/data/facturas_sinteticas/json/`
as `factura_0001.json … factura_NNNN.json`.

Each file mirrors the full Invoice schema:

```json
{
  "filename": "factura_0001.pdf",
  "status": "completed",
  "supplier_name": "Acme Corp Ltd",
  "invoice_number": "INV-2024-0001",
  "invoice_date": "15/03/2024",
  "due_date": "14/04/2024",
  "subtotal": 1600.00,
  "tax_amount": 320.00,
  "total_amount": 1920.00,
  "currency": "GBP",
  "line_items": [...]
}
```

To ingest the JSON-only files through the normal upload pipeline (OCR + extraction),
you would need real PDF versions. Use `--insert-db` to bypass the pipeline and
insert the pre-extracted data directly — useful for populating a dev/test database.

---

## Environment Variables

Copy `.env.example` to `.env` inside `invoice_system/backend/` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./invoice_system.db` | Database connection string |
| `UPLOAD_DIR` | `./uploads` | Directory for uploaded files |
| `TESSERACT_CMD` | `tesseract` | Path to Tesseract binary |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LLM_PROVIDER` | `claude` | LLM provider: `claude` or `openai` |
| `LLM_API_KEY` | *(empty)* | API key for the chosen LLM provider |
