"""Command-line interface for SmartPDF AI."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from config import CONFIG, SUMMARY_TYPES, ensure_project_directories
from src.exporter import export_to_json, export_to_text
from src.logger import get_logger
from src.pdf_reader import extract_pdf_text
from src.summarizer import generate_analysis
from src.utils import APICallError, ConfigurationError, PDFProcessingError, SmartPDFError

load_dotenv()
ensure_project_directories()
logger = get_logger(__name__)
console = Console()


def _print_header() -> None:
    """Show a simple professional banner."""
    console.print(
        Panel.fit(
            "[bold cyan]SmartPDF AI[/bold cyan]\nAI-Powered PDF Summarizer & Study Assistant",
            border_style="cyan",
        )
    )


def _ask_for_pdf_path() -> Path:
    """Prompt the user for a PDF file path."""
    while True:
        path_input = Prompt.ask("Enter the full path to a PDF file")
        pdf_path = Path(path_input).expanduser().resolve()
        if pdf_path.exists() and pdf_path.suffix.lower() == ".pdf":
            return pdf_path
        console.print("[red]Please enter a valid PDF file path.[/red]")


def _ask_for_summary_type() -> str:
    """Prompt the user for a summary style."""
    options = list(SUMMARY_TYPES)
    choice = Prompt.ask(
        "Choose a summary type",
        choices=options,
        default="detailed",
    )
    return choice


def _display_document_stats(file_name: str, page_count: int, word_count: int, summary_type: str) -> None:
    """Show extracted document information in a clean table."""
    table = Table(title="Document Overview", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value", style="white")
    table.add_row("File Name", file_name)
    table.add_row("Pages", str(page_count))
    table.add_row("Word Count", f"{word_count:,}")
    table.add_row("Summary Type", summary_type.title())
    table.add_row("AI Model", CONFIG.groq_model)
    console.print(table)


def _display_analysis(analysis) -> None:
    """Print the AI output in a readable format."""
    console.print(Panel(analysis.executive_summary or "No executive summary available.", title="Executive Summary", border_style="green"))
    console.print(Panel(analysis.detailed_summary or "No detailed summary available.", title="Detailed Summary", border_style="blue"))

    if analysis.bullet_summary:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.bullet_summary), title="Bullet Summary", border_style="magenta"))

    if analysis.key_points:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.key_points), title="Key Points", border_style="yellow"))

    if analysis.topics:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.topics), title="Important Topics", border_style="cyan"))

    if analysis.definitions:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.definitions), title="Important Definitions", border_style="cyan"))

    if analysis.keywords:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.keywords), title="Keywords", border_style="cyan"))

    if analysis.study_notes:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.study_notes), title="Study Notes", border_style="green"))

    if analysis.interview_questions:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.interview_questions), title="Interview Questions", border_style="bright_blue"))

    if analysis.mcqs:
        mcq_table = Table(title="MCQs", show_lines=True)
        mcq_table.add_column("#", style="bold cyan", width=4)
        mcq_table.add_column("Question", style="white")
        mcq_table.add_column("Answer", style="green")
        for index, mcq in enumerate(analysis.mcqs, start=1):
            question = mcq.get("question", "No question")
            answer = mcq.get("answer", "No answer")
            mcq_table.add_row(str(index), question, answer)
        console.print(mcq_table)

    if analysis.study_tips:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.study_tips), title="Study Tips", border_style="magenta"))

    if analysis.suggestions:
        console.print(Panel("\n".join(f"- {item}" for item in analysis.suggestions), title="Suggestions", border_style="red"))

    console.print(Panel(Markdown(analysis.summary or analysis.executive_summary or "No summary available."), title="Selected Summary", border_style="cyan"))


def main() -> None:
    """Run the CLI workflow."""
    _print_header()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        console.print("[red]Missing GROQ_API_KEY. Add it to your environment or .env file.[/red]")
        return

    pdf_path = _ask_for_pdf_path()
    summary_type = _ask_for_summary_type()

    try:
        extracted_pdf = extract_pdf_text(pdf_path)
        _display_document_stats(
            file_name=extracted_pdf.info.file_name,
            page_count=extracted_pdf.info.page_count,
            word_count=extracted_pdf.info.word_count,
            summary_type=summary_type,
        )

        console.print("[cyan]Generating AI analysis...[/cyan]")
        analysis = generate_analysis(
            document_text=extracted_pdf.text,
            document_name=extracted_pdf.info.file_name,
            summary_type=summary_type,
            api_key=api_key,
        )

        _display_analysis(analysis)

        txt_path = export_to_text(analysis)
        json_path = export_to_json(analysis)
        console.print(f"[green]Saved TXT:[/green] {txt_path}")
        console.print(f"[green]Saved JSON:[/green] {json_path}")
        console.print("[bold green]Analysis complete.[/bold green]")

    except (PDFProcessingError, ConfigurationError, APICallError, SmartPDFError) as exc:
        console.print(f"[red]{exc}[/red]")
        logger.exception("CLI error")
    except Exception:
        console.print("[red]An unexpected error occurred while processing the PDF.[/red]")
        logger.exception("Unexpected CLI error")


if __name__ == "__main__":
    main()
