# Usage Guide

## Prerequisites

| Dependency | Version | Notes |
|---|---|---|
| Python | 3.10+ | |
| pip | latest | |
| Tesseract OCR | 4.0+ | Must be on `PATH` |
| poppler-utils | latest | Required by `pdf2image` for PDF support |
| Node.js | 18+ | For the frontend |
| npm | 9+ | |

### Installing Tesseract

**Ubuntu / Debian**
```
sudo apt install tesseract-ocr
```

**macOS (Homebrew)**
```
brew install tesseract
```

**Windows**
Download the installer from https://github.com/UB-Mannheim/tesseract/wiki and add the install directory to `PATH`.

### Installing poppler

**Ubuntu / Debian**
```
sudo apt install poppler-utils
```

**macOS**
```
brew install poppler
```

**Windows**
Download a poppler binary release and add `bin/` to `PATH`.

---

## Backend Setup

### 1. Create and activate a virtual environment

The venv lives at `invoice_system/venv/`, one level above `backend/`.

```bash
cd invoice_system
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env if needed (e.g. DATABASE_URL, UPLOAD_DIR, TESSERACT_CMD)
```

### 4. Launch the backend server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at http://localhost:8000.
Interactive Swagger docs: http://localhost:8000/docs
Health check: http://localhost:8000/health

The database file (`invoice_system.db`) and uploads directory are created automatically on first run.

---

## Frontend Setup

### 1. Install Node dependencies

```bash
cd invoice_system/frontend
npm install
```

### 2. Start the development server

```bash
npm run dev
```

The UI is available at http://localhost:5173.

The Vite dev server proxies all `/api/*` requests to the backend at http://127.0.0.1:8000, so both must be running simultaneously.

### 3. Production build (optional)

```bash
npm run build
# Serve the dist/ folder with any static file server
```

---

## Running the Batch and Evaluation Scripts

All scripts must be run from the `invoice_system/backend/` directory with the virtual environment activated (from `invoice_system/`).

### Step 0: Generate sample data (first time only)

```bash
# from invoice_system/
source venv/bin/activate
cd backend
python scripts/create_sample_data.py
```

This creates `sample_invoices/`, `ocr_outputs/`, `ground_truth_text/`, `pred_json/`, and `gt_json/` with three example invoices ready to use.

### run_pipeline_on_folder.py

Processes every supported file in a folder, stores results in the database, and optionally writes a CSV report.

```bash
# Basic usage (results stored in DB only)
python scripts/run_pipeline_on_folder.py --input /path/to/invoices

# With CSV export
python scripts/run_pipeline_on_folder.py \
    --input  /path/to/invoices \
    --csv    ./results/batch_report.csv
```

Output includes per-file status and timing, plus a summary line showing total processing time and average time per file.

---

### evaluate_ocr_metrics.py

Compares OCR output text files against ground-truth text files.

**Prepare inputs:**
- `--ocr-dir`: directory of `.txt` files produced by the OCR engine (one per invoice, stem must match the GT file).
- `--gt-dir`: directory of hand-corrected `.txt` ground-truth files.

```bash
python scripts/evaluate_ocr_metrics.py \
    --ocr-dir ./ocr_outputs \
    --gt-dir  ./ground_truth_text \
    --output  ./results/ocr_metrics.tsv
```

Outputs a tab-separated table with `char_accuracy` and `word_accuracy` per file, plus macro averages.

---

### evaluate_extraction_metrics.py

Compares structured extraction outputs against ground-truth JSON files and reports per-field precision, recall, and F1.

**Prepare inputs:**

Ground-truth JSON format (one file per invoice):
```json
{
  "invoice_number": "INV-001",
  "invoice_date":   "15/03/2024",
  "total_amount":   1200.00,
  "tax_amount":     200.00
}
```

System prediction JSON: same structure, produced by exporting extracted fields (e.g. via `GET /api/invoices/{id}` and saving only the four fields).

```bash
python scripts/evaluate_extraction_metrics.py \
    --pred-dir ./extraction_outputs \
    --gt-dir   ./ground_truth_json \
    --tol      0.01 \
    --output   ./results/extraction_metrics.tsv
```

The `--tol` flag sets the tolerance for numeric amount comparison (default: 0.01).

Output includes a per-file match table and a per-field precision/recall/F1 summary with macro averages.

---

## Quick Start Checklist

- [ ] Tesseract installed and on `PATH` (`tesseract --version` works)
- [ ] poppler installed (`pdfinfo --version` works)
- [ ] `pip install -r requirements.txt` completed without errors
- [ ] Backend running: `uvicorn app.main:app --reload` at port 8000
- [ ] Frontend running: `npm run dev` at port 5173
- [ ] Browser: http://localhost:5173 shows the Invoice list page
- [ ] Upload a test PDF via the Upload page and verify it appears in the list
