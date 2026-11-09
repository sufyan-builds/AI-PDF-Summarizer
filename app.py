"""Streamlit application for SmartPDF AI."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from config import CONFIG, SUMMARY_TYPES, ensure_project_directories
from src.exporter import export_all_formats
from src.logger import get_logger
from src.pdf_reader import ExtractedPDF, extract_pdf_text
from src.summarizer import AnalysisResult, generate_analysis
from src.utils import APICallError, ConfigurationError, PDFProcessingError, SmartPDFError
from src.voice import read_summary_aloud

load_dotenv()
ensure_project_directories()
logger = get_logger(__name__)

st.set_page_config(
    page_title=f"{CONFIG.app_name} | AI PDF Summarizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_styles() -> None:
    """Apply a polished dark theme to the Streamlit app."""
    st.markdown(
        """
        <style>
            :root {
                --bg-primary: #0b1120;
                --bg-secondary: #111827;
                --bg-tertiary: #1f2937;
                --text-primary: #f9fafb;
                --text-secondary: #cbd5e1;
                --accent: #7c3aed;
                --accent-2: #06b6d4;
                --border: rgba(148, 163, 184, 0.18);
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(124, 58, 237, 0.18), transparent 28%),
                    radial-gradient(circle at top right, rgba(6, 182, 212, 0.14), transparent 24%),
                    linear-gradient(180deg, #050816 0%, #0b1120 100%);
                color: var(--text-primary);
            }

            .hero {
                padding: 2rem;
                border: 1px solid var(--border);
                border-radius: 28px;
                background: linear-gradient(135deg, rgba(17, 24, 39, 0.94), rgba(15, 23, 42, 0.82));
                box-shadow: 0 24px 80px rgba(0, 0, 0, 0.25);
            }

            .hero h1 {
                margin: 0;
                font-size: 3rem;
                line-height: 1.1;
                color: var(--text-primary);
            }

            .hero p {
                margin-top: 0.75rem;
                color: var(--text-secondary);
                font-size: 1.05rem;
            }

            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 1rem;
                margin-top: 1.5rem;
            }

            .feature-card,
            .metric-card,
            .glass-card {
                border: 1px solid var(--border);
                border-radius: 22px;
                background: rgba(17, 24, 39, 0.78);
                backdrop-filter: blur(10px);
                box-shadow: 0 16px 50px rgba(0, 0, 0, 0.18);
            }

            .feature-card {
                padding: 1rem;
                min-height: 120px;
            }

            .feature-card h3 {
                margin: 0 0 0.5rem 0;
                font-size: 1rem;
                color: #ffffff;
            }

            .feature-card p {
                margin: 0;
                color: var(--text-secondary);
                font-size: 0.95rem;
            }

            .metric-card {
                padding: 1rem 1.1rem;
            }

            .metric-label {
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--text-secondary);
            }

            .metric-value {
                font-size: 1.6rem;
                font-weight: 700;
                margin-top: 0.35rem;
                color: #ffffff;
            }

            .section-title {
                font-size: 1.5rem;
                font-weight: 700;
                margin: 0 0 0.5rem 0;
                color: #ffffff;
            }

            .stSidebar {
                background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
            }

            .stButton > button,
            .stDownloadButton > button {
                border-radius: 999px;
                border: 1px solid rgba(124, 58, 237, 0.35);
                background: linear-gradient(135deg, #7c3aed, #06b6d4);
                color: white;
                padding: 0.65rem 1.1rem;
                font-weight: 600;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 12px 28px rgba(124, 58, 237, 0.28);
            }

            .stTextInput input,
            .stSelectbox div[data-baseweb="select"] > div,
            .stFileUploader {
                border-radius: 16px;
            }

            .stExpander {
                border-radius: 20px;
                border: 1px solid var(--border);
                background: rgba(15, 23, 42, 0.7);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_homepage() -> None:
    """Show the marketing-style landing area."""
    st.markdown(
        f"""
        <div class="hero">
            <h1>SmartPDF AI</h1>
            <p>Upload any PDF, extract the important ideas, and turn it into clean summaries, study notes, interview prep, and downloadable study material.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    feature_columns = st.columns(3)
    features = [
        ("AI Summary", "Executive, detailed, and bullet summaries for fast revision."),
        ("Study Assistant", "Key points, definitions, questions, MCQs, and study tips."),
        ("Export & Voice", "Download TXT, JSON, Markdown, or listen to the summary."),
    ]

    for column, (title, description) in zip(feature_columns, features, strict=False):
        with column:
            st.markdown(
                f"""
                <div class="feature-card">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_sidebar() -> str:
    """Render the sidebar controls and return the selected summary type."""
    st.sidebar.title("SmartPDF AI")
    st.sidebar.caption(f"Version {CONFIG.version}")
    st.sidebar.markdown("---")

    summary_type = st.sidebar.selectbox(
        "Summary Type",
        options=list(SUMMARY_TYPES),
        index=1,
        help="Choose the summary style shown in the main summary section.",
    )

    st.sidebar.info(
        f"Model: {CONFIG.groq_model}\n\nTemperature: {CONFIG.temperature}\n\nMax Tokens: {CONFIG.max_tokens}"
    )

    api_key_present = bool(os.getenv("GROQ_API_KEY"))
    if api_key_present:
        st.sidebar.success("Groq API key detected")
    else:
        st.sidebar.warning("Missing GROQ_API_KEY in your environment")

    st.sidebar.markdown("---")
    st.sidebar.caption("Supported PDFs: books, lecture notes, research papers, reports, and assignments.")
    return summary_type


def _save_uploaded_pdf(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> Path:
    """Store the uploaded file in a temporary PDF on disk."""
    suffix = Path(uploaded_file.name).suffix or ".pdf"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_file.name)
    temp_file.write(uploaded_file.getvalue())
    temp_file.close()
    return temp_path


def _render_metrics(pdf_data: ExtractedPDF, analysis: AnalysisResult) -> None:
    """Show high-level dashboard cards."""
    metric_columns = st.columns(4)
    metrics = [
        ("Pages", str(pdf_data.info.page_count)),
        ("Word Count", f"{pdf_data.info.word_count:,}"),
        ("Summary Type", analysis.summary_type.title()),
        ("AI Model", CONFIG.groq_model),
    ]

    for column, (label, value) in zip(metric_columns, metrics, strict=False):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_download_buttons(export_paths: dict[str, Path]) -> None:
    """Render download buttons for exported files."""
    button_columns = st.columns(3)
    labels = [("TXT", "txt", "text/plain"), ("JSON", "json", "application/json"), ("Markdown", "md", "text/markdown")]

    for column, (label, key, mime_type) in zip(button_columns, labels, strict=False):
        with column:
            file_path = export_paths.get(key)
            if file_path and file_path.exists():
                st.download_button(
                    label=f"Download {label}",
                    data=file_path.read_bytes(),
                    file_name=file_path.name,
                    mime=mime_type,
                    use_container_width=True,
                )


def _render_result(pdf_data: ExtractedPDF, analysis: AnalysisResult, export_paths: dict[str, Path]) -> None:
    """Render the analysis results in expandable dashboard sections."""
    _render_metrics(pdf_data, analysis)
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    summary_columns = st.columns([2, 1])
    with summary_columns[0]:
        st.markdown("<div class='section-title'>Summary Preview</div>", unsafe_allow_html=True)
        st.markdown(analysis.summary or analysis.executive_summary or "No summary available.")
    with summary_columns[1]:
        st.markdown("<div class='section-title'>Document Details</div>", unsafe_allow_html=True)
        st.write(f"**File:** {pdf_data.info.file_name}")
        st.write(f"**Pages:** {pdf_data.info.page_count}")
        st.write(f"**Words:** {pdf_data.info.word_count:,}")
        st.write(f"**Summary Type:** {analysis.summary_type.title()}")
        st.write(f"**AI Model:** {CONFIG.groq_model}")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    if st.button("Read Summary", use_container_width=False):
        try:
            read_summary_aloud(analysis.summary or analysis.executive_summary)
            st.success("Summary read aloud successfully.")
        except SmartPDFError as exc:
            st.error(str(exc))
            logger.exception("Voice output failed")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    _render_download_buttons(export_paths)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    with st.expander("Executive Summary", expanded=True):
        st.write(analysis.executive_summary or "No executive summary available.")

    with st.expander("Detailed Summary"):
        st.write(analysis.detailed_summary or "No detailed summary available.")

    with st.expander("Bullet Summary"):
        st.markdown("\n".join(f"- {item}" for item in analysis.bullet_summary) or "No bullet summary available.")

    with st.expander("Study Assistant"):
        assistant_columns = st.columns(2)
        with assistant_columns[0]:
            st.subheader("Key Points")
            st.markdown("\n".join(f"- {item}" for item in analysis.key_points) or "No key points available.")
            st.subheader("Topics")
            st.markdown("\n".join(f"- {item}" for item in analysis.topics) or "No topics available.")
            st.subheader("Definitions")
            st.markdown("\n".join(f"- {item}" for item in analysis.definitions) or "No definitions available.")
        with assistant_columns[1]:
            st.subheader("Keywords")
            st.markdown("\n".join(f"- {item}" for item in analysis.keywords) or "No keywords available.")
            st.subheader("Study Notes")
            st.markdown("\n".join(f"- {item}" for item in analysis.study_notes) or "No study notes available.")
            st.subheader("Study Tips")
            st.markdown("\n".join(f"- {item}" for item in analysis.study_tips) or "No study tips available.")

    with st.expander("Interview Questions"):
        st.markdown("\n".join(f"- {item}" for item in analysis.interview_questions) or "No interview questions available.")

    with st.expander("MCQs with Answers"):
        if analysis.mcqs:
            for index, mcq in enumerate(analysis.mcqs, start=1):
                st.markdown(f"**{index}. {mcq.get('question', 'No question')}**")
                for option in mcq.get("options", []):
                    st.markdown(f"- {option}")
                st.caption(f"Answer: {mcq.get('answer', 'No answer')}")
                st.caption(f"Explanation: {mcq.get('explanation', 'No explanation')}")
                st.markdown("---")
        else:
            st.write("No MCQs available.")

    with st.expander("Actionable Suggestions"):
        st.markdown("\n".join(f"- {item}" for item in analysis.suggestions) or "No suggestions available.")

    with st.expander("Structured JSON Preview"):
        st.json(analysis.to_dict())


def main() -> None:
    """Run the Streamlit app."""
    _inject_styles()
    summary_type = _render_sidebar()

    st.markdown(
        f"""
        <div style="margin-bottom: 1rem;">
            <p style="color: #cbd5e1; margin-bottom: 0.25rem;">AI-Powered PDF Summarizer & Study Assistant</p>
            <h2 style="color: white; margin-top: 0;">Turn any PDF into summaries, study notes, and interview prep.</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    if not uploaded_file:
        _render_homepage()
        return

    temp_pdf_path: Path | None = None
    try:
        temp_pdf_path = _save_uploaded_pdf(uploaded_file)
        pdf_data = extract_pdf_text(temp_pdf_path)

        st.success(f"Loaded {pdf_data.info.file_name} successfully.")
        st.write(f"Extracted {pdf_data.info.word_count:,} words from {pdf_data.info.page_count} pages.")

        analyze_clicked = st.button("Generate AI Analysis", use_container_width=True)
        if analyze_clicked:
            progress_bar = st.progress(0)
            progress_bar.progress(15)
            with st.spinner("Analyzing document with Groq..."):
                progress_bar.progress(35)
                analysis = generate_analysis(
                    document_text=pdf_data.text,
                    document_name=pdf_data.info.file_name,
                    summary_type=summary_type,
                )
                progress_bar.progress(80)
                export_paths = export_all_formats(analysis)
                progress_bar.progress(100)

            st.session_state["pdf_data"] = pdf_data
            st.session_state["analysis"] = analysis
            st.session_state["export_paths"] = {key: str(path) for key, path in export_paths.items()}
            st.success("Analysis complete. Files saved to the outputs folder.")

        if "analysis" in st.session_state and "pdf_data" in st.session_state:
            stored_pdf_data = st.session_state["pdf_data"]
            stored_analysis = st.session_state["analysis"]
            stored_paths = {
                key: Path(value) for key, value in st.session_state.get("export_paths", {}).items()
            }
            _render_result(stored_pdf_data, stored_analysis, stored_paths)

    except (PDFProcessingError, ConfigurationError, APICallError, SmartPDFError) as exc:
        st.error(str(exc))
        logger.exception("Application error")
    except Exception as exc:  # pragma: no cover - defensive catch for UI runtime issues
        st.error("An unexpected error occurred while processing the PDF.")
        logger.exception("Unexpected Streamlit error")
    finally:
        if temp_pdf_path and temp_pdf_path.exists():
            try:
                temp_pdf_path.unlink()
            except OSError:
                logger.warning("Could not remove temp file: %s", temp_pdf_path)


if __name__ == "__main__":
    main()
