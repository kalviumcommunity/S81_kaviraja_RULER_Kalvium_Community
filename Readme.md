# RAG Application Starter (`rag-app-starter`)

Team repository for the RAG (Retrieval-Augmented Generation) application data product project.

This project provides the foundation and structure for building a Retrieval-Augmented Generation pipeline using document extraction, vector indexing (ChromaDB), and LLM integration (OpenAI).

---

## Token-Aware Chunker Engine (`src/token_chunker.py`)

A token-aware document chunker that sizes chunks by exact token count using `tiktoken` (`cl100k_base`) and maintains controlled token overlap between adjacent chunks.

- **Task 1 — Token-Based Sizing**: Sizes chunks strictly in tokens (`512 tokens` target), preventing token budget overflow in LLMs and embedding models.
- **Task 2 — Controlled Overlap**: Enforces a `64 token` controlled overlap (~12.5%) between adjacent chunks, repeating trailing tokens from previous chunks.
- **Task 3 — Boundary Context Preservation**: Prevents context fragmentation across chunk boundaries (e.g. preserves authorization thresholds and subject clauses intact).
- **Task 4 — Justified Settings**: Technical justification for `512 token` size and `64 token` overlap tuned for `text-embedding-3-small` / `gpt-4o-mini`.
- **Task 5 — Output Artifacts**: Outputs detailed chunk logs to `outputs/token_chunker_results.json` and `outputs/token_chunker_output.txt`.


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

## End-to-End RAG Pipeline

Run the connected query-to-answer flow:

```bash
python scripts/run_rag_pipeline.py
```

The runner performs four explicit stages: query embedding, ChromaDB retrieval, grounded context assembly, and answer generation. It prints the answer and returned sources and saves the structured result to `outputs/rag_pipeline_sample.json`. Without `OPENAI_API_KEY`, it runs with deterministic offline adapters; with a configured key, it uses the existing OpenAI-compatible client for embeddings and generation. See [docs/rag-pipeline.md](docs/rag-pipeline.md) for the flow description.
