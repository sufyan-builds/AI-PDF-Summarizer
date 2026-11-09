# SmartPDF AI

SmartPDF AI is a beginner-friendly, production-style Python application that turns any PDF into useful summaries, study notes, interview questions, MCQs, and downloadable study material using the Groq API.

The project includes both a modern Streamlit dashboard and a Rich-based command-line interface.

## Project Overview

This app is designed to help students and professionals quickly understand long PDFs such as:

- Books
- Lecture notes
- Research papers
- Assignments
- Reports
- Documentation
- Manuals

It extracts text with PyMuPDF, sends the content to Groq for analysis, and returns structured JSON that can be saved as TXT, JSON, or Markdown.

## Features

- PDF upload from any location on your computer
- PDF text extraction with page count and word count
- AI-generated executive, detailed, and bullet summaries
- Study assistant content:
  - Key points
  - Important topics
  - Important definitions
  - Keywords
  - Study notes
  - 5 interview questions
  - 5 MCQs with answers
  - Study tips
  - Actionable suggestions
- Voice output with `pyttsx3`
- Export to TXT, JSON, and Markdown
- Beautiful dark-themed Streamlit dashboard
- CLI version with Rich formatting
- Logging and user-friendly error handling

## Installation

### 1. Clone or open the project

```bash
cd AI-PDF-Summarizer
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Create a `.env` file in the project root and add:

```env
GROQ_API_KEY=your_groq_api_key_here
```

You can also start from `.env.example`.

## Requirements

- Python 3.12+
- Groq API account and API key
- Internet connection for AI analysis
- Windows/macOS/Linux with text-to-speech support for `pyttsx3`

## Folder Structure

```text
SmartPDF-AI/
├── app.py
├── cli.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── outputs/
├── logs/
└── src/
    ├── pdf_reader.py
    ├── summarizer.py
    ├── prompts.py
    ├── exporter.py
    ├── voice.py
    ├── utils.py
    └── logger.py
```

## How to Run

### Streamlit app

```bash
streamlit run app.py
```

### CLI app

```bash
python cli.py
```

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `GROQ_API_KEY` | Required for Groq AI analysis |

## Output Files

Generated files are saved in the `outputs/` folder:

- TXT report
- JSON report
- Markdown report

Logs are written to the `logs/` folder.

## Screenshots

Add screenshots of the Streamlit dashboard here after running the app.

Suggested screenshots:

- Homepage
- Uploaded PDF dashboard view
- Summary output sections
- Download buttons

## Future Improvements

- Add PDF page preview
- Support OCR for image-based PDFs
- Add a chat-style follow-up assistant
- Add theme toggle for light and dark modes
- Add batch processing for multiple PDFs

## License

MIT License

## Notes

- If a PDF has no extractable text, the app will show a friendly error.
- The voice feature reads the generated summary aloud using the local system TTS engine.
- The CLI saves TXT and JSON outputs automatically after analysis.
