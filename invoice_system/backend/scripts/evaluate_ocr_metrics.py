#!/usr/bin/env python3
"""
evaluate_ocr_metrics.py
------------------------
Compare OCR output text files against ground-truth text files and compute
character-level accuracy (CER) and word-level accuracy (WER).

Expected folder layout:
    --ocr-dir      folder of *.txt files produced by the OCR engine
    --gt-dir       folder of *.txt ground-truth files

File names must match between the two directories (e.g. invoice_001.txt in
both).  A TSV report is printed to stdout and optionally saved to a file.

Usage:
    python scripts/evaluate_ocr_metrics.py \\
        --ocr-dir ./ocr_outputs \\
        --gt-dir  ./ground_truth \\
        [--output metrics_ocr.tsv]
"""

import argparse
import sys
from pathlib import Path


# ── Metric helpers ────────────────────────────────────────────────────────────

def _edit_distance(a: str, b: str) -> int:
    """Standard dynamic-programming edit distance (Levenshtein)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * lb
        for j, cb in enumerate(b, 1):
            curr[j] = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            )
        prev = curr
    return prev[lb]


def char_accuracy(hypothesis: str, reference: str) -> float:
    """
    Character-level accuracy = 1 - CER.

    CER = edit_distance(hyp, ref) / len(ref)
    Returns a value in [0, 1].  Returns 1.0 if reference is empty.
    """
    if not reference:
        return 1.0
    cer = _edit_distance(hypothesis, reference) / len(reference)
    return max(0.0, 1.0 - cer)


def word_accuracy(hypothesis: str, reference: str) -> float:
    """
    Word-level accuracy = 1 - WER.

    WER = edit_distance(hyp_words, ref_words) / len(ref_words)
    Returns a value in [0, 1].  Returns 1.0 if reference has no words.
    """
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if not ref_words:
        return 1.0
    wer = _edit_distance(hyp_words, ref_words) / len(ref_words)
    return max(0.0, 1.0 - wer)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate OCR output against ground truth.")
    parser.add_argument("--ocr-dir", required=True, help="Directory with OCR .txt files.")
    parser.add_argument("--gt-dir",  required=True, help="Directory with ground-truth .txt files.")
    parser.add_argument("--output",  default=None,  help="Optional TSV output file path.")
    args = parser.parse_args()

    ocr_dir = Path(args.ocr_dir)
    gt_dir  = Path(args.gt_dir)

    for d in (ocr_dir, gt_dir):
        if not d.is_dir():
            print(f"ERROR: '{d}' is not a valid directory.", file=sys.stderr)
            sys.exit(1)

    gt_files = {f.stem: f for f in gt_dir.glob("*.txt")}
    ocr_files = {f.stem: f for f in ocr_dir.glob("*.txt")}
    common = sorted(set(gt_files) & set(ocr_files))

    if not common:
        print("No matching file names found between OCR and ground-truth directories.")
        sys.exit(0)

    missing_ocr = sorted(set(gt_files) - set(ocr_files))
    if missing_ocr:
        print(f"WARNING: {len(missing_ocr)} GT file(s) have no matching OCR output: {missing_ocr[:5]}")

    header = ["file", "char_accuracy", "word_accuracy"]
    rows = []

    for stem in common:
        gt_text  = gt_files[stem].read_text(encoding="utf-8", errors="replace")
        ocr_text = ocr_files[stem].read_text(encoding="utf-8", errors="replace")
        ca = char_accuracy(ocr_text, gt_text)
        wa = word_accuracy(ocr_text, gt_text)
        rows.append({"file": stem, "char_accuracy": ca, "word_accuracy": wa})

    # Print table
    print("\t".join(header))
    for r in rows:
        print(f"{r['file']}\t{r['char_accuracy']:.4f}\t{r['word_accuracy']:.4f}")

    # Averages
    avg_ca = sum(r["char_accuracy"] for r in rows) / len(rows)
    avg_wa = sum(r["word_accuracy"] for r in rows) / len(rows)
    print("-" * 50)
    print(f"AVERAGE\t{avg_ca:.4f}\t{avg_wa:.4f}")
    print(f"\nEvaluated {len(rows)} file(s).  Avg char accuracy: {avg_ca:.2%}  |  Avg word accuracy: {avg_wa:.2%}")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            f.write("\t".join(header) + "\n")
            for r in rows:
                f.write(f"{r['file']}\t{r['char_accuracy']:.4f}\t{r['word_accuracy']:.4f}\n")
            f.write(f"AVERAGE\t{avg_ca:.4f}\t{avg_wa:.4f}\n")
        print(f"Report saved to '{out_path}'.")


if __name__ == "__main__":
    main()
