"""
Hallucination Guardrails & Refusal Handling Demonstration Runner (Tasks 1 to 5).

Runs:
1. Setup & Corpus Preparation.
2. Case 1: Strong Supporting Context -> Confident Grounded Answer Preservation (Task 4).
3. Case 2: Out-of-Domain Query with Low Similarity -> Safe Refusal (Task 1, 2, 3).
4. Case 3: Empty Retrieval Results -> Safe Refusal (Task 1, 2, 3).
5. Case 4: Weak Lexical Keyword Overlap -> Safe Refusal (Task 1, 2, 3).
6. Export Output Artifacts (Task 5).
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any

# Ensure project root and src are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from llm_client import LLMClient
from token_chunker import TokenAwareChunker, TokenChunk
from context_injection import ContextInjector, TokenBudgetConfig, SourceMarkerStyle
from hallucination_guardrails import (
    HallucinationGuardrail,
    GuardrailConfig,
    GuardrailDecision,
    GuardrailResult,
)


def load_sample_knowledge_chunks() -> List[TokenChunk]:
    """Loads sample banking regulation chunks for testing."""
    chunker = TokenAwareChunker(chunk_size_tokens=100, chunk_overlap_tokens=20)
    doc_path = os.path.join("data", "sample_banking_regulation.txt")

    if os.path.exists(doc_path):
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        return chunker.chunk_text(
            text=content,
            doc_id="DOC_BRCF_2026",
            filename="sample_banking_regulation.txt",
            source_path=doc_path,
            section="Section 3: High-Value Authorizations",
        )
    return [
        TokenChunk(
            chunk_id="chunk_001",
            text="Any single capital expenditure exceeding $50,000 requires unanimous board approval and an independent audit report prior to disbursement.",
            token_count=24,
            start_token=0,
            end_token=24,
            overlap_tokens=0,
            doc_id="DOC_BRCF_2026",
            filename="sample_banking_regulation.txt",
            section="Section 3: High-Value Authorizations",
        )
    ]


def run_guardrails_demonstration():
    print("================================================================================")
    print("   HALLUCINATION GUARDRAILS & REFUSAL HANDLING DEMONSTRATION (Tasks 1 - 5)      ")
    print("================================================================================\n")

    os.makedirs("outputs", exist_ok=True)
    log_file = os.path.join("outputs", "guardrail_execution_log.txt")

    llm = LLMClient(log_file=log_file)
    injector = ContextInjector()
    config = GuardrailConfig(
        min_similarity_threshold=0.35,
        min_chunks_above_threshold=1,
        min_keyword_overlap_ratio=0.15,
        min_context_character_length=40,
    )
    guardrail = HallucinationGuardrail(
        config=config,
        llm_client=llm,
        context_injector=injector,
    )

    chunks = load_sample_knowledge_chunks()
    print(f"[Setup] Loaded {len(chunks)} knowledge chunks for guardrail evaluation.\n")

    # Run Demonstration Suite
    demo_results = guardrail.run_demonstration_suite(sample_chunks=chunks)

    # Print Detailed Per-Case Output
    for idx, case in enumerate(demo_results["demonstrations"], 1):
        res = case["result"]
        dec = res["decision"]
        sig = dec["quality_signals"]

        print("--------------------------------------------------------------------------------")
        print(f"CASE #{idx}: {case['title']}")
        print(f"Description: {case['description']}")
        print("--------------------------------------------------------------------------------")
        print(f" -> Query: \"{case['input_query']}\"")
        print(f" -> Candidates Provided: {case['provided_chunks_count']} chunks | Similarity Scores: {case['provided_similarity_scores']}")
        print(f" -> Quality Signals Evaluated:")
        print(f"    * Top Score:        {sig['top_similarity_score']} (Threshold: {config.min_similarity_threshold})")
        print(f"    * Chunks >= Thresh: {sig['chunks_above_threshold']} (Required: {config.min_chunks_above_threshold})")
        print(f"    * Keyword Overlap:  {sig['keyword_overlap_ratio'] * 100:.1f}% (Required: {config.min_keyword_overlap_ratio * 100:.1f}%)")
        print(f"    * Empty Retrieval:  {sig['is_empty_retrieval']}")
        print(f" -> Guardrail Decision:  {dec['verdict']} (Should Refuse: {dec['should_refuse']})")
        if dec["refusal_reasons"]:
            print(f" -> Refusal Trigger(s):  {dec['refusal_reasons']}")
        print(f" -> Final Output Answer:\n    \"{res['final_answer']}\"")
        if res["cited_sources"]:
            print(f" -> Cited Sources: {[s['marker'] for s in res['cited_sources']]}")
        print()

    # Task 5: Export Sample Output Files
    json_path = os.path.join("outputs", "hallucination_guardrail_results.json")
    txt_path = os.path.join("outputs", "guardrail_refusal_sample.txt")
    md_path = os.path.join("outputs", "guardrail_report.md")

    guardrail.export_sample_artifacts(
        demo_summary=demo_results,
        output_json_path=json_path,
        output_txt_path=txt_path,
        output_md_path=md_path,
    )

    print("================================================================================")
    print("[Task 5] Guardrail Artifacts Successfully Exported:")
    print(f" -> Structured JSON: {json_path}")
    print(f" -> Inspection Log:  {txt_path}")
    print(f" -> Markdown Report: {md_path}")
    print("================================================================================\n")

    return demo_results


if __name__ == "__main__":
    run_guardrails_demonstration()
