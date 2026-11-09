"""PDF extraction utilities for SmartPDF AI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from src.logger import get_logger
from src.utils import DocumentInfo, PDFProcessingError, clean_text, count_words

logger = get_logger(__name__)


@dataclass(frozen=True)
class ExtractedPDF:
    """Structured PDF content and metadata."""

    info: DocumentInfo
    text: str


def extract_pdf_text(pdf_path: str | Path) -> ExtractedPDF:
    """Read a PDF file and return its text and basic statistics."""
    file_path = Path(pdf_path).expanduser().resolve()

    if not file_path.exists():
        raise PDFProcessingError(f"PDF file not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise PDFProcessingError("Please choose a valid PDF file.")

    logger.info("Reading PDF: %s", file_path)

    try:
        with fitz.open(file_path) as document:
            if document.is_encrypted:
                raise PDFProcessingError("This PDF is encrypted and cannot be opened.")

            page_count = document.page_count
            if page_count == 0:
                raise PDFProcessingError("The PDF appears to be empty.")

            page_texts: list[str] = []
            for page in document:
                page_text = clean_text(page.get_text("text"))
                if page_text:
                    page_texts.append(page_text)

    except fitz.FileDataError as exc:
        logger.exception("Invalid or corrupted PDF: %s", file_path)
        raise PDFProcessingError("The selected file is not a valid or readable PDF.") from exc
    except fitz.PyMuPDFError as exc:
        logger.exception("PyMuPDF failed while reading: %s", file_path)
        raise PDFProcessingError("Failed to read the PDF file.") from exc
    except OSError as exc:
        logger.exception("OS error while reading PDF: %s", file_path)
        raise PDFProcessingError("Could not access the PDF file.") from exc

    text = clean_text("\n\n".join(page_texts))
    if not text:
        raise PDFProcessingError(
            "No extractable text was found. The PDF may be empty or image-based."
        )

    info = DocumentInfo(
        file_name=file_path.name,
        file_path=file_path,
        page_count=page_count,
        word_count=count_words(text),
    )

    return ExtractedPDF(info=info, text=text)
