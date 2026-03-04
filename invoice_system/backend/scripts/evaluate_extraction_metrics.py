#!/usr/bin/env python3
"""
evaluate_extraction_metrics.py
-------------------------------
Compare structured extraction outputs against ground-truth JSON or CSV
and compute per-field precision, recall, and F1 score for:
    invoice_number, invoice_date, total_amount, tax_amount

Ground-truth format (JSON, one object per file):
    { "invoice_number": "INV-001", "invoice_date": "2024-01-15",
      "total_amount": 1200.00, "tax_amount": 200.00 }

System output format: same JSON structure, produced by the extraction layer.

Both directories must contain matching filenames (stem must match).
Numeric fields are compared within a configurable tolerance.

Usage:
    python scripts/evaluate_extraction_metrics.py \\
        --pred-dir ./extraction_outputs \\
        --gt-dir   ./ground_truth_json  \\
        [--tol 0.01] [--output metrics_extraction.tsv]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


EVAL_FIELDS = ["invoice_number", "invoice_date", "total_amount", "tax_amount"]


# ── Comparison helpers ────────────────────────────────────────────────────────

def _normalise_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value).strip().lower()


def _normalise_amount(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _field_match(pred: Any, gt: Any, field: str, tol: float) -> bool:
    """Return True if the predicted value matches the ground truth for *field*."""
    if field in ("total_amount", "tax_amount"):
        pv = _normalise_amount(pred)
        gv = _normalise_amount(gt)
        if pv is None or gv is None:
            return pv == gv
        return abs(pv - gv) <= tol
    else:
        return _normalise_str(pred) == _normalise_str(gt)


# ── Precision / Recall / F1 per field ────────────────────────────────────────

class FieldStats:
    def __init__(self):
        self.tp = 0   # predicted, correct
        self.fp = 0   # predicted, wrong
        self.fn = 0   # not predicted (None), but GT has value

    def update(self, pred: Any, gt: Any, field: str, tol: float):
        pred_present = pred is not None and str(pred).strip() != ""
        gt_present   = gt   is not None and str(gt).strip()   != ""

        if pred_present and gt_present:
            if _field_match(pred, gt, field, tol):
                self.tp += 1
            else:
                self.fp += 1
        elif pred_present and not gt_present:
            self.fp += 1
        elif not pred_present and gt_present:
            self.fn += 1
        # both absent -> true negative, not counted in P/R/F1

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


# ── Main ──────────────────────────────────────────────────────────────────────

def load_json_or_csv(path: Path) -> Dict[str, Any]:
    """Load a single ground-truth or prediction file (JSON or single-row CSV)."""
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() in (".csv", ".tsv"):
        import csv
        delim = "\t" if path.suffix.lower() == ".tsv" else ","
        with path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delim)
            rows = list(reader)
        if rows:
            return rows[0]
        return {}
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate extraction field accuracy.")
    parser.add_argument("--pred-dir", required=True, help="Directory with predicted JSON files.")
    parser.add_argument("--gt-dir",   required=True, help="Directory with ground-truth JSON files.")
    parser.add_argument("--tol",      type=float, default=0.01,
                        help="Tolerance for numeric amount comparison (default: 0.01).")
    parser.add_argument("--output",   default=None, help="Optional TSV output file.")
    args = parser.parse_args()

    pred_dir = Path(args.pred_dir)
    gt_dir   = Path(args.gt_dir)

    for d in (pred_dir, gt_dir):
        if not d.is_dir():
            print(f"ERROR: '{d}' is not a valid directory.", file=sys.stderr)
            sys.exit(1)

    gt_files   = {f.stem: f for f in gt_dir.iterdir()   if f.suffix.lower() in (".json", ".csv", ".tsv")}
    pred_files = {f.stem: f for f in pred_dir.iterdir() if f.suffix.lower() in (".json", ".csv", ".tsv")}
    common     = sorted(set(gt_files) & set(pred_files))

    if not common:
        print("No matching file names found between prediction and ground-truth directories.")
        sys.exit(0)

    stats: Dict[str, FieldStats] = {f: FieldStats() for f in EVAL_FIELDS}
    per_file_rows = []

    for stem in common:
        try:
            gt   = load_json_or_csv(gt_files[stem])
            pred = load_json_or_csv(pred_files[stem])
        except Exception as exc:
            print(f"WARNING: could not load '{stem}': {exc}", file=sys.stderr)
            continue

        row = {"file": stem}
        for field in EVAL_FIELDS:
            gv = gt.get(field)
            pv = pred.get(field)
            stats[field].update(pv, gv, field, args.tol)
            match = _field_match(pv, gv, field, args.tol) if (pv is not None or gv is not None) else True
            row[field] = "OK" if match else f"PRED={pv!r} GT={gv!r}"
        per_file_rows.append(row)

    # Print per-file detail
    header = ["file"] + EVAL_FIELDS
    print("\t".join(header))
    for r in per_file_rows:
        print("\t".join(str(r.get(h, "")) for h in header))

    # Print per-field summary
    print("\n--- Field-level Precision / Recall / F1 ---")
    summary_header = ["field", "precision", "recall", "f1", "TP", "FP", "FN"]
    print("\t".join(summary_header))
    for field in EVAL_FIELDS:
        s = stats[field]
        print(f"{field}\t{s.precision:.4f}\t{s.recall:.4f}\t{s.f1:.4f}\t{s.tp}\t{s.fp}\t{s.fn}")

    # Macro average
    avg_p  = sum(stats[f].precision for f in EVAL_FIELDS) / len(EVAL_FIELDS)
    avg_r  = sum(stats[f].recall    for f in EVAL_FIELDS) / len(EVAL_FIELDS)
    avg_f1 = sum(stats[f].f1        for f in EVAL_FIELDS) / len(EVAL_FIELDS)
    print("-" * 60)
    print(f"MACRO AVG\t{avg_p:.4f}\t{avg_r:.4f}\t{avg_f1:.4f}")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            f.write("\t".join(summary_header) + "\n")
            for field in EVAL_FIELDS:
                s = stats[field]
                f.write(f"{field}\t{s.precision:.4f}\t{s.recall:.4f}\t{s.f1:.4f}\t{s.tp}\t{s.fp}\t{s.fn}\n")
            f.write(f"MACRO AVG\t{avg_p:.4f}\t{avg_r:.4f}\t{avg_f1:.4f}\n")
        print(f"\nReport saved to '{out_path}'.")


if __name__ == "__main__":
    main()
