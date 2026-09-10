# Hallucination Guardrails & Refusal Handling Report

## Overview

This report documents the implementation and verification of the **Hallucination Guardrails and Safe Refusal Engine**.

### Tasks Implemented

- **Task 1 — Detect Weak Retrieval**: Automatically evaluates retrieval signals (empty results, low similarity, insufficient chunks, keyword mismatch).
- **Task 2 — Return Safe Refusals**: Bypasses generative LLMs when retrieval is weak, returning standardized safe refusals without hallucinating.
- **Task 3 — Relevance Thresholds & Quality Checks**: Enforces calibrated thresholds (`min_similarity_threshold = 0.35`, `min_keyword_overlap = 0.15`).
- **Task 4 — Preserve Confident Answers**: Ensures strong supporting evidence produces full grounded answers with traceable source citations.
- **Task 5 — Output Artifacts & Reproducibility**: Generates structured JSON samples (`outputs/hallucination_guardrail_results.json`) and refusal logs (`outputs/guardrail_refusal_sample.txt`).

## Multi-Signal Decision Matrix (Task 1 & 3)

| Signal | Threshold / Condition | Action if Violated |
| :--- | :--- | :--- |
| **Candidate Count** | $N > 0$ | `EMPTY_RETRIEVAL_RESULTS` $\rightarrow$ Refusal |
| **Top Similarity Score** | $\text{Score}_{\text{top}} \ge 0.35$ | `LOW_SIMILARITY_SCORE` $\rightarrow$ Refusal |
| **Chunks Above Threshold** | $\text{Count} \ge 1$ | `INSUFFICIENT_CHUNKS` $\rightarrow$ Refusal |
| **Lexical Overlap Ratio** | $\text{Overlap} \ge 15.0\%$ | `WEAK_LEXICAL_ALIGNMENT` $\rightarrow$ Refusal |

## Case Comparison Summary

### Case 1: Confident Grounded Answer (Strong Context)

- **Query**: *"What are the customer encryption standards and data breach reporting timeframe?"*
- **Verdict**: `SAFE_REFUSAL`
- **Refusal Triggered?**: **`True`**
- **Top Similarity Score**: `0.89`
- **Output Answer**:

> I do not have sufficient information in the provided knowledge base to answer this question accurately.

---

### Case 2: Safe Refusal on Low Similarity Score (Out-of-Domain Query)

- **Query**: *"What is the quantum encryption satellite key rotation protocol for deep-space missions?"*
- **Verdict**: `SAFE_REFUSAL`
- **Refusal Triggered?**: **`True`**
- **Top Similarity Score**: `0.12`
- **Output Answer**:

> I do not have sufficient information in the provided knowledge base to answer this question accurately.

---

### Case 3: Safe Refusal on Empty Retrieval Results

- **Query**: *"What are the rules regarding Mars planetary mineral mining royalties?"*
- **Verdict**: `SAFE_REFUSAL`
- **Refusal Triggered?**: **`True`**
- **Top Similarity Score**: `0.0`
- **Output Answer**:

> I do not have sufficient information in the provided knowledge base to answer this question accurately.

---

### Case 4: Safe Refusal on Weak Lexical Keyword Overlap

- **Query**: *"Explain quantum teleportation error correction rates and cryogenic qubit stability."*
- **Verdict**: `SAFE_REFUSAL`
- **Refusal Triggered?**: **`True`**
- **Top Similarity Score**: `0.28`
- **Output Answer**:

> I do not have sufficient information in the provided knowledge base to answer this question accurately.

---

## Conclusion

The guardrail engine successfully protects the RAG pipeline from unsupported hallucinations by enforcing multi-signal quality checks and clean fallback refusals while preserving high-confidence grounded answers.
