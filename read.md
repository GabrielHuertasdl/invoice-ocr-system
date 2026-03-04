How to launch the backend

  cd invoice_system/backend
  python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env          # edit if needed
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  Swagger UI: http://localhost:8000/docs

  System requirements: Tesseract 4+ on PATH (sudo apt install tesseract-ocr) and poppler (sudo apt install
  poppler-utils) for PDF support.

  ---
  How to launch the frontend

  cd invoice_system/frontend
  npm install
  npm run dev

  Open http://localhost:5173. The Vite proxy forwards /api/* to the backend automatically.

  ---
  How to run the scripts

  All commands from invoice_system/backend/ with the venv active:

  # Batch process a folder of invoices
  python scripts/run_pipeline_on_folder.py --input ./sample_invoices --csv ./out/report.csv

  # Evaluate OCR accuracy (OCR .txt outputs vs ground-truth .txt files, matched by filename stem)
  python scripts/evaluate_ocr_metrics.py \
      --ocr-dir ./ocr_outputs --gt-dir ./ground_truth_text --output ./out/ocr_metrics.tsv

  # Evaluate extraction field accuracy (predicted JSON vs ground-truth JSON)
  python scripts/evaluate_extraction_metrics.py \
      --pred-dir ./pred_json --gt-dir ./gt_json --tol 0.01 --output ./out/extraction_metrics.tsv
