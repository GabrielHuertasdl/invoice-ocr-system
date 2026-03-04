"""
Image preprocessing pipeline.

Converts PDFs to images and applies enhancements (grayscale, denoise,
threshold) that improve Tesseract accuracy on invoice scans.
"""

from pathlib import Path
from typing import List
from PIL import Image
import cv2
import numpy as np


def _enhance_image(img: Image.Image) -> Image.Image:
    """
    Apply grayscale conversion, denoising, and Otsu thresholding to an image.
    Returns an enhanced PIL Image suitable for OCR.
    """
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


def _pdf_to_images(pdf_path: Path) -> List[Image.Image]:
    """Convert a PDF file to a list of PIL Images (one per page)."""
    try:
        from pdf2image import convert_from_path
        return convert_from_path(str(pdf_path), dpi=300)
    except Exception as exc:
        raise RuntimeError(f"Failed to convert PDF '{pdf_path}': {exc}") from exc


def prepare_images(file_path: Path) -> List[Image.Image]:
    """
    Given a file path (PDF or image), return a list of enhanced PIL Images
    ready for OCR processing.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        raw_images = _pdf_to_images(file_path)
    else:
        raw_images = [Image.open(file_path)]

    return [_enhance_image(img) for img in raw_images]
