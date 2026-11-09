"""Export helpers for SmartPDF AI outputs."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from config import CONFIG
from src.logger import get_logger
from src.summarizer import AnalysisResult
from src.utils import safe_filename

logger = get_logger(__name__)


def build_output_stem(title: str, summary_type: str) -> str:
    """Build a stable base filename for exported files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = safe_filename(title)
    safe_summary_type = safe_filename(summary_type)
    return f"{safe_title}_{safe_summary_type}_{timestamp}"


def export_to_json(result: AnalysisResult, output_dir: Path | None = None) -> Path:
    """Save the full analysis as structured JSON."""
    target_dir = output_dir or CONFIG.output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / f"{build_output_stem(result.title, result.summary_type)}.json"
    file_path.write_text(
        json.dumps(result.to_dict(), indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Saved JSON export to %s", file_path)
    return file_path


def export_to_text(result: AnalysisResult, output_dir: Path | None = None) -> Path:
    """Save the analysis as a readable text report."""
    target_dir = output_dir or CONFIG.output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / f"{build_output_stem(result.title, result.summary_type)}.txt"
    file_path.write_text(_build_text_report(result), encoding="utf-8")
    logger.info("Saved TXT export to %s", file_path)
    return file_path


def export_to_markdown(result: AnalysisResult, output_dir: Path | None = None) -> Path:
    """Save the analysis as a Markdown report."""
    target_dir = output_dir or CONFIG.output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / f"{build_output_stem(result.title, result.summary_type)}.md"
    file_path.write_text(_build_markdown_report(result), encoding="utf-8")
    logger.info("Saved Markdown export to %s", file_path)
    return file_path


def export_all_formats(result: AnalysisResult, output_dir: Path | None = None) -> dict[str, Path]:
    """Export the result to TXT, JSON, and Markdown."""
    target_dir = output_dir or CONFIG.output_dir
    return {
        "txt": export_to_text(result, target_dir),
        "json": export_to_json(result, target_dir),
        "md": export_to_markdown(result, target_dir),
    }


def _build_text_report(result: AnalysisResult) -> str:
    lines = [
        f"Title: {result.title}",
        f"Summary Type: {result.summary_type}",
        f"Selected Summary Label: {result.selected_summary_label}",
        "",
        "Executive Summary",
        result.executive_summary or "No data available.",
        "",
        "Detailed Summary",
        result.detailed_summary or "No data available.",
        "",
        "Bullet Summary",
    ]

    lines.extend(f"- {item}" for item in result.bullet_summary or ["No data available."])
    lines.extend(["", "Key Points"])
    lines.extend(f"- {item}" for item in result.key_points or ["No data available."])
    lines.extend(["", "Topics"])
    lines.extend(f"- {item}" for item in result.topics or ["No data available."])
    lines.extend(["", "Definitions"])
    lines.extend(f"- {item}" for item in result.definitions or ["No data available."])
    lines.extend(["", "Keywords"])
    lines.extend(f"- {item}" for item in result.keywords or ["No data available."])
    lines.extend(["", "Study Notes"])
    lines.extend(f"- {item}" for item in result.study_notes or ["No data available."])
    lines.extend(["", "Interview Questions"])
    lines.extend(f"- {item}" for item in result.interview_questions or ["No data available."])
    lines.extend(["", "MCQs"])

    if result.mcqs:
        for index, mcq in enumerate(result.mcqs, start=1):
            lines.extend(
                [
                    f"{index}. {mcq.get('question', 'No question')}",
                    *[f"   - {option}" for option in mcq.get("options", [])],
                    f"   Answer: {mcq.get('answer', 'No answer')}",
                    f"   Explanation: {mcq.get('explanation', 'No explanation')}",
                    "",
                ]
            )
    else:
        lines.append("No data available.")

    lines.extend(["", "Study Tips"])
    lines.extend(f"- {item}" for item in result.study_tips or ["No data available."])
    lines.extend(["", "Suggestions"])
    lines.extend(f"- {item}" for item in result.suggestions or ["No data available."])
    lines.append("")

    return "\n".join(lines)


def _build_markdown_report(result: AnalysisResult) -> str:
    mcq_section: list[str] = []
    if result.mcqs:
        for index, mcq in enumerate(result.mcqs, start=1):
            mcq_section.extend(
                [
                    f"### MCQ {index}",
                    f"**Question:** {mcq.get('question', 'No question')}",
                    "",
                    "**Options:**",
                    *[f"- {option}" for option in mcq.get("options", [])],
                    f"**Answer:** {mcq.get('answer', 'No answer')}",
                    f"**Explanation:** {mcq.get('explanation', 'No explanation')}",
                    "",
                ]
            )
    else:
        mcq_section.append("No data available.")

    sections = [
        f"# {result.title}",
        f"**Summary Type:** {result.summary_type}",
        f"**Selected Summary Label:** {result.selected_summary_label}",
        "",
        "## Executive Summary",
        result.executive_summary or "No data available.",
        "",
        "## Detailed Summary",
        result.detailed_summary or "No data available.",
        "",
        "## Bullet Summary",
    ]

    sections.extend(f"- {item}" for item in result.bullet_summary or ["No data available."])
    sections.extend(["", "## Key Points"])
    sections.extend(f"- {item}" for item in result.key_points or ["No data available."])
    sections.extend(["", "## Topics"])
    sections.extend(f"- {item}" for item in result.topics or ["No data available."])
    sections.extend(["", "## Definitions"])
    sections.extend(f"- {item}" for item in result.definitions or ["No data available."])
    sections.extend(["", "## Keywords"])
    sections.extend(f"- {item}" for item in result.keywords or ["No data available."])
    sections.extend(["", "## Study Notes"])
    sections.extend(f"- {item}" for item in result.study_notes or ["No data available."])
    sections.extend(["", "## Interview Questions"])
    sections.extend(f"- {item}" for item in result.interview_questions or ["No data available."])
    sections.extend(["", "## MCQs"])
    sections.extend(mcq_section)
    sections.extend(["## Study Tips"])
    sections.extend(f"- {item}" for item in result.study_tips or ["No data available."])
    sections.extend(["", "## Suggestions"])
    sections.extend(f"- {item}" for item in result.suggestions or ["No data available."])
    sections.append("")

    return "\n".join(sections)
