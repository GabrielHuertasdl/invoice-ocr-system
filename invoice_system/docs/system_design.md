# System Design

## Goals and Constraints

The primary requirement is a **fully local** system: no external API calls, no cloud dependencies, and no paid services.  The design therefore favours open-source, pip-installable components that run on commodity hardware.

Secondary goals:
- Modular pipeline so that individual stages can be replaced independently.
- A REST API that supports both the React UI and standalone scripting.
- Persistence of all intermediate artefacts (raw OCR text, validation notes) for auditability.

---

## Key Design Decisions

### 1. Synchronous pipeline in the upload endpoint

**Decision**: The pipeline runs synchronously inside `POST /api/invoices/upload`.

**Rationale**: For a local, single-user system processing a small number of files at a time, synchronous execution is simpler to reason about, easier to debug, and avoids the operational overhead of a task queue.

**Trade-off**: Large PDFs (>10 pages) or batches of many files will block the HTTP response for several seconds.  If this becomes a problem, the `run_pipeline` function is already isolated so it can be moved to a background task (FastAPI `BackgroundTasks` or Celery) without changing any other code.

### 2. Rule-based extraction (regex)

**Decision**: Field extraction uses compiled regular expressions rather than a neural NLP model.

**Rationale**:
- Zero additional model downloads or GPU requirements.
- Predictable, auditable matching logic.
- Fast (sub-millisecond per invoice).
- Sufficient accuracy for well-structured invoices with standard layouts.

**Trade-off**: Regex patterns are brittle against unusual formatting, non-English invoices, or scans with heavy OCR noise.  Accuracy degrades for handwritten or image-heavy invoices.

**Extension path**: The `extract_fields(raw_text: str) -> dict` function in `services/extraction/extractor.py` is the single extraction interface.  It can be replaced with a call to a fine-tuned [LayoutLM](https://huggingface.co/microsoft/layoutlm-base-uncased) or [Donut](https://huggingface.co/naver-clova-ix/donut-base-finetuned-docvqa) model without touching any other module.

### 3. Tesseract as the OCR engine

**Decision**: pytesseract (Tesseract 4+) is the default OCR engine.

**Rationale**: Tesseract is mature, free, and produces good accuracy on clean, typed text.  The preprocessing step (grayscale, denoise, Otsu threshold) significantly improves results on scanned documents.

**Trade-off**: Tesseract struggles with complex multi-column layouts and handwriting.  For production-grade accuracy, [EasyOCR](https://github.com/JaidedAI/EasyOCR) or cloud OCR (Google Document AI, AWS Textract) would be more robust.

**Extension path**: Replace `services/ocr/tesseract_ocr.py` with an EasyOCR implementation that exposes the same `run_ocr(images: List[Image]) -> str` signature.

### 4. SQLite as the default database

**Decision**: SQLite is used by default via SQLAlchemy.

**Rationale**: Zero installation for the developer; the entire database is a single file.  SQLAlchemy abstracts the dialect so switching to PostgreSQL requires only changing `DATABASE_URL`.

**Trade-off**: SQLite does not support concurrent writes well.  A multi-worker deployment must use PostgreSQL.

### 5. Lenient validation (warnings, not hard failures)

**Decision**: Validation issues are stored as text in `validation_notes` rather than rejecting the invoice.

**Rationale**: OCR is imperfect.  Blocking an invoice due to a misread total would frustrate users.  Warnings surface issues without preventing storage, and the detail view allows manual correction via PUT.

---

## Current Limitations

| Area | Limitation |
|---|---|
| OCR accuracy | Handwritten text, very low-resolution scans, or non-Latin scripts are not reliably handled. |
| Extraction coverage | Only a subset of possible invoice layouts is covered by the current regex patterns.  Exotic formats (e.g. Japanese, Arabic right-to-left) are not supported. |
| Date normalisation | Dates are stored as extracted strings, not normalised to ISO 8601.  Comparison logic in validation handles the most common formats but may miss edge cases. |
| Concurrency | Single-process SQLite is not suitable for concurrent multi-user access. |
| Authentication | No user authentication or authorisation is implemented. |
| File storage | Uploaded files are stored in a local directory without size limits or cleanup. |

---

## Extension Roadmap

1. **Better OCR**: Swap Tesseract for EasyOCR or a cloud API via the `run_ocr` interface.
2. **ML extraction**: Replace regex with a LayoutLM fine-tuned on an invoice dataset via the `extract_fields` interface.
3. **Async processing**: Add Celery + Redis; upload endpoint returns immediately with `status=pending`.
4. **Authentication**: Add OAuth2/JWT via FastAPI's security utilities.
5. **Multi-currency**: Integrate an exchange-rate API for currency normalisation.
6. **Export**: Add `GET /api/invoices/export.csv` endpoint.
