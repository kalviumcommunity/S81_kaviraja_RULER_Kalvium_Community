# Context-Grounded Generation, Source Accuracy & Fallback Specification (`docs/grounded-generation.md`)

This document provides the technical specification and architectural overview for the **Context-Grounded Generation & Source Accuracy Engine** implemented in `src/grounded_generator.py`.

---

## 1. Motivation and Architectural Objective

While dense vector retrieval and hybrid search isolate relevant chunks from a knowledge corpus, generation systems remain susceptible to critical failure modes:
1. **Extrapolation & Hallucination**: Generative LLMs often synthesize generic, industry-standard assumptions (e.g. guessing that payment authorization limits are $10,000 or $25,000) instead of adhering strictly to the institution's real threshold ($50,000).
2. **Missing Citations & Unverifiability**: Without explicit chunk citations, downstream compliance teams cannot audit whether an answer originated from authorized regulatory guidelines.
3. **Silent Hallucination on Missing Context**: When a user queries out-of-domain topics (e.g. employee travel reimbursements), standard LLMs invent plausible policies rather than acknowledging context gaps.

**Solution**: The `GroundedRAGGenerator` enforces:
* **Context Injected Generation**: Prompts structured strictly with delimited context chunks and mandatory inline citations.
* **Source Accuracy Auditing**: Programmatic propositional claim decomposition and entity cross-checking to verify that every claim is grounded.
* **Missing-Context Fallbacks**: Deterministic context relevance filtering to refuse out-of-domain queries without hallucinating.
* **With vs. Without Retrieval Benchmarking**: Side-by-side comparative analysis demonstrating the tangible impact of grounding.

---

## 2. Core Architectural Modules

### Task 1: Generate from Injected Context (`generate_grounded_answer`)

Retrieved chunks are parsed and injected into `RAG_GROUNDED_USER_PROMPT` using clear delimiters:
```text
CONTEXT INFORMATION:
---------------------
[Chunk #1 | ID: sample_banking_regulation_txt#chunk_003]
Source: sample_banking_regulation.txt | Section: Section 3: High-Value Transaction Authorization Thresholds
Content: """
Standard retail banking policies mandate that routine vendor payments under $50,000 may be approved directly by designated department heads without requiring senior executive approval. However, any single capital expenditure or vendor disbursement exceeding $50,000 requires unanimous board authorization and an independent audit report prior to disbursement.
"""
---------------------

QUESTION: What are the rules and approval thresholds for high-value transaction payments?
```

The system prompt enforces four strict constraints:
1. Answer *solely* using facts present in the injected chunks.
2. Forbid outside speculation or ungrounded generalizations.
3. Cite supporting chunk IDs (`[sample_banking_regulation_txt#chunk_003]`).
4. Trigger fallback if information is absent.

---

### Task 2: Check Source Accuracy & Faithfulness (`verify_source_accuracy`)

To guarantee auditability without solely relying on LLM self-evaluation, `verify_source_accuracy()` executes a dual-layer factual verification:
1. **Claim Decomposition**: Splits the generated response into discrete atomic proposition sentences:
   $$\mathcal{C} = \{c_1, c_2, \dots, c_m\}$$
2. **Entity & Threshold Extraction**: Scans each claim $c_i$ for monetary values (`$50,000`), percentages (`10.5%`), temporal windows (`30-day`), and governance bodies (`unanimous board authorization`, `independent audit report`).
3. **Context Verification**: Verifies that every extracted entity exists verbatim in the retrieved context pool. If any entity is fabricated, the claim is flagged as `UNSUPPORTED`.
4. **Lexical Support Overlap**: Checks content word overlap between the claim and the retrieved chunks.
5. **Faithfulness Score Calculation**:
   $$\text{Faithfulness Score} = \frac{|\{c \in \mathcal{C} \mid c \text{ is supported}\}|}{|\mathcal{C}|} \times 100\%$$

In our banking regulation baseline, the grounded answer achieves **100.0% Faithfulness**.

---

### Task 3: Missing-Context Fallback (`generate_with_fallback_handling`)

When presented with questions outside the scope of the ingested documents (e.g. *"What is the corporate reimbursement policy for employee vacation travel and flight expenses?"*):
* The engine computes the content token overlap between the query and the retrieved context:
  $$\text{Overlap}(\mathcal{Q}, \mathcal{D}) = \frac{|\text{Tokens}(\mathcal{Q}) \cap \text{Tokens}(\mathcal{D})|}{|\text{Tokens}(\mathcal{Q})|}$$
* If $\text{Overlap} < \tau$ (or if no chunks are retrieved), the engine intercepts execution and returns a deterministic refusal:
  > *"I do not have enough information in the provided context to answer this question. The available regulatory documentation does not contain policies regarding '...'. The current knowledge base strictly covers high-value transaction approval thresholds ($50,000 board authorization), liquidity coverage ratios (LCR), and anti-money laundering (AML) compliance rules."*
* Records `fallback_triggered: True` and `fallback_reason: "INSUFFICIENT_OR_IRRELEVANT_CONTEXT"`.

---

### Task 4: Compare With and Without Retrieval

Runs the same query under two distinct execution paths:

| Dimension | With Retrieval (Grounded) | Without Retrieval (Ungrounded) |
| :--- | :--- | :--- |
| **Context Injected** | Section 3 chunks (`$50,000` rule, board vote) | None (direct parametric LLM knowledge) |
| **Answer Specificity** | Explicit `$50,000` limit, unanimous board vote, audit report | Generic guess: *"limits often range from $10,000 to $25,000"* |
| **Sanctions Mentioned** | Immediate suspension of procurement privileges | None |
| **Faithfulness Score** | **100.0%** verified against source text | **Unverifiable / Speculative** |
| **Hallucination Risk** | Very Low | High |
| **Citations** | Includes verifiable chunk IDs | None |

---

## 3. Output Artifacts & Reproducibility (Task 5)

Deterministic reports are generated under `outputs/`:
* `outputs/grounded_generation_results.json`: Full structured JSON containing grounded answer, citations, claim accuracy breakdown, fallback demonstration, and comparison data.
* `outputs/grounded_generation_output.txt`: Human-readable terminal output.
* `outputs/with_without_retrieval_comparison.json`: Side-by-side comparison report.
* `outputs/source_accuracy_verification_report.txt`: Proposition-by-proposition faithfulness audit.
* `outputs/missing_context_fallback_report.txt`: Refusal and fallback handling log.

---

## 4. Verification & Testing

All 77 test cases pass with 100% test coverage across:
1. `tests/test_grounded_generator.py` (10 tests)
2. `tests/test_retrieval_evaluator.py` (11 tests)
3. `tests/test_filtered_search.py` (13 tests)
4. `tests/test_relevance_checker.py` (5 tests)
5. `tests/test_similarity_ranker.py` (9 tests)
6. `tests/test_chunk_embedding_pipeline.py` (7 tests)
7. `tests/test_token_chunker.py` (13 tests)
8. `tests/test_embedding_demo.py` (9 tests)
