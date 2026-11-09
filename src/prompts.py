"""Prompt builders for Groq-powered document analysis."""

from __future__ import annotations

from textwrap import dedent

from config import CONFIG

SUMMARY_TYPES = {
    "executive": "Executive Summary",
    "detailed": "Detailed Summary",
    "bullet": "Bullet Point Summary",
}


def build_analysis_prompt(document_text: str, document_name: str, summary_type: str) -> str:
    """Build a single structured prompt for the Groq model.

    The model is asked to return valid JSON so the app can safely save and
    render the content in Streamlit and the CLI.
    """

    readable_summary_type = SUMMARY_TYPES.get(summary_type, SUMMARY_TYPES["detailed"])

    return dedent(
        f"""
        You are SmartPDF AI, a professional study assistant for students.

        Analyze the PDF content below and return ONLY valid JSON.
        Do not include markdown fences, explanations, or extra text.

        Requirements:
        - Write clearly and professionally.
        - Base every answer on the provided document.
        - Keep the summary focused and useful for studying.
        - If the document is long, prioritize the most important ideas.
        - Use concise language for keywords and definitions.
        - Make interview questions practical and relevant.
        - Make MCQs challenging but fair.

        Output JSON keys:
        {{
            "title": "{document_name}",
            "summary_type": "{summary_type}",
            "selected_summary_label": "{readable_summary_type}",
            "executive_summary": "short executive overview",
            "detailed_summary": "full detailed explanation",
            "bullet_summary": ["bullet 1", "bullet 2", "bullet 3"],
            "summary": "the {readable_summary_type.lower()}",
            "key_points": ["point 1", "point 2"],
            "topics": ["topic 1", "topic 2"],
            "definitions": ["definition 1", "definition 2"],
            "keywords": ["keyword 1", "keyword 2"],
            "study_notes": ["note 1", "note 2"],
            "interview_questions": ["question 1", "question 2", "question 3", "question 4", "question 5"],
            "mcqs": [
                {{
                    "question": "MCQ question",
                    "options": ["A", "B", "C", "D"],
                    "answer": "correct answer",
                    "explanation": "short explanation"
                }}
            ],
            "study_tips": ["tip 1", "tip 2"],
            "suggestions": ["suggestion 1", "suggestion 2"]
        }}

        Document name: {document_name}
        Summary preference: {readable_summary_type}

        PDF text:
        {document_text}
        """
    ).strip()


def build_system_message() -> str:
    """Return the system instruction for the Groq chat request."""
    return dedent(
        f"""
        You are a careful AI assistant inside {CONFIG.app_name}.
        You extract insights from PDFs and return valid JSON only.
        """
    ).strip()
