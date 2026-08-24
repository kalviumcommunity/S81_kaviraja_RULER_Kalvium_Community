# RAG Application Starter (`rag-app-starter`)

Team repository for the RAG (Retrieval-Augmented Generation) application data product project.

This project provides the foundation and structure for building a Retrieval-Augmented Generation pipeline using document extraction, vector indexing (ChromaDB), and LLM integration (OpenAI).

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

## Running the Application

### 6. Execute the Starter Application

Run the entry point script to verify your setup:

```bash
python src/main.py
```

---

## Project Structure

```text
rag-app-starter/
├── data/               # Documents and knowledge-base source data
├── docs/               # Technical documentation & extraction specs
├── outputs/            # Generated outputs and processing results
├── prompts/            # LLM prompts and instruction templates
├── src/                # Application source code
│   └── main.py         # Entry point script
├── .env.example        # Template for environment configuration
├── .gitignore          # Files and folders excluded from Git
├── README.md           # Workspace documentation
└── requirements.txt    # Pinned Python dependencies
```

---

## Setup Verification Note

> **Verification Status: PASSED**
> The workspace setup, virtual environment creation (`.venv`), dependency installation (`openai`, `chromadb`, `python-dotenv`), package imports, and script execution (`python src/main.py`) were tested and verified in a clean isolated Python environment.
