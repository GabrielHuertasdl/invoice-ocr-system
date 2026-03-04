"""File ingestion utilities: validation and persistence of uploaded files."""

import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def validate_file_type(filename: str) -> None:
    """Raise HTTP 400 if the file extension is not supported."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {ALLOWED_EXTENSIONS}",
        )


def save_upload(upload: UploadFile, upload_dir: str) -> Path:
    """
    Persist an uploaded file to disk under a UUID-based name.

    Returns the absolute path of the saved file.
    """
    suffix = Path(upload.filename).suffix.lower()
    dest_name = f"{uuid.uuid4().hex}{suffix}"
    dest_path = Path(upload_dir) / dest_name
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("wb") as fh:
        shutil.copyfileobj(upload.file, fh)
    return dest_path
