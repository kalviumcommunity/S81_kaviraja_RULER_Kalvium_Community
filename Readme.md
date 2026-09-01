# RAG Application Starter (`rag-app-starter`)

Team repository for the RAG (Retrieval-Augmented Generation) application data product project.

This project provides the foundation and structure for building a Retrieval-Augmented Generation pipeline using document extraction, vector indexing (ChromaDB), and LLM integration (OpenAI).

---

## Embedding Fundamentals Engine (`src/embedding_demo.py`)

A vector embedding demonstration engine that generates real text embeddings, verifies vector dimension consistency, and calculates semantic cosine similarity across sample texts.

- **Task 1 — Real Vector Generation**: Generates embeddings for sample texts using configured `text-embedding-3-small` / OpenAI-compatible API.
- **Task 2 — Dimension Verification**: Programmatically verifies every returned vector has identical length (`1536` dimensions) and contains numeric float values.
- **Task 3 — Cosine Similarity Comparison**: Computes cosine similarity between Similar pair (Text A vs Text B: `0.5964`) and Unrelated pair (Text A vs Text C: `0.0193`), asserting `similarity(A, B) > similarity(A, C)`.
- **Task 4 — Vector Concept Documentation**: Detailed conceptual documentation in [`docs/embedding-fundamentals.md`](docs/embedding-fundamentals.md) explaining how embeddings represent semantic meaning.
- **Task 5 — Reproducible Output Artifacts**: Outputs formatted demonstration logs to `outputs/embedding_demo_output.txt` and `outputs/embedding_demonstration_results.json`.

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
