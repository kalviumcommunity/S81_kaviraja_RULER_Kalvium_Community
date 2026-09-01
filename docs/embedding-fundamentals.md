# Embedding Fundamentals Specification (`docs/embedding-fundamentals.md`)

This document provides a conceptual overview and technical specification for vector embeddings within our Retrieval-Augmented Generation (RAG) pipeline.

---

## 1. What Embedding Vectors Represent

**Vector embeddings** are dense, fixed-length numeric vector representations of the semantic meaning and contextual information contained in text.

Key characteristics:
* **Semantic Meaning**: Unlike raw text strings, embedding vectors capture the underlying conceptual meaning.
* **Not Random IDs**: Embeddings are calculated by machine learning models trained on vast corpora; they are deterministic and meaningful representations in a high-dimensional vector space.
* **Not Keyword Counts**: Embeddings go far beyond simple bag-of-words or term-frequency counters (like TF-IDF). They understand synonyms, context, and intent (e.g., recognizing that *"bank account balance"* and *"available funds"* convey the same request).
* **Geometric Proximity in Vector Space**: Texts with similar meanings are mapped to vectors located closer together in vector space (measured by directional angle or distance).
* **Semantic Comparison via Cosine Similarity**: Mathematical metrics such as **Cosine Similarity** calculate the cosine of the angle between two vectors, returning a score near `1.0` for semantically similar texts and near `0.0` or negative for unrelated topics.
* **Core Utility in RAG & Semantic Search**: In RAG retrieval pipelines, user queries and document chunks are converted into embedding vectors. Vector databases execute fast nearest-neighbor similarity searches to retrieve the most relevant context chunks even when exact keywords do not match.

---

## 2. Implementation Overview

The embedding fundamentals demonstration is implemented in `src/embedding_demo.py` and supported by `src/llm_client.py`.

### Key Components

1. **`LLMClient.generate_embeddings(texts, model=None)`**:
   - Reuses project environment configuration (`OPENAI_API_BASE_URL`, `OPENAI_API_KEY`, `EMBEDDING_MODEL`).
   - Interacts with OpenAI-compatible embedding endpoints (`text-embedding-3-small` / 1536 dimensions).
   - Handles errors gracefully and supports mock mode for offline testing.

2. **`verify_vector_dimensions(embeddings)`**:
   - Programmatically verifies that all returned embeddings have non-zero, identical vector lengths.
   - Ensures valid floating-point values across all dimensions.

3. **`cosine_similarity(vec_a, vec_b)`**:
   - Calculates exact cosine similarity:
     $$\text{Cosine Similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$

4. **`EmbeddingDemonstration` Engine**:
   - Compares:
     - **Text A (Original)**: *"The customer wants to check their bank account balance."*
     - **Text B (Similar)**: *"The user would like to know how much money is available in their account."*
     - **Text C (Unrelated)**: *"A football match was played during heavy rain."*
   - Verifies programmatically that $\text{similarity}(\text{Text A}, \text{Text B}) > \text{similarity}(\text{Text A}, \text{Text C})$.
   - Generates reproducible outputs:
     - `outputs/embedding_demo_output.txt`
     - `outputs/embedding_demonstration_results.json`

---

## 3. Verified Execution Results

```text
Embedding Provider: OpenRouter (OpenAI-Compatible API)
Embedding Model: text-embedding-3-small
Vector Dimension: 1536
Dimension Consistency: PASS

Cosine Similarity Scores:
 - Text A vs Text B (Similar meaning): 0.5964
 - Text A vs Text C (Unrelated meaning): 0.0193

Result Status: PASS — similar texts scored higher than unrelated texts
```
