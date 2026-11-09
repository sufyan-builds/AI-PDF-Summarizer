"""Groq-powered analysis for SmartPDF AI."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from groq import Groq

from config import CONFIG
from src.logger import get_logger
from src.prompts import build_analysis_prompt, build_system_message
from src.utils import APICallError, ConfigurationError, unique_items

logger = get_logger(__name__)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


@dataclass(slots=True)
class AnalysisResult:
    """Structured analysis returned by the AI model."""

    title: str
    summary_type: str
    selected_summary_label: str
    executive_summary: str
    detailed_summary: str
    bullet_summary: list[str]
    summary: str
    key_points: list[str]
    topics: list[str]
    definitions: list[str]
    keywords: list[str]
    study_notes: list[str]
    interview_questions: list[str]
    mcqs: list[dict[str, Any]]
    study_tips: list[str]
    suggestions: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return {
            "title": self.title,
            "summary_type": self.summary_type,
            "selected_summary_label": self.selected_summary_label,
            "executive_summary": self.executive_summary,
            "detailed_summary": self.detailed_summary,
            "bullet_summary": self.bullet_summary,
            "summary": self.summary,
            "key_points": self.key_points,
            "topics": self.topics,
            "definitions": self.definitions,
            "keywords": self.keywords,
            "study_notes": self.study_notes,
            "interview_questions": self.interview_questions,
            "mcqs": self.mcqs,
            "study_tips": self.study_tips,
            "suggestions": self.suggestions,
        }


def generate_analysis(
    document_text: str,
    document_name: str,
    summary_type: str,
    api_key: str | None = None,
) -> AnalysisResult:
    """Generate a structured document analysis using Groq."""
    resolved_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not resolved_api_key:
        raise ConfigurationError("Missing GROQ_API_KEY. Add it to your .env file.")

    if not document_text.strip():
        raise ConfigurationError("Cannot summarize empty document text.")

    logger.info("Generating analysis for %s with summary type %s", document_name, summary_type)

    try:
        client = Groq(api_key=resolved_api_key)
        response = client.chat.completions.create(
            model=CONFIG.groq_model,
            messages=[
                {"role": "system", "content": build_system_message()},
                {
                    "role": "user",
                    "content": build_analysis_prompt(document_text, document_name, summary_type),
                },
            ],
            temperature=CONFIG.temperature,
            max_completion_tokens=CONFIG.max_tokens,
            response_format={"type": "json_object"},  # Force JSON mode output
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Groq request failed")
        # Expose the specific error message to assist debugging
        raise APICallError(f"Groq API call failed: {exc}") from exc

    raw_content = getattr(response.choices[0].message, "content", "") if response.choices else ""
    parsed_payload = _parse_json_payload(raw_content)
    return _build_analysis_result(parsed_payload, document_name, summary_type)


def _parse_json_payload(raw_content: str) -> dict[str, Any]:
    """Parse a JSON payload from the model response."""
    if not raw_content.strip():
        raise APICallError("The AI response was empty.")

    stripped_content = raw_content.strip()
    fence_match = _JSON_FENCE_RE.match(stripped_content)
    if fence_match:
        stripped_content = fence_match.group(1).strip()

    try:
        parsed = json.loads(stripped_content)
    except json.JSONDecodeError as exc:
        logger.exception("Failed to parse Groq JSON response")
        raise APICallError("The AI returned invalid JSON format.") from exc

    if not isinstance(parsed, dict):
        raise APICallError("The AI response must be a JSON object.")

    return parsed


def _build_analysis_result(
    payload: dict[str, Any],
    document_name: str,
    summary_type: str,
) -> AnalysisResult:
    """Normalize the AI payload into a stable dataclass."""

    def as_string(value: Any, fallback: str = "") -> str:
        if isinstance(value, str):
            return value.strip()
        if value is None:
            return fallback
        return str(value).strip()

    def as_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return unique_items(as_string(item) for item in value if as_string(item))
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def as_mcq_list(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        mcqs: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            mcqs.append(
                {
                    "question": as_string(item.get("question")),
                    "options": as_list(item.get("options")),
                    "answer": as_string(item.get("answer")),
                    "explanation": as_string(item.get("explanation")),
                }
            )
        return mcqs

    bullet_summary = as_list(payload.get("bullet_summary"))
    selected_summary = as_string(payload.get("summary"))
    if not selected_summary and bullet_summary:
        selected_summary = "\n".join(f"- {item}" for item in bullet_summary)

    title = as_string(payload.get("title"), document_name) or document_name

    return AnalysisResult(
        title=title,
        summary_type=as_string(payload.get("summary_type"), summary_type) or summary_type,
        selected_summary_label=as_string(
            payload.get("selected_summary_label"),
            payload.get("summary_type", summary_type),
        ),
        executive_summary=as_string(payload.get("executive_summary")),
        detailed_summary=as_string(payload.get("detailed_summary")),
        bullet_summary=bullet_summary,
        summary=selected_summary,
        key_points=as_list(payload.get("key_points")),
        topics=as_list(payload.get("topics")),
        definitions=as_list(payload.get("definitions")),
        keywords=as_list(payload.get("keywords")),
        study_notes=as_list(payload.get("study_notes")),
        interview_questions=as_list(payload.get("interview_questions")),
        mcqs=as_mcq_list(payload.get("mcqs")),
        study_tips=as_list(payload.get("study_tips")),
        suggestions=as_list(payload.get("suggestions")),
    )