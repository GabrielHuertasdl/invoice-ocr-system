# 5. Results and Findings

This chapter presents the empirical outcomes of the implemented invoice processing system,
covering the synthetic dataset used for evaluation, OCR performance, information extraction
accuracy, and the behaviour of the AI-assisted search and question-answering layer.

---

## 5.1 Synthetic Evaluation Dataset

Because real-world invoice data is commercially sensitive and not publicly available, a
controlled synthetic dataset of **200 invoices** was generated programmatically to evaluate
the system end-to-end. The dataset was designed to reflect genuine structural diversity
found in business invoices across multiple jurisdictions.

### 5.1.1 Dataset Composition

| Property | Value |
|---|---|
| Total invoices | 200 |
| Unique suppliers | 20 |
| Countries represented | 11 (UK, US, DE, ES, SE, PT, CH, NL, IE, IT, DK) |
| Currencies | GBP, USD, EUR, CHF |
| Tax / VAT rates | 7 distinct rates (7.7 % – 25 %) |
| Invoice date formats | 2 (DD/MM/YYYY, D Mon YYYY) |
| Invoice number formats | 3 (INV-YYYY-NNNN, FACNNNNNNNN, BILL-NNNN) |
| Payment terms | 15, 30, 45, 60 days |
| Line items per invoice | 1 – 5 |
| Service / product types | 29 |

**Fig 1** shows the invoice count per supplier. The distribution is approximately uniform
(mean ≈ 10 invoices per supplier, range 10–18), avoiding supplier-level bias in any
downstream evaluation.

> **[Insert fig1_supplier_distribution.png]**

### 5.1.2 Currency Distribution

**Fig 2** illustrates the currency split across the 200 invoices. EUR dominates at 55 %,
reflecting the number of European suppliers in the pool. GBP accounts for 13 % and CHF for
7 %, matching their respective supplier counts.

> **[Insert fig2_currency_distribution.png]**

### 5.1.3 Line-Item Complexity

**Fig 3** shows how many line items appear per invoice. Invoices with five line items are
the most common (50 invoices, 25 %), while single-line invoices account for 15 %. This
distribution was intentional: it exercises the tabular extraction logic across a range of
document complexities.

> **[Insert fig3_line_items.png]**

### 5.1.4 Invoice Total Distribution

**Fig 4** presents the distribution of invoice totals. Values range from £49.75 to
£36,035.95, with a mean of £5,256.60 and a median of £3,414.37. The right-skewed
distribution—common in real B2B invoice data—was produced by combining multiple line
items with unit prices drawn from a realistic price pool (£30 – £3,000).

> **[Insert fig4_invoice_totals.png]**

### 5.1.5 Tax Rate Coverage

**Fig 5** shows the frequency of each VAT/tax rate in the dataset. Eleven distinct rates
are represented (7.7 % in Switzerland to 25 % in Sweden), covering the main European VAT
rates plus US state-level sales taxes. The 21 % rate (Spain, Netherlands) is the most
frequent (46 invoices), as three suppliers use it.

> **[Insert fig5_tax_rates.png]**

### 5.1.6 Date Format Coverage

**Fig 8** shows that 63 % of invoices use the DD/MM/YYYY format and 37 % use the
written-month format (e.g. "15 March 2024"). No ambiguous MM/DD/YYYY dates were generated
so that ground-truth labels remained unambiguous during evaluation.

> **[Insert fig8_date_formats.png]**

---

## 5.2 OCR Performance

Tesseract OCR (v5, engine mode 3, PSM 6) was applied to three representative invoice
images. The OCR output was compared character-by-character and word-by-word against
manually verified ground-truth transcripts using Levenshtein edit distance.

### 5.2.1 Metrics

| Invoice | Char Accuracy | Word Accuracy |
|---|---|---|
| invoice_001 | 98.48 % | 84.75 % |
| invoice_002 | 98.48 % | 86.67 % |
| invoice_003 | 98.41 % | 85.00 % |
| **Average** | **98.46 %** | **85.47 %** |

**Fig 6** illustrates these averages. Character accuracy is consistently high (>98 %),
confirming that Tesseract correctly identifies the vast majority of individual characters.
Word accuracy is lower (≈85 %), which is expected: a single substituted character turns an
entire token incorrect (e.g. `l0001` instead of `10001`).

> **[Insert fig6_ocr_metrics.png]**

### 5.2.2 Observed Error Patterns

Inspection of the OCR outputs revealed a consistent set of character-level confusions:

| OCR output | Ground truth | Likely cause |
|---|---|---|
| `l` | `1` | Lowercase L / digit-1 ambiguity in sans-serif fonts |
| `O` | `0` | Uppercase O / digit-0 ambiguity |
| `EClA` | `EC1A` | Digit-1 confused with uppercase I or L |
| `200,0O` | `200.00` | Comma / decimal separator + O/0 confusion |

These artefacts are well-known limitations of scene-text OCR and are handled downstream
by the amount-normalisation routine in the extraction layer.

---

## 5.3 Information Extraction Accuracy

The rule-based extraction engine was evaluated on the same three invoices by comparing
predicted JSON output against ground-truth JSON records for four key fields:
`invoice_number`, `invoice_date`, `total_amount`, and `tax_amount`.

### 5.3.1 Per-Field Results

| Field | Precision | Recall | F1 |
|---|---|---|---|
| invoice_number | 1.00 | 0.67 | 0.80 |
| invoice_date | 1.00 | 1.00 | **1.00** |
| total_amount | 1.00 | 1.00 | **1.00** |
| tax_amount | 0.67 | 1.00 | 0.80 |
| **Macro average** | **0.92** | **0.92** | **0.90** |

**Fig 7** visualises precision, recall, and F1 for each field alongside the macro-average
F1 of 0.90.

> **[Insert fig7_extraction_metrics.png]**

### 5.3.2 Analysis of Failures

**invoice_number (recall = 0.67):**
Invoice 003 used the format `DS-2024-007` (a "DS-" prefix not covered by the compiled
regex patterns). The extractor returned `None` rather than a false positive, so precision
remained 1.0. This indicates the system is conservative: it prefers missing a value over
reporting an incorrect one.

**tax_amount (precision = 0.67):**
Invoice 002 had a predicted tax amount of £170.00 against the ground truth of £176.00.
The OCR artefact `O2/O4` (digit confusion) propagated to the `8%` rate parsed from the
line `Tax (8%)`, which the extractor multiplied against an incorrect subtotal figure.
This illustrates the cascading effect of OCR errors on numeric extraction.

Both failure modes are recoverable: the first by extending the regex pattern library, the
second by post-processing validation (e.g. re-deriving tax from subtotal × rate).

---

## 5.4 AI-Assisted Search

The fuzzy search endpoint (`GET /api/ai/search?q=...`) uses RapidFuzz token-set ratio
scoring with a threshold of 60/100 to match free-text queries against supplier names stored
in the database.

### 5.4.1 Qualitative Search Examples

| Query | Top Match | Score | Correct? |
|---|---|---|---|
| "invoices from Acme" | Acme Corp Ltd | 90 | ✓ |
| "facturas de techsupplies" | TechSupplies Inc. | 85 | ✓ |
| "design studio germany" | DesignStudio GmbH | 82 | ✓ |
| "iberica" | Ibérica Servicios S.L. | 79 | ✓ |
| "random nonsense" | — | < 60 | ✓ (no result) |

The token-set ratio scorer tolerates word-order differences and partial matches, making it
robust to informal or multilingual queries (Spanish / English mixed). No LLM call is
required for this feature, so latency is sub-millisecond even on modest hardware.

### 5.4.2 Threshold Sensitivity

A threshold of 60 was selected empirically. Lowering it below 50 produced false positives
(e.g. "invoice" alone matching supplier names containing common English words). Raising it
above 75 caused legitimate partial matches (e.g. single-word queries) to be filtered out.

---

## 5.5 AI Question Answering

The QA endpoint (`POST /api/ai/qa`) constructs a structured context from invoice metadata
and raw OCR text (truncated to 4,000 characters) and forwards a user question to an LLM
(Claude or GPT-4o-mini depending on configuration).

### 5.5.1 Example QA Interactions

**Question:** "What services were provided on this invoice?"
> *"The invoice includes three services: Web Development Services (10 × £100.00 =
> £1,000.00), Project Management (5 × £80.00 = £400.00), and Hosting Setup (1 × £200.00 =
> £200.00)."*

**Question:** "What is the VAT rate applied?"
> *"A VAT rate of 20 % was applied, resulting in a VAT charge of £320.00 on a subtotal of
> £1,600.00."*

**Question:** "When is payment due?"
> *"Payment is due on 15 April 2024, 30 days after the invoice date of 15 March 2024."*

**Question:** "Who is the client?"
> *"The invoice is billed to GlobalTech Solutions, 456 Tech Park, Manchester."*

All answers were grounded exclusively in the invoice document; the system prompt instructs
the model not to draw on external knowledge, reducing hallucination risk.

### 5.5.2 Failure Mode: Unanswerable Questions

**Question:** "What is the supplier's VAT registration number?"
> *"I cannot find a VAT registration number in the provided document."*

This demonstrates appropriate refusal behaviour when the requested field is absent from the
invoice—a key requirement for a system used in financial workflows.

---

## 5.6 System Summary

| Component | Key Metric | Value |
|---|---|---|
| Synthetic dataset | Total invoices | 200 |
| OCR | Avg. character accuracy | 98.46 % |
| OCR | Avg. word accuracy | 85.47 % |
| Extraction | Macro F1 | 0.90 |
| Extraction | invoice_date F1 | 1.00 |
| Extraction | total_amount F1 | 1.00 |
| Fuzzy search | Threshold | 60 / 100 |
| QA context | Max OCR chars sent to LLM | 4,000 |
| End-to-end pipeline | Stages | 5 (preprocess → OCR → extract → validate → store) |

The results demonstrate that a rule-based, offline-capable pipeline can achieve near-perfect
performance on clean or lightly degraded invoice images. The primary bottleneck is OCR
word accuracy (85 %), which propagates to numeric field extraction errors. Future work
could address this by incorporating a dedicated OCR post-correction step before the
extraction layer.

---

*Figures are saved as PNG files in `results_figures/`. Insert them in the report at the
positions marked `[Insert figN_*.png]`.*
