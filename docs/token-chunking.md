# Token-Aware Text Chunker Documentation

This module provides a token-aware document chunking engine designed for RAG (Retrieval-Augmented Generation) applications.

---

## Technical Overview & Implementation Tasks

### Task 1 — Token-Based Sizing (`tiktoken`)
Character-based text splitting fails to guarantee token context window compliance because character-to-token ratios vary depending on language, special characters, code, and whitespace. 
The `TokenAwareChunker` uses `tiktoken` (specifically `cl100k_base` encoding, which powers OpenAI `gpt-4o-mini`, `gpt-4`, and `text-embedding-3-small`) to strictly partition documents based on **exact token counts**.

- **Tokenizer Engine**: `tiktoken.get_encoding("cl100k_base")`
- **Measurement**: Token array slice size `len(tokens) <= chunk_size_tokens`.
- **Character Offset Tracing**: Calculates precise `start_char` and `end_char` position relative to original source text.

---

### Task 2 — Controlled Token Overlap
To prevent information loss at chunk edges, `TokenAwareChunker` implements a controlled sliding window with token overlap between adjacent chunks.

- **Window Sliding Step**: `step = chunk_size_tokens - chunk_overlap_tokens`
- **Overlap Guarantee**: Each chunk $i$ ($i > 1$) repeats the exact last $N$ tokens (`chunk_overlap_tokens`) of chunk $i-1$.
- **Metadata Tagging**: Tracks `start_token`, `end_token`, `token_count`, and `overlap_tokens` for auditability and verification.

---

### Task 3 — Boundary Context Preservation Demonstration

#### Comparison: Without Overlap vs With Controlled Overlap

Consider the following passage containing a critical authorization policy rule:

> *"Standard retail banking policies mandate that routine vendor payments under $50,000 may be approved directly by designated department heads without requiring senior executive approval. However, any single capital expenditure or vendor disbursement exceeding $50,000 requires unanimous board authorization and an independent audit report prior to disbursement."*

| Feature | Without Overlap (`overlap = 0`) | With Controlled Overlap (`overlap = 12`) |
| :--- | :--- | :--- |
| **Chunk 1 Boundary** | Ends at `"...any single capital expenditure"` | Ends at `"...any single capital expenditure"` |
| **Chunk 2 Boundary** | Starts with `"exceeding $50,000 requires unanimous..."` | Starts with `"any single capital expenditure exceeding $50,000 requires..."` |
| **Context Status** | ❌ **CONTEXT SEVERED**: Chunk 2 loses the subject ("capital expenditure"). An LLM retrieving Chunk 2 alone cannot infer what "exceeding $50,000" refers to. | ✅ **CONTEXT PRESERVED INTACT**: Chunk 2 includes the subject and condition, preserving complete factual context. |

---

### Task 4 — Technical Justification of Settings

| Setting | Value | Technical Justification |
| :--- | :--- | :--- |
| **Target Model** | `text-embedding-3-small` / `gpt-4o-mini` | Standard OpenAI RAG stack requiring strict token budget management. |
| **Chunk Size** | **512 tokens** | Balances semantic richness and vector retrieval performance. 512 tokens (~350–400 words) captures complete paragraphs without diluting key entity signals, while leaving ample headroom in context windows. |
| **Controlled Overlap** | **64 tokens** (~12.5%) | 64 tokens (~45–50 words / 1–2 complete sentences) covers typical dependent clauses, entity modifiers, and conjunctions. |
| **Cost vs Context** | **12.5% Overhead** | Adding a 64-token overlap incurs only a minor 12.5% token redundancy cost while completely eliminating boundary fragmentation errors. |

---

### Task 5 — Executing & Viewing Sample Outputs

#### Run Token Chunker Pipeline
```bash
python scripts/run_token_chunker_demo.py
```

#### Run Unit Test Suite
```bash
python -m unittest tests/test_token_chunker.py
```

#### Generated Artifacts
- **JSON Output**: `outputs/token_chunker_results.json` (Structured JSON containing token metadata, boundary demo, and chunk list)
- **Text Log**: `outputs/token_chunker_output.txt` (Human-readable execution report)
