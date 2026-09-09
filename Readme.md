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

---

## Relevance Quality & Sanity Suite (`src/relevance_checker.py`)

A vector search relevance evaluation engine that executes known query-chunk test cases, verifies ranking order, diagnoses model blindspots, and compiles comprehensive sanity reports.

- **Task 1 — Known Relevance Test Suite**: Defines structured query-chunk pairs with expected section targets (AML, Basel IV Liquidity, Payment Thresholds).
- **Task 2 — Ranking Order Verification**: Confirms that related document chunks rank strictly above unrelated corpus chunks with positive score margins.
- **Task 3 — Failing / Surprising Case Diagnosis**: Identifies vector embedding negation blindspots (e.g. query asking for disbursements that 'do NOT require unanimous board approval' ranking positive approval requirement chunk #1 due to topic keyword density).
- **Task 4 — Sanity Report Summary**: Compiles test counts, pass rates (100% on standard relevance), top-ranked sources, similarity scores, and pipeline recommendations.
- **Task 5 — Output Artifacts & Reproducibility**: Exports structured JSON results to `outputs/relevance_sanity_results.json` and human-readable text logs to `outputs/relevance_sanity_report.txt`.

---

## Metadata-Filtered & Hybrid Search Engine (`src/filtered_search.py`)

A high-precision retrieval engine combining pre-retrieval metadata filtering, Okapi BM25 lexical keyword matching, exact entity/phrase boosting, and dense vector semantic search.

- **Task 1 — Metadata Filter**: Restricts retrieval to authorized subsets (section, source document, document type, category) using flexible filter operators (`exact`, `contains`, `in`, `gte`, `lte`, or custom callables).
- **Task 2 — Filtered vs. Unfiltered Comparison**: Runs queries side-by-side with and without metadata filtering, confirming that the filtered search removes cross-section noise and isolates target chunks.
- **Task 3 — Keyword & Hybrid Matching**: Combines dense vector cosine similarity with lexical keyword scoring using linear combination ($\alpha \cdot \text{Score}_{\text{vec}} + (1 - \alpha) \cdot \text{Score}_{\text{lex}}$) and exact phrase/threshold bonuses (e.g. `"$50,000"`, `"10.5%"`).
- **Task 4 — Precision Improvement Demonstration**: Quantitatively proves retrieval precision improvements (e.g. Precision@3 increasing from `66.67%` to `100.0%`, net `+33.33%` gain) by eliminating loosely related distractor chunks.
- **Task 5 — Output Artifacts & Reproducibility**: Exports structured JSON to `outputs/filtered_search_results.json`, `outputs/hybrid_search_comparison.json`, and human-readable text logs to `outputs/filtered_search_output.txt` and `outputs/precision_demonstration_report.txt`.

---

## Retrieval Evaluation Suite (`src/retrieval_evaluator.py`)

A quantitative evaluation engine that benchmarks retrieval recall, precision, MRR, hit rates, and graded quality signals against a gold-standard labelled query dataset, with automated failure diagnostics.

- **Task 1 — Prepare Labelled Queries**: Defines and loads a structured 8-query benchmark dataset ([`data/labelled_queries.json`](data/labelled_queries.json)) with ground-truth relevant chunk IDs and difficulty tags.
- **Task 2 — Measure Recall@K**: Evaluates exact set Recall@K and Hit@K across multiple candidate depths ($K \in \{1, 2, 3, 5\}$), achieving 100% Recall and 100% Hit Rate at $K \ge 2$.
- **Task 3 — Report Precision@K & Quality Signals**: Measures Precision@K, Mean Reciprocal Rank (MRR: `0.8125`), F1@K, and graded relevance judgments (Highly Relevant: 2, Partially Relevant: 1, Irrelevant: 0).
- **Task 4 — Inspect Failures & Root Causes**: Categorizes failure modes (e.g. `EMBEDDING_NEGATION_BLINDSPOT`, `CROSS_SECTION_LEXICAL_DISTRACTION`, `CHUNK_BOUNDARY_FRAGMENTATION`) and provides actionable remediation guidance.
---

## Context Injection & Prompt Augmentation Engine (`src/context_injection.py`)

A production-grade prompt assembly and context injection engine that formats retrieved chunks with source markers, strictly enforces model token budgets with `tiktoken`, and injects grounding instructions to eliminate hallucinations.

- **Task 1 — Inject Retrieved Chunks**: Formats retrieved chunks with clean metadata demarcation and injects them into the prompt context.
- **Task 2 — Enforce Token Budget**: Calculates token headroom dynamically (`model_limit - system_tokens - question_tokens - max_answer_tokens - safety_margin`) using `tiktoken` (`cl100k_base`), fitting chunks sequentially and cleanly skipping overflow chunks.
- **Task 3 — Include Source Markers**: Injects standardized citation markers (`[1]`, `[2]`, `[Source X: filename | Section]`) to enable direct, verifiable source citations in generated responses.
- **Task 4 — Add Grounding Instructions**: Enforces strict instructions preventing hallucinations and mandating clear statements when the context is insufficient.
- **Task 5 — Output Artifacts & Reproducibility**: Generates structured JSON samples ([`outputs/augmented_prompt_sample.json`](outputs/augmented_prompt_sample.json)), prompt inspection logs ([`outputs/augmented_prompt_sample.txt`](outputs/augmented_prompt_sample.txt)), and comprehensive reports ([`outputs/context_injection_report.md`](outputs/context_injection_report.md)).


- **Task 1 — Injected Context Generation**: Synthesizes responses strictly using facts from retrieved chunks, enforcing inline chunk citations (`[sample_banking_regulation_txt#chunk_003]`) and forbidding external hallucination.
- **Task 2 — Source Accuracy Auditing**: Programmatically decomposes generated answers into atomic proposition claims, cross-checks numerical thresholds (`$50,000`), percentages, and governance terms against context, achieving **100.0% Faithfulness**.
- **Task 3 — Missing-Context Fallback**: Detects out-of-domain queries lacking supporting evidence and returns an explicit, polite refusal without fabricating information (`fallback_triggered: True`).
- **Task 4 — With vs. Without Retrieval Comparison**: Directly demonstrates how grounding transforms vague, generic guesses ($10,000/$25,000) into 100% compliant, auditable institutional policy ($50,000 unanimous board vote + independent audit).
- **Task 5 — Output Artifacts & Reproducibility**: Exports structured JSON to `outputs/grounded_generation_results.json`, `outputs/with_without_retrieval_comparison.json`, and text logs to `outputs/grounded_generation_output.txt`, `outputs/source_accuracy_verification_report.txt`, and `outputs/missing_context_fallback_report.txt`.

---

## Hallucination Guardrails & Refusal Handling (`src/hallucination_guardrails.py`)

A pre-generation quality guardrail and safe refusal engine that monitors retrieval signals, triggers deterministic safe refusals on weak context, and preserves confident grounded answers when strong evidence exists.

- **Task 1 — Weak Retrieval Detection**: Detects weak retrieval using multi-signal checks (empty candidates, low similarity score, too few chunks above threshold, or weak lexical alignment).
- **Task 2 — Safe Refusal Generation**: Returns an explicit, standardized refusal without invoking generative LLMs, eliminating hallucination risks.
- **Task 3 — Multi-Criteria Thresholds**: Applies configurable decision rules (`min_similarity_threshold = 0.35`, `min_keyword_overlap_ratio = 0.15`, `min_chunks_above_threshold = 1`).
- **Task 4 — Confident Answer Preservation**: Routes verified strong evidence to grounded generation with complete source citations.
- **Task 5 — Output Artifacts & Reproducibility**: Exports structured JSON to [`outputs/hallucination_guardrail_results.json`](outputs/hallucination_guardrail_results.json), refusal inspection logs to [`outputs/guardrail_refusal_sample.txt`](outputs/guardrail_refusal_sample.txt), and report to [`outputs/guardrail_report.md`](outputs/guardrail_report.md).

---

## Conversational RAG & Multi-Turn Query Rewriting (`src/conversational_rag.py`)

A conversational RAG engine that tracks dialogue history across multiple turns, resolves ambiguous follow-up questions containing pronouns or ellipses into self-contained standalone search queries, and retrieves high-precision grounded context.

- **Task 1 — Track Conversation History**: Tracks user questions, assistant answers, rewritten standalone queries, retrieved context chunks, and citations across turns using `ConversationTurn` and `ConversationHistoryTracker` with sliding-window FIFO management.
- **Task 2 — Rewrite Follow-Up Questions**: Reformulates follow-up queries with coreference pronouns (*"them"*, *"it"*, *"under that threshold"*) into standalone queries using `ConversationalQueryRewriter` and `CONVERSATIONAL_QUERY_REWRITE_SYSTEM_PROMPT`, preserving independent queries without alteration.
- **Task 3 — Retrieve Using Rewritten Query**: Proves quantitative retrieval precision and similarity score gains ($\Delta S > 0$) by benchmarking rewritten queries against raw follow-up queries via `ConversationalRetriever.compare_retrieval()`.
- **Task 4 — Demonstrate Multi-Turn Dialogue**: Demonstrates an end-to-end 4-turn institutional regulatory dialogue where follow-ups are accurately answered and cited because conversational history was used to reformulate queries.
- **Task 5 — Output Artifacts & Reproducibility**: Exports structured JSON to [`outputs/sample_dialogue.json`](outputs/sample_dialogue.json) and [`outputs/conversational_rag_results.json`](outputs/conversational_rag_results.json), human-readable dialogue transcripts to [`outputs/sample_dialogue.txt`](outputs/sample_dialogue.txt), and comprehensive report to [`outputs/conversational_rag_report.md`](outputs/conversational_rag_report.md). Detailed documentation in [`docs/conversational-rag.md`](docs/conversational-rag.md).

---

## Prerequisites

## Source Citation & Attribution

Generated answers are validated against the chunks injected into the grounded prompt. A valid marker such as `[1]` maps to the retrieved chunk's document ID, filename, section, page, chunk ID, character span, and exact original retrieved text. The API returns these mappings in `parsed_object.citations`, and the UI source drawer uses the returned character span for verification.

Answers with no retrieved evidence, missing citations, or unknown citation markers return the explicit no-source fallback and an empty `citations` list. See [`outputs/citation_demo.json`](outputs/citation_demo.json) and [`outputs/citation_demo.md`](outputs/citation_demo.md) for cited and fallback examples.

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
