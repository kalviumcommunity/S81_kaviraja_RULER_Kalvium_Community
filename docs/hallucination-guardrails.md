# Hallucination Guardrails & Refusal Handling Documentation

## 1. Motivation & Problem Statement
In Retrieval-Augmented Generation (RAG) systems, when a user asks an out-of-domain question or retrieval fails to return relevant context, standard LLMs often generate plausible-sounding but completely fabricated hallucinations.

To make the system production-grade and auditable, the **Hallucination Guardrail Engine** implements multi-signal pre-generation checks that detect weak context, trigger deterministic safe refusals, and preserve confident answers when strong evidence is present.

---

## 2. Multi-Signal Detection Architecture (Task 1 & Task 3)

The guardrail evaluates four orthogonal quality signals before allowing generative LLM calls:

$$\text{GuardrailDecision} = \begin{cases} 
\text{SAFE\_REFUSAL}, & \text{if } N = 0 \lor S_{\text{top}} < \theta_{\text{sim}} \lor K_{\text{valid}} < K_{\text{min}} \lor O_{\text{kw}} < \theta_{\text{kw}} \\
\text{PROCEED\_CONFIDENT\_ANSWER}, & \text{otherwise}
\end{cases}$$

### Quality Signals Monitored:
1. **Empty Retrieval Detection ($N = 0$)**: Catches zero-candidate search failures immediately without calling the LLM.
2. **Top Similarity Threshold ($S_{\text{top}} \ge 0.35$)**: Ensures at least one retrieved chunk exhibits high semantic alignment with the query.
3. **Thresholded Candidate Count ($K_{\text{valid}} \ge 1$)**: Verifies that the required number of distinct supporting chunks meet the quality threshold.
4. **Lexical Keyword Overlap ($O_{\text{kw}} \ge 15\%$)**: Guards against vector embedding false positives (such as topic-density matches without entity overlap).
5. **Context Density**: Rejects fragments shorter than minimum character boundaries ($L \ge 40$ chars).

---

## 3. Safe Refusal Handling (Task 2)
When any retrieval quality check fails, the pipeline:
1. Bypasses the generative LLM call entirely (saving latency, token cost, and preventing hallucination).
2. Sets `is_refusal: True` and returns the standardized institutional refusal message:
   > *"I do not have sufficient information in the provided knowledge base to answer this question accurately."*
3. Records the exact failure reason (e.g. `LOW_SIMILARITY_SCORE`, `EMPTY_RETRIEVAL_RESULTS`, `WEAK_LEXICAL_ALIGNMENT`) in the audit telemetry.

---

## 4. Confident Grounded Answer Preservation (Task 4)
When retrieval quality checks pass:
1. Formats chunks with numbered source markers (`[1]`, `[2]`).
2. Generates an answer strictly grounded in the verified context with inline source citations.
3. Verifies that fact claims match the supporting context.

---

## 5. Artifacts and Audit Trails (Task 5)
All evaluations are logged to:
- `outputs/hallucination_guardrail_results.json`: Complete structured JSON output.
- `outputs/guardrail_refusal_sample.txt`: Human-readable refusal and confident generation sample logs.
- `outputs/guardrail_report.md`: Markdown summary report with comparative telemetry.
