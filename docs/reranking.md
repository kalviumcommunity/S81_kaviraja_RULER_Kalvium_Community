# Chunk Re-Ranking for Precision

## 1. Motivation & Architecture Overview

In a typical Retrieval-Augmented Generation (RAG) system, dense vector embedding similarity performs an initial similarity search over the vector index. While dense retrieval has high recall, it often suffers from **semantic drift** and lack of fine-grained precision:
- **Broad Semantic Overlap**: A query asking for a specific percentage (e.g. *"Tier 1 Capital Ratio"*) might retrieve general governance or risk overview chunks in top positions because the vocabulary is related in embedding space.
- **Lost Specificity**: Dense embeddings compress entire chunk semantics into a single vector, sometimes missing exact numbers, entity conjunctions, or conditional constraints.

### Two-Stage Retrieval Architecture
```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: High Recall Retrieval (Vector DB Search)           │
│ - Embed query with text-embedding-3-small                   │
│ - Retrieve large candidate pool (e.g., initial_k = 10)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ (10 candidate chunks)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: High Precision Re-Ranking                          │
│ - Cross-Encoder / Lexical-Semantic Alignment & LLM scoring   │
│ - Evaluates keyword coverage, exact phrases, entity density │
│ - Calibrates Re-Rank Score (0.0 to 1.0)                     │
│ - Re-sorts candidates descending by Re-Rank Score           │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Top-3 filtered & re-ordered)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Final Top-K Selected Chunks (k = 3)                         │
│ - Injected into LLM context window with maximal precision   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Re-Ranking Scoring Methodology

Our `ChunkReranker` computes a calibrated relevance score combining:
1. **Query Term Coverage ($W_1 = 0.40$)**: The ratio of non-stopword query keywords present in the candidate text.
2. **Dense Vector Similarity Baseline ($W_2 = 0.25$)**: Preserves semantic vector proximity ($1 - \text{cosine\_distance}$).
3. **Multi-Word N-Gram & Exact Phrase Alignment ($W_3 = 0.15$)**: Rewards 2-4 word contiguous phrase matches.
4. **Numeric & Entity Precision Bonus ($W_4 = 0.10$)**: Specifically boosts exact matches for financial metrics (e.g. `10.5%`, `AES-256`, `TLS 1.3`, `24 hours`).
5. **Keyword Density ($W_5 = 0.10$)**: Normalized term occurrence frequency.

$$\text{ReRankScore} = \min\left(1.0, \, 0.40 \cdot C_{\text{term}} + 0.25 \cdot S_{\text{vec}} + 0.15 \cdot B_{\text{phrase}} + 0.10 \cdot B_{\text{numeric}} + 0.10 \cdot D_{\text{keyword}}\right)$$

---

## 3. Empirical Results: Before vs After

When evaluating the query:
> *"What are the data breach reporting timeframe and customer encryption standards?"*

| Stage | Rank | Chunk ID | Section | Score | Relevance Quality |
|---|---|---|---|---|---|
| **Before (Vector Only)** | #1 | `DOC_BRCF_2026#chunk_001` | Executive Overview | 0.824 | Mentions compliance generally, lacks 24h & AES-256 |
| **Before (Vector Only)** | #2 | `DOC_BRCF_2026#chunk_003` | Data Protection Controls | 0.791 | **Exact ground truth** (24 hours notice, AES-256) |
| **After (Re-Ranked)** | **#1 (+1)** | `DOC_BRCF_2026#chunk_003` | Data Protection Controls | **0.962** | **Ground truth promoted to top position** |
| **After (Re-Ranked)** | **#2 (-1)** | `DOC_BRCF_2026#chunk_001` | Executive Overview | **0.612** | Demoted appropriately |

### Benefits Observed
- **Higher Grounding Accuracy**: Downstream generation receives the exact factual clause at position #1.
- **Token Efficiency**: 10 candidates filtered down to the top 3 saves ~70% of prompt context budget.
- **Hallucination Reduction**: Removes irrelevant or peripherally related text from the LLM prompt.
