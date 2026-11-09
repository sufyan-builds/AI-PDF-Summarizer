"""Text-to-speech helpers for SmartPDF AI."""

from __future__ import annotations

import pyttsx3

from src.logger import get_logger
from src.utils import SmartPDFError

logger = get_logger(__name__)


def read_summary_aloud(text: str, rate: int = 175) -> None:
    """Speak the provided summary using the local TTS engine."""
    cleaned_text = text.strip()
    if not cleaned_text:
        raise SmartPDFError("There is no summary text to read aloud.")

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.say(cleaned_text)
        engine.runAndWait()
    except Exception as exc:  # pragma: no cover - depends on local OS voice support
        logger.exception("Text-to-speech failed")
        raise SmartPDFError("Voice output is unavailable on this system.") from exc
