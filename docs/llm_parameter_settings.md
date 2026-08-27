# LLM Parameter Guidelines for Grounded RAG Tasks

## Overview

Retrieval-Augmented Generation (RAG) systems rely on factual, precise, and hallucination-free completions. Hyperparameter selection plays a critical role in controlling model determinism, context grounding, and token economy.

---

## Recommended Parameter Configuration Matrix

| Parameter | Recommended Value | Purpose & Rationale |
| :--- | :--- | :--- |
| **`temperature`** | **`0.0`** (or `0.0 - 0.2`) | **Strict Determinism & Factuality**: Minimizes sampling randomness. Forces the model to choose high-probability tokens grounded in retrieved context, preventing imaginative hallucination or rambling. |
| **`max_tokens`** | **`250 - 500`** | **Budget & Output Capping**: Limits generation length to protect API budget and prevent long-winded responses while providing enough headroom for full factual answers without premature truncation (`finish_reason: "length"`). |
| **`top_p`** | **`1.0`** (or `0.9`) | **Nucleus Sampling Control**: When `temperature=0.0`, `top_p` is left at `1.0`. For slight token variance while eliminating low-probability tail tokens, `top_p=0.9` can be used. |
| **`stop`** | **`["\n\nUser:", "--- END ---"]`** | **Generation Delimiters**: Halts response generation immediately if structural prompt delimiters appear, preventing prompt leakage or accidental continuation into user roles. |

---

## Parameter Impact & Trade-Off Analysis

### 1. Temperature (`temperature`)
- **Low (`0.0`)**: Exact, reproducible, factual outputs. High compliance accuracy for RAG document Q&A.
- **Medium (`0.7`)**: Standard natural language fluency with moderate variance.
- **High (`1.3+`)**: Creative, diverse phrasing, but prone to hallucinations, speculation, and ungrounded statements. Unsuitable for regulatory/RAG applications.

### 2. Maximum Tokens (`max_tokens`)
- **Under-sized (`< 30 tokens`)**: Truncated responses (`finish_reason: "length"`), cutting off answers mid-sentence.
- **Sufficient (`250 - 500 tokens`)**: Complete answers with predictable token cost bounds (`finish_reason: "stop"`).

### 3. Nucleus Sampling (`top_p`)
- **Low (`0.1`)**: Restricts token selection to top 10% probability mass for strict domain control.
- **Standard (`0.9 - 1.0`)**: Full token distribution pool, ideal when temperature is set to `0.0`.

### 4. Stop Sequences (`stop`)
- Halts generation when target strings are encountered, enforcing output boundary control.
