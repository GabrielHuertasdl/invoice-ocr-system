#!/usr/bin/env python3
"""
generar_facturas_sinteticas.py
------------------------------
Generates at least 200 synthetic invoice records with realistic but
entirely fictional data, following the exact schema used by the project
(Invoice ORM model + LineItem ORM model).

Output
------
  data/facturas_sinteticas/json/    One JSON file per invoice (NN.json)

Optional flags
--------------
  --count N      Number of invoices to generate (default: 200)
  --insert-db    Also insert records into invoice_system.db via the
                 existing CRUD layer (same flow as the real pipeline)
  --out-dir DIR  Override the default output directory

Usage (from invoice_system/backend/ with venv active)
------------------------------------------------------
  python scripts/generar_facturas_sinteticas.py
  python scripts/generar_facturas_sinteticas.py --count 300
  python scripts/generar_facturas_sinteticas.py --insert-db
  python scripts/generar_facturas_sinteticas.py --count 50 --out-dir /tmp/test_invoices
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

# ── Allow running from backend/ without installing the package ────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Data pools ────────────────────────────────────────────────────────────────

SUPPLIERS = [
    ("Acme Corp Ltd",           "123 Business Street, London, EC1A 1BB",      "GB", "GBP", 0.20),
    ("TechSupplies Inc.",       "789 Innovation Ave, New York, NY 10001",      "US", "USD", 0.08),
    ("DesignStudio GmbH",       "Hauptstrasse 10, 10115 Berlin",               "DE", "EUR", 0.19),
    ("GlobalTech Solutions",    "456 Tech Park, Manchester, M1 2WD",           "GB", "GBP", 0.20),
    ("Ibérica Servicios S.L.",  "Calle Mayor 15, 28013 Madrid",                "ES", "EUR", 0.21),
    ("Nordic Systems AB",       "Storgatan 5, 111 29 Stockholm",               "SE", "EUR", 0.25),
    ("Sunrise Digital Lda.",    "Rua Augusta 80, 1100-053 Lisboa",             "PT", "EUR", 0.23),
    ("Alpine Consulting AG",    "Bahnhofstrasse 22, 8001 Zürich",              "CH", "CHF", 0.077),
    ("BrightMind Analytics",    "101 Data Drive, Austin, TX 78701",            "US", "USD", 0.0825),
    ("Nexus Software BV",       "Keizersgracht 100, 1015 CL Amsterdam",        "NL", "EUR", 0.21),
    ("Coastal Media Ltd",       "15 Harbour View, Dublin 2, D02 XY45",        "IE", "EUR", 0.23),
    ("Ferro Industrias S.A.",   "Avda. Diagonal 420, 08037 Barcelona",         "ES", "EUR", 0.21),
    ("Pacific Freight Co.",     "500 Ocean Blvd, Los Angeles, CA 90001",       "US", "USD", 0.095),
    ("RedBrick Studios",        "27 Brick Lane, London, E1 6PU",               "GB", "GBP", 0.20),
    ("DataFlow GmbH",           "Unter den Linden 77, 10117 Berlin",           "DE", "EUR", 0.19),
    ("Horizon Ventures S.r.l.", "Via Roma 55, 20121 Milano",                   "IT", "EUR", 0.22),
    ("Summit Logistics ApS",    "Vesterbrogade 149, 1620 Copenhagen",          "DK", "EUR", 0.25),
    ("ClearPath IT S.L.",       "Gran Via 23, 48001 Bilbao",                   "ES", "EUR", 0.21),
    ("Blueprint Architects",    "2 Regent Street, Edinburgh, EH1 3DG",         "GB", "GBP", 0.20),
    ("Zenith Consulting Inc.",  "350 Fifth Avenue, New York, NY 10118",        "US", "USD", 0.08875),
]

CLIENTS = [
    "GlobalTech Solutions",
    "Startup Ventures LLC",
    "EU Commerce BV",
    "Retail Dynamics S.A.",
    "Omega Holding Group",
    "Pioneer Retail Ltd",
    "FastGrow Corp",
    "SkyNet Industries",
    "Meridian Partners",
    "Atlas Trading Co.",
    "Vanguard Enterprises",
    "Cascade Systems",
    "Polaris Media Group",
    "Titan Manufacturing",
    "Quantum Leap Ltd",
]

LINE_ITEM_POOL = [
    ("Web Development Services",        50,  250),
    ("Mobile App Development",          80,  400),
    ("UI/UX Design",                    60,  200),
    ("Project Management",              50,  150),
    ("Cloud Hosting (monthly)",        100,  500),
    ("Database Administration",         70,  180),
    ("Security Audit",                 300, 1200),
    ("SEO Optimisation",               100,  400),
    ("Content Writing",                 30,   80),
    ("Technical Support (hours)",       40,  120),
    ("Software Licence",               200,  800),
    ("Server Migration",               500, 2000),
    ("Data Analysis",                   80,  250),
    ("Training Sessions",              150,  400),
    ("Brand Identity Design",          400, 1500),
    ("Social Media Management",        200,  600),
    ("API Integration",                300,  900),
    ("QA Testing",                      60,  150),
    ("DevOps Consulting",              100,  350),
    ("Network Setup",                  150,  500),
    ("Logo Design",                    300, 1200),
    ("Photography",                    200,  800),
    ("Video Production",               500, 3000),
    ("Legal Advisory",                 200,  800),
    ("Accounting Services",            150,  500),
    ("HR Consulting",                  100,  350),
    ("Office Supplies",                 10,  100),
    ("Hardware Procurement",           200, 2000),
    ("Maintenance Contract",           300, 1000),
    ("Subscription Services",           50,  300),
]

INVOICE_PREFIXES = ["INV", "FAC", "REC", "DOC", "BILL", "SRV"]


# ── Generator helpers ─────────────────────────────────────────────────────────

def _invoice_number(rng: random.Random, year: int, seq: int) -> str:
    prefix = rng.choice(INVOICE_PREFIXES)
    # Mix of formats seen in the real sample data
    style = rng.randint(0, 2)
    if style == 0:
        return f"{prefix}-{year}-{seq:04d}"
    if style == 1:
        return f"{prefix}{year}{seq:04d}"
    return f"{prefix}-{seq:04d}"


def _random_date(rng: random.Random, start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


def _format_date(d: date, fmt: str) -> str:
    """Return date in the format matching the project's varied samples."""
    if fmt == "dd/mm/yyyy":
        return d.strftime("%d/%m/%Y")
    if fmt == "mm/dd/yyyy":
        return d.strftime("%m/%d/%Y")
    # "D Mon YYYY"
    return d.strftime("%-d %b %Y")


def _generate_line_items(
    rng: random.Random, n: int
) -> list[dict[str, Any]]:
    items = rng.sample(LINE_ITEM_POOL, n)
    result = []
    for description, min_price, max_price in items:
        unit_price = round(rng.uniform(min_price, max_price), 2)
        quantity = rng.choice([1, 1, 1, 2, 3, 5, 10])
        line_total = round(unit_price * quantity, 2)
        result.append(
            {
                "description": description,
                "quantity": float(quantity),
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )
    return result


def generate_invoice(rng: random.Random, seq: int) -> dict[str, Any]:
    """
    Generate one synthetic invoice dict that matches the Invoice ORM schema.

    All monetary relationships are exact:
        subtotal  = sum of line_total values
        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = subtotal + tax_amount
    """
    supplier_name, address, _country, currency, tax_rate = rng.choice(SUPPLIERS)
    client = rng.choice(CLIENTS)

    # Dates – invoice between 2022-01-01 and 2025-12-31
    date_formats = ["dd/mm/yyyy", "mm/dd/yyyy", "D Mon YYYY"]
    date_fmt = rng.choice(date_formats)

    inv_date = _random_date(rng, date(2022, 1, 1), date(2025, 12, 31))
    due_days = rng.choice([15, 30, 45, 60])
    due_date = inv_date + timedelta(days=due_days)

    # Year derived from invoice date (for invoice number)
    year = inv_date.year

    # Line items (1–5)
    n_items = rng.randint(1, 5)
    line_items = _generate_line_items(rng, n_items)

    subtotal = round(sum(li["line_total"] for li in line_items), 2)
    tax_amount = round(subtotal * tax_rate, 2)
    total_amount = round(subtotal + tax_amount, 2)

    return {
        "filename": f"factura_{seq:04d}.pdf",
        "file_path": f"./data/facturas_sinteticas/json/factura_{seq:04d}.pdf",
        "status": "completed",
        "supplier_name": supplier_name,
        "supplier_address": address,
        "client_name": client,
        "invoice_number": _invoice_number(rng, year, seq),
        "invoice_date": _format_date(inv_date, date_fmt),
        "due_date": _format_date(due_date, date_fmt),
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "currency": currency,
        "tax_rate_pct": round(tax_rate * 100, 2),
        "validation_notes": None,
        "error_message": None,
        "line_items": line_items,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic invoice JSON files for testing."
    )
    parser.add_argument(
        "--count", type=int, default=200,
        help="Number of invoices to generate (default: 200).",
    )
    parser.add_argument(
        "--out-dir", default=None,
        help="Output directory for JSON files (default: data/facturas_sinteticas/json/).",
    )
    parser.add_argument(
        "--insert-db", action="store_true",
        help="Also insert generated invoices into invoice_system.db.",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    args = parser.parse_args()

    root = Path(__file__).parent.parent  # backend/
    out_dir = Path(args.out_dir) if args.out_dir else root / "data" / "facturas_sinteticas" / "json"
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    invoices: list[dict[str, Any]] = []

    print(f"Generating {args.count} synthetic invoices …")
    for i in range(1, args.count + 1):
        inv = generate_invoice(rng, i)
        invoices.append(inv)
        json_path = out_dir / f"factura_{i:04d}.json"
        json_path.write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  ✓ {args.count} JSON files written to {out_dir}")

    # ── Optional DB insertion ─────────────────────────────────────────────────
    if args.insert_db:
        try:
            from app.services.storage.database import init_db, SessionLocal
            from app.services.storage.crud import create_invoice, update_invoice, save_line_items
            from app.models.invoice import ProcessingStatus
        except ImportError as exc:
            print(f"ERROR: Could not import app modules – {exc}")
            print("Make sure you are running from invoice_system/backend/ with venv active.")
            sys.exit(1)

        print(f"\nInserting {args.count} records into the database …")
        init_db()

        inserted = 0
        with SessionLocal() as db:
            for inv in invoices:
                record = create_invoice(
                    db,
                    filename=inv["filename"],
                    file_path=inv["file_path"],
                )
                update_invoice(
                    db,
                    record,
                    {
                        "status": ProcessingStatus.completed,
                        "supplier_name": inv["supplier_name"],
                        "invoice_number": inv["invoice_number"],
                        "invoice_date": inv["invoice_date"],
                        "due_date": inv["due_date"],
                        "subtotal": inv["subtotal"],
                        "tax_amount": inv["tax_amount"],
                        "total_amount": inv["total_amount"],
                        "currency": inv["currency"],
                        "raw_text": _build_raw_text(inv),
                        "validation_notes": inv["validation_notes"],
                    },
                )
                save_line_items(db, record, inv["line_items"])
                inserted += 1

        print(f"  ✓ {inserted} records inserted into the database.")

    print("\nDone.")
    print(f"  JSON files : {out_dir}")
    if args.insert_db:
        print(f"  Database   : {root / 'invoice_system.db'}")


def _build_raw_text(inv: dict[str, Any]) -> str:
    """Build a minimal raw OCR-style text for the synthetic invoice."""
    lines = [
        inv["supplier_name"],
        inv.get("supplier_address", ""),
        "",
        "INVOICE",
        "",
        f"Invoice No:   {inv['invoice_number']}",
        f"Invoice Date: {inv['invoice_date']}",
        f"Due Date:     {inv['due_date']}",
        "",
        f"Bill To: {inv.get('client_name', '')}",
        "",
        f"{'Description':<35} {'Qty':>5}  {'Unit Price':>10}  {'Line Total':>10}",
    ]
    for item in inv["line_items"]:
        lines.append(
            f"{item['description']:<35} {item['quantity']:>5.0f}  "
            f"{item['unit_price']:>10.2f}  {item['line_total']:>10.2f}"
        )
    lines += [
        "",
        f"{'Subtotal:':>55} {inv['subtotal']:>10.2f}",
        f"{'Tax ({:.0f}%):'.format(inv['tax_rate_pct']):>55} {inv['tax_amount']:>10.2f}",
        f"{'Total Due:':>55} {inv['total_amount']:>10.2f}",
        "",
        f"Currency: {inv['currency']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
