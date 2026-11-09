"""Shared utility helpers for SmartPDF AI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class SmartPDFError(Exception):
    """Base exception for application-specific errors."""


class ConfigurationError(SmartPDFError):
    """Raised when required configuration is missing or invalid."""


class PDFProcessingError(SmartPDFError):
    """Raised when a PDF cannot be read or processed."""


class APICallError(SmartPDFError):
    """Raised when the AI API returns an error."""


@dataclass(frozen=True)
class DocumentInfo:
    """Basic document statistics extracted from a PDF."""

    file_name: str
    file_path: Path
    page_count: int
    word_count: int


_WHITESPACE_RE = re.compile(r"\s+")
_INVALID_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def clean_text(text: str) -> str:
    """Normalize whitespace and remove obvious noise from extracted text."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def count_words(text: str) -> int:
    """Return a simple word count for a block of text."""
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return 0
    return len(cleaned_text.split(" "))


def has_text(text: str) -> bool:
    """Check whether text contains meaningful content."""
    return bool(clean_text(text))


def chunk_text(text: str, max_chunk_size: int = 6000) -> list[str]:
    """Split long text into chunks that fit comfortably in a prompt."""
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return []

    words = cleaned_text.split(" ")
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for word in words:
        projected_length = current_length + len(word) + (1 if current_chunk else 0)
        if current_chunk and projected_length > max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length = projected_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def safe_filename(value: str) -> str:
    """Convert an arbitrary string into a filesystem-safe filename."""
    cleaned_value = _INVALID_FILENAME_RE.sub("_", value).strip("._-")
    return cleaned_value or "smartpdf_output"


def unique_items(items: Iterable[str]) -> list[str]:
    """Return items in their original order without duplicates."""
    seen: set[str] = set()
    unique_list: list[str] = []

    for item in items:
        normalized_item = item.strip()
        if normalized_item and normalized_item not in seen:
            seen.add(normalized_item)
            unique_list.append(normalized_item)

    return unique_list
