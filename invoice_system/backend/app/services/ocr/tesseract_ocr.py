"""
Tesseract OCR wrapper.

Runs pytesseract on one or more pre-processed PIL Images and joins the
resulting text pages with a page separator.
"""

from typing import List
from PIL import Image
import pytesseract
from app.config import settings

# Allow override of Tesseract binary path via env
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

# Custom config: page segmentation mode 6 (assume a single uniform block of text)
_TESS_CONFIG = r"--oem 3 --psm 6"


def run_ocr(images: List[Image.Image]) -> str:
    """
    Extract text from a list of PIL Images using Tesseract.

    Pages are joined with a newline separator.  Returns the combined raw
    text string.
    """
    page_texts: List[str] = []
    for img in images:
        text = pytesseract.image_to_string(img, config=_TESS_CONFIG, lang="eng")
        page_texts.append(text)
    return "\n--- PAGE BREAK ---\n".join(page_texts)
