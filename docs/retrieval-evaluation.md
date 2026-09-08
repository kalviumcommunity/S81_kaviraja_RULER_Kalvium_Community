# Retrieval Evaluation Suite Specification (`docs/retrieval-evaluation.md`)

This document provides the technical specification, metric definitions, benchmark dataset documentation, and failure diagnosis taxonomy for the **Retrieval Evaluation Suite** implemented in `src/retrieval_evaluator.py`.

---

## 1. Evaluation Methodology & Metrics

To objectively evaluate the quality of our RAG retrieval pipeline beyond informal spot-checks, the system benchmarks retrieval against a curated, gold-standard labelled query dataset across multiple depths ($K \in \{1, 2, 3, 5\}$).

### Metric Definitions

1. **Recall@K**:
   Measures the proportion of relevant corpus chunks successfully retrieved in the top-$K$ candidates:
   $$\text{Recall@K} = \frac{|\text{Retrieved Top-}K \cap \text{Expected Relevant Chunks}|}{|\text{Expected Relevant Chunks}|}$$

2. **Hit Rate@K (Hit@K)**:
   A binary indicator measuring whether *at least one* known relevant chunk was retrieved in the top-$K$ candidates:
   $$\text{Hit@K} = \begin{cases} 1 & \text{if } |\text{Retrieved Top-}K \cap \text{Expected Relevant Chunks}| > 0 \\ 0 & \text{otherwise} \end{cases}$$

3. **Precision@K**:
   Measures the proportion of retrieved top-$K$ candidates that are genuinely relevant to the query:
   $$\text{Precision@K} = \frac{|\text{Retrieved Top-}K \cap \text{Expected Relevant Chunks}|}{K}$$

4. **Mean Reciprocal Rank (MRR)**:
   Evaluates ranking efficiency by calculating the reciprocal rank of the first relevant chunk retrieved across all queries:
   $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
   where $\text{rank}_i$ is the rank position of the first relevant chunk for query $i$.

5. **F1@K Score**:
   The harmonic mean balancing Precision@K and Recall@K:
   $$F_1@K = 2 \cdot \frac{\text{Precision@K} \cdot \text{Recall@K}}{\text{Precision@K} + \text{Recall@K}}$$

6. **Graded Relevance Quality Signal**:
   Manual and heuristic graded relevance judgments:
   * **Score 2 (Highly Relevant)**: Exact expected chunk answering the core information need.
   * **Score 1 (Partially Relevant)**: Chunk from the same document section providing contextual background.
   * **Score 0 (Irrelevant)**: Out-of-scope or unrelated chunk.

---

## 2. Gold-Standard Labelled Query Benchmark (`data/labelled_queries.json`)

The benchmark comprises 8 diverse queries targeting distinct sections, edge cases, and challenge types:

| Query ID | Category | Target Section | Difficulty | Expected Chunks |
| :--- | :--- | :--- | :--- | :--- |
| **Q-001** | Standard Relevance | Section 1: Executive Summary & Overview | Easy | `chunk_001` |
| **Q-002** | Standard Relevance | Section 2: Capital Reserves & Liquidity Ratios | Easy | `chunk_002` |
| **Q-003** | Standard Relevance | Section 3: High-Value Authorization Thresholds | Easy | `chunk_003`, `chunk_004` |
| **Q-004** | Negation Blindspot | Section 3: High-Value Authorization Thresholds | Hard (Edge Case) | `chunk_003` |
| **Q-005** | Lexical Distractor | Section 3: High-Value Authorization Thresholds | Medium | `chunk_003`, `chunk_004` |
| **Q-006** | Specific Entity / Threshold | Section 2: Capital Reserves & Liquidity Ratios | Easy | `chunk_002` |
| **Q-007** | Boundary Consequence Clause | Section 3: High-Value Authorization Thresholds | Medium | `chunk_004` |
| **Q-008** | Semantic Paraphrase | Section 1: Executive Summary & Overview | Medium | `chunk_001` |

---

## 3. Benchmark Evaluation Results

Execution of the evaluation suite against the banking regulation corpus produced the following verified aggregate metrics:

```text
Total Queries Evaluated: 8
Overall Benchmark Pass Rate: 62.5%
Mean Reciprocal Rank (MRR): 0.8125
Average Graded Quality Signal: 0.6875 / 2.00

Depth Analysis:
  Depth K=1: Recall@1 = 0.5000 | Precision@1 = 0.6250 | Hit@1 = 62.5%  | F1@1 = 0.5417
  Depth K=2: Recall@2 = 1.0000 | Precision@2 = 0.6250 | Hit@2 = 100.0% | F1@2 = 0.7500
  Depth K=3: Recall@3 = 1.0000 | Precision@3 = 0.4166 | Hit@3 = 100.0% | F1@3 = 0.5750
  Depth K=5: Recall@5 = 1.0000 | Precision@5 = 0.2500 | Hit@5 = 100.0% | F1@5 = 0.3928
```

Key observations:
* At **$K=2$ and $K=3$**, the retrieval system achieves **100% Hit Rate and 100% Recall**, confirming that relevant chunks are consistently returned in the top candidate window.
* Precision decreases naturally as $K$ increases beyond the count of relevant chunks in the small corpus.

---

## 4. Failure Inspection Taxonomy & Root Causes (Task 4)

Automated diagnostic analysis categorized failed or low-scoring queries into specific failure modes:

### 1. `EMBEDDING_NEGATION_BLINDSPOT` (e.g. Q-004)
* **Query**: *"Which vendor disbursements do NOT require unanimous board approval?"*
* **Target Chunk**: Chunk #3 (routine payments under $50k approved directly without board approval).
* **Observed Rank**: Rank #2.
* **Top Result**: Chunk #4 (exceeding $50k requires unanimous board authorization).
* **Root Cause**: Dense embedding models map text by positive topical density (`vendor disbursements`, `board approval`) and fail to invert vector direction for boolean negation (`NOT`).
* **Remediation**: Rephrase negative constraints via query rewriting or pre-filter on authorization tiers.

### 2. `CROSS_SECTION_LEXICAL_DISTRACTION` (e.g. Q-005)
* **Query**: *"What audit procedures and compliance checks are required for transaction authorization?"*
* **Root Cause**: General compliance terminology (`audit`, `compliance`, `authorization`) appears in both Section 1 and Section 3, inflating similarity scores for non-target sections.
* **Remediation**: Pre-retrieval metadata filtering scoped to target policy section.

### 3. `CHUNK_BOUNDARY_FRAGMENTATION` (e.g. Q-006 / Q-007)
* **Root Cause**: Regulatory consequences (e.g. procurement privileges suspension) severed across chunk split points, depriving the isolated chunk of its full subject clause.
* **Remediation**: Enforce controlled token overlap (e.g. 64–128 tokens) or hierarchical document parent-child chunking.

---

## 5. Generated Output Artifacts (Task 5)

All evaluation runs produce reproducible artifacts:
* `outputs/retrieval_evaluation_results.json`: Full structured JSON containing query-level recall, precision, MRR, and aggregate metrics.
* `outputs/retrieval_evaluation_report.txt`: Human-readable summary table and query breakdown.
* `outputs/retrieval_failure_analysis.json`: Diagnostic failure reports with root cause classifications and recommendations.
* `outputs/retrieval_failure_analysis.txt`: Human-readable failure inspection document.
