#!/usr/bin/env python3
"""
create_sample_data.py
---------------------
Generates all sample directories and files needed to test the three scripts:

  sample_invoices/          - PNG invoice images for run_pipeline_on_folder.py
  ocr_outputs/              - Simulated OCR .txt outputs for evaluate_ocr_metrics.py
  ground_truth_text/        - Ground-truth .txt files for evaluate_ocr_metrics.py
  pred_json/                - Simulated extraction predictions for evaluate_extraction_metrics.py
  gt_json/                  - Ground-truth JSON for evaluate_extraction_metrics.py

Run from the backend/ directory:
    python scripts/create_sample_data.py
"""

import json
import sys
from pathlib import Path

# Check Pillow is available
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is not installed. Run: pip install Pillow")
    sys.exit(1)


ROOT = Path(__file__).parent.parent  # backend/

SAMPLE_INVOICES   = ROOT / "sample_invoices"
OCR_OUTPUTS       = ROOT / "ocr_outputs"
GROUND_TRUTH_TEXT = ROOT / "ground_truth_text"
PRED_JSON         = ROOT / "pred_json"
GT_JSON           = ROOT / "gt_json"

# ── Invoice text templates ────────────────────────────────────────────────────

INVOICES = [
    {
        "stem": "invoice_001",
        "text": """\
Acme Corp Ltd
123 Business Street, London, EC1A 1BB

INVOICE

Invoice No:   INV-2024-0042
Invoice Date: 15/03/2024
Due Date:     15/04/2024

Bill To:
  GlobalTech Solutions
  456 Tech Park, Manchester

Description                     Qty    Unit Price    Line Total
Web Development Services         10       100.00       1000.00
Project Management                5        80.00        400.00
Hosting Setup                     1       200.00        200.00

                                      Subtotal:       1600.00
                                      VAT (20%):       320.00
                                      Total Due:      1920.00

Currency: GBP
""",
        "gt": {
            "invoice_number": "INV-2024-0042",
            "invoice_date":   "15/03/2024",
            "total_amount":   1920.00,
            "tax_amount":     320.00,
        },
    },
    {
        "stem": "invoice_002",
        "text": """\
TechSupplies Inc.
789 Innovation Ave, New York, NY 10001

INVOICE

Invoice Number: INV-2024-0099
Date of Invoice: 02/04/2024
Payment Due:     02/05/2024

Bill To:
  Startup Ventures LLC
  101 Startup Blvd, San Francisco

Description                     Qty    Unit Price    Total
Cloud Server (monthly)            3       150.00       450.00
Support Hours                    10        75.00       750.00
Software Licence                  2       500.00      1000.00

                                      Subtotal:       2200.00
                                      Tax (8%):        176.00
                                      Grand Total:    2376.00

USD
""",
        "gt": {
            "invoice_number": "INV-2024-0099",
            "invoice_date":   "02/04/2024",
            "total_amount":   2376.00,
            "tax_amount":     176.00,
        },
    },
    {
        "stem": "invoice_003",
        "text": """\
DesignStudio GmbH
Hauptstrasse 10, 10115 Berlin

RECHNUNG / INVOICE

Invoice No: DS-2024-007
Invoice Date: 20 Mar 2024
Due Date: 20 Apr 2024

Client:
  EU Commerce BV
  Amsterdam, Netherlands

Item                            Qty    Unit Price    Amount
Logo Design                       1      1200.00     1200.00
Brand Guidelines Document         1       800.00      800.00
Social Media Kit                  1       400.00      400.00

                                      Net Total:      2400.00
                                      VAT (19%):       456.00
                                      Total Amount:   2856.00

EUR
""",
        "gt": {
            "invoice_number": "DS-2024-007",
            "invoice_date":   "20 Mar 2024",
            "total_amount":   2856.00,
            "tax_amount":     456.00,
        },
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_invoice_image(text: str, out_path: Path) -> None:
    """Render invoice text onto a white A4-like image and save as PNG."""
    width, height = 794, 1123   # ~A4 at 96 dpi
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Use a basic bitmap font; ImageFont.load_default() is always available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except (IOError, OSError):
        font = ImageFont.load_default()
        font_title = font

    x, y = 50, 50
    for line in text.splitlines():
        f = font_title if line.strip() in ("INVOICE", "RECHNUNG / INVOICE") else font
        draw.text((x, y), line, fill="black", font=f)
        y += 20

    img.save(str(out_path), format="PNG", dpi=(150, 150))


def introduce_ocr_noise(text: str) -> str:
    """Simulate minor OCR errors: swap common look-alike characters."""
    replacements = [
        ("0", "O", 0.15),
        ("1", "l", 0.10),
        ("rn", "m", 0.20),
        (".", ",", 0.10),
    ]
    import random
    random.seed(42)
    result = list(text)
    for i, ch in enumerate(result):
        for orig, replacement, prob in replacements:
            if ch == orig and random.random() < prob:
                result[i] = replacement
                break
    return "".join(result)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    for d in (SAMPLE_INVOICES, OCR_OUTPUTS, GROUND_TRUTH_TEXT, PRED_JSON, GT_JSON):
        d.mkdir(parents=True, exist_ok=True)

    for inv in INVOICES:
        stem = inv["stem"]
        text = inv["text"]
        gt   = inv["gt"]

        # 1. Invoice image (for run_pipeline_on_folder.py)
        img_path = SAMPLE_INVOICES / f"{stem}.png"
        make_invoice_image(text, img_path)
        print(f"  Created invoice image:   {img_path.relative_to(ROOT)}")

        # 2. Ground-truth text (clean)
        gt_txt_path = GROUND_TRUTH_TEXT / f"{stem}.txt"
        gt_txt_path.write_text(text, encoding="utf-8")
        print(f"  Created GT text:         {gt_txt_path.relative_to(ROOT)}")

        # 3. Simulated OCR output (with minor noise)
        ocr_txt_path = OCR_OUTPUTS / f"{stem}.txt"
        ocr_txt_path.write_text(introduce_ocr_noise(text), encoding="utf-8")
        print(f"  Created OCR output:      {ocr_txt_path.relative_to(ROOT)}")

        # 4. Ground-truth JSON (for evaluate_extraction_metrics.py)
        gt_json_path = GT_JSON / f"{stem}.json"
        gt_json_path.write_text(json.dumps(gt, indent=2), encoding="utf-8")
        print(f"  Created GT JSON:         {gt_json_path.relative_to(ROOT)}")

        # 5. Simulated prediction JSON (one field deliberately off to show F1 < 1)
        pred = dict(gt)
        if stem == "invoice_002":
            pred["tax_amount"] = 170.00   # wrong on purpose
        if stem == "invoice_003":
            pred["invoice_number"] = None  # missing on purpose
        pred_json_path = PRED_JSON / f"{stem}.json"
        pred_json_path.write_text(json.dumps(pred, indent=2), encoding="utf-8")
        print(f"  Created pred JSON:       {pred_json_path.relative_to(ROOT)}")

        print()

    print("Sample data created successfully.")
    print()
    print("Run the scripts:")
    print("  python scripts/run_pipeline_on_folder.py --input ./sample_invoices --csv ./out/report.csv")
    print("  python scripts/evaluate_ocr_metrics.py --ocr-dir ./ocr_outputs --gt-dir ./ground_truth_text --output ./out/ocr_metrics.tsv")
    print("  python scripts/evaluate_extraction_metrics.py --pred-dir ./pred_json --gt-dir ./gt_json --tol 0.01 --output ./out/extraction_metrics.tsv")


if __name__ == "__main__":
    main()
