# RAG Application Starter (`rag-app-starter`)

Team repository for the RAG (Retrieval-Augmented Generation) application data product project.

This project provides the foundation and structure for building a Retrieval-Augmented Generation pipeline using document extraction, vector indexing (ChromaDB), and LLM integration (OpenAI).

---

## Features & Implementation

### Multi-Format Document Loader (`src/document_loader.py`)
Parses heterogeneous source document formats into a common plain-text representation tagged with source metadata identity and robust exception handling.

- **Supported Formats**: PDF (`.pdf`), HTML (`.html`, `.htm`), Markdown (`.md`, `.markdown`), and Plain Text (`.txt`).
- **Graceful Failure Handling**: Survives missing files (`FileNotFoundError`), corrupt binary PDFs (`PdfReadError`), and unsupported extensions (`.docx`, `.xyz`) with explicit status logging and clear warnings instead of crashing.
- **Source Identity Preservation**: Attaches source file path, filename, format, word/character counts, and format-specific metadata to every extracted document.
- **Intake Confirmation**: Prints formatted text character length, word count, status summary, and sample text previews.
- **Sample Corpus**: Includes a pre-populated test corpus in `data/sample_corpus/` featuring valid documents alongside corrupt and unsupported test files.

---

## Prerequisites

- **Python**: Version 3.10 or higher
- **pip**: Package installer for Python
- **Git**: Version control system

---

## Workspace Setup Instructions

### 1. Create Virtual Environment

Create an isolated Python virtual environment named `.venv`:

**Windows (PowerShell / Command Prompt):**
```powershell
python -m venv .venv
```

**Linux / macOS:**
```bash
python3 -m venv .venv
```

### 2. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.\.venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

Install the pinned dependencies into the active virtual environment:

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

### 4. Create `.env` file

Copy the `.env.example` template to create your local `.env` file:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

### 5. Add API Credentials

Open `.env` in your editor and configure your environment variables:

```env
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_actual_openai_api_key_here
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

> **Security Note:** Never commit your real `.env` file or API credentials to Git. The `.env` file is excluded in `.gitignore`.

---

## Running the Application & Loader

### 6. Execute the Main Document Loader Demo

Run the main entry point to execute multi-format intake across the sample corpus:

```bash
python src/main.py
```

### 7. Run Unit Tests

Execute the automated test suite covering all document formats and failure modes:

```bash
python -m unittest discover tests
```

---

## Project Structure

```text
rag-app-starter/
├── data/
│   └── sample_corpus/  # Multi-format sample corpus (PDF, HTML, MD, TXT, corrupt PDF)
├── docs/               # Technical documentation & extraction specs
├── outputs/            # Generated outputs and document loader JSON logs
├── prompts/            # LLM prompts and instruction templates
├── scripts/
│   └── generate_sample_corpus.py # Script to populate sample corpus
├── src/                # Application source code
│   ├── document_loader.py # Multi-format document loader engine
│   └── main.py         # Entry point script
├── tests/
│   └── test_document_loader.py # Unit tests for document loader
├── .env.example        # Template for environment configuration
├── .gitignore          # Files and folders excluded from Git
├── README.md           # Workspace documentation
└── requirements.txt    # Pinned Python dependencies
```

---

## Setup Verification Note

> **Verification Status: PASSED**
> Multi-format document intake (PDF, HTML, Markdown, Plain Text), graceful error handling (missing/corrupt/unsupported files), source identity metadata, and unit test execution (`python -m unittest discover tests`) were tested and verified in a clean isolated Python environment.
