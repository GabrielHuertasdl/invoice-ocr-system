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

## Environment Variables

Copy `.env.example` to `.env` inside `invoice_system/backend/` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./invoice_system.db` | Database connection string |
| `UPLOAD_DIR` | `./uploads` | Directory for uploaded files |
| `TESSERACT_CMD` | `tesseract` | Path to Tesseract binary |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
