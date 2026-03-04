#!/usr/bin/env python3
"""
run_pipeline_on_folder.py
--------------------------
Run the full invoice processing pipeline on every PDF/image file found
inside a given folder, persist results to the database, optionally export
a CSV summary, and print a timing report.

Usage:
    python scripts/run_pipeline_on_folder.py --input ./sample_invoices [--csv results.csv]
"""

import argparse
import csv
import sys
import time
from pathlib import Path

# Allow running from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage.database import init_db, SessionLocal
from app.services.storage.crud import create_invoice
from app.services.pipeline import run_pipeline
from app.services.ingestion.file_handler import ALLOWED_EXTENSIONS


def collect_files(folder: Path):
    """Yield all invoice files with supported extensions inside *folder*."""
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            yield path


def main():
    parser = argparse.ArgumentParser(description="Batch-process a folder of invoices.")
    parser.add_argument("--input", required=True, help="Path to the folder containing invoice files.")
    parser.add_argument("--csv", default=None, help="Optional output CSV path for the results summary.")
    args = parser.parse_args()

    input_folder = Path(args.input).resolve()
    if not input_folder.is_dir():
        print(f"ERROR: '{input_folder}' is not a valid directory.")
        sys.exit(1)

    files = list(collect_files(input_folder))
    if not files:
        print(f"No supported invoice files found in '{input_folder}'.")
        sys.exit(0)

    print(f"Found {len(files)} file(s). Initialising database...")
    init_db()

    rows = []
    total_start = time.perf_counter()

    with SessionLocal() as db:
        for file_path in files:
            start = time.perf_counter()
            print(f"  Processing: {file_path.name} ...", end=" ", flush=True)

            invoice = create_invoice(db, filename=file_path.name, file_path=str(file_path))
            invoice = run_pipeline(db, invoice)

            elapsed = time.perf_counter() - start
            status_str = invoice.status.value
            print(f"{status_str} ({elapsed:.2f}s)")

            rows.append(
                {
                    "id": invoice.id,
                    "filename": invoice.filename,
                    "status": status_str,
                    "supplier_name": invoice.supplier_name or "",
                    "invoice_number": invoice.invoice_number or "",
                    "invoice_date": invoice.invoice_date or "",
                    "total_amount": invoice.total_amount or "",
                    "currency": invoice.currency or "",
                    "validation_notes": invoice.validation_notes or "",
                    "processing_time_s": f"{elapsed:.3f}",
                }
            )

    total_elapsed = time.perf_counter() - total_start
    succeeded = sum(1 for r in rows if r["status"] == "completed")
    failed = len(rows) - succeeded

    print(
        f"\nDone. {succeeded}/{len(rows)} succeeded, {failed} failed. "
        f"Total time: {total_elapsed:.2f}s (avg {total_elapsed / len(rows):.2f}s/file)."
    )

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"CSV report written to '{csv_path}'.")


if __name__ == "__main__":
    main()
