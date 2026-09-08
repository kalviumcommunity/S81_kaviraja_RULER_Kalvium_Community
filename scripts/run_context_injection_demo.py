"""
Context Injection & Prompt Augmentation Demonstration Runner (Tasks 1 to 5).

Runs end-to-end demonstrations:
1. Scenario 1: Standard Context Injection with Numbered Source Markers [1], [2] & Grounded Answering.
2. Scenario 2: Strict Token Budget Enforcement & Headroom Management (Skipping overflowing chunks).
3. Scenario 3: Verbose Source Markers & Multi-Document Context Injection.
4. Scenario 4: Insufficient Context / Out-of-Scope Query demonstrating grounding refusal instruction adherence.
5. Task 5: Output Artifact Generation (outputs/augmented_prompt_sample.json, outputs/augmented_prompt_sample.txt, outputs/context_injection_report.md).
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
from context_injection import (
    ContextInjector,
    TokenBudgetConfig,
    SourceMarkerStyle,
    AugmentedPrompt,
)


def load_demo_chunks() -> List[TokenChunk]:
    """Loads and chunks sample banking regulation and AI application documents."""
    chunker = TokenAwareChunker(chunk_size_tokens=90, chunk_overlap_tokens=15)
    all_chunks = []

    doc_configs = [
        {
            "path": os.path.join("data", "sample_banking_regulation.txt"),
            "doc_id": "DOC_BRCF_2026",
            "filename": "sample_banking_regulation.txt",
            "section": "Section 3: High-Value Authorizations & Liquidity",
        },
        {
            "path": os.path.join("data", "doc1.txt"),
            "doc_id": "DOC1_AI_OVERVIEW",
            "filename": "doc1.txt",
            "section": "Section 1: AI Fundamentals",
        },
        {
            "path": os.path.join("data", "doc2.txt"),
            "doc_id": "DOC2_AI_APPLICATIONS",
            "filename": "doc2.txt",
            "section": "Section 2: Enterprise Applications",
        },
    ]

    for doc in doc_configs:
        if os.path.exists(doc["path"]):
            with open(doc["path"], "r", encoding="utf-8") as f:
                content = f.read()
            chunks = chunker.chunk_text(
                text=content,
                doc_id=doc["doc_id"],
                filename=doc["filename"],
                source_path=doc["path"],
                section=doc["section"],
            )
            all_chunks.extend(chunks)

    return all_chunks


def run_context_injection_demonstration() -> Dict[str, Any]:
    print("================================================================================")
    print("      CONTEXT INJECTION & PROMPT AUGMENTATION DEMONSTRATION (Tasks 1 - 5)       ")
    print("================================================================================\n")

    os.makedirs("outputs", exist_ok=True)
    log_file = os.path.join("outputs", "context_injection_log.txt")
    llm = LLMClient(log_file=log_file)
    chunks = load_demo_chunks()
    print(f"[Setup] Loaded {len(chunks)} pre-tokenized chunks from knowledge repository.\n")

    demonstrations = []

    # --------------------------------------------------------------------------
    # SCENARIO 1: Standard Context Injection with Numbered Source Markers (Task 1, 3, 4)
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("SCENARIO 1: Standard Injected Chunks with Numbered Source Markers [1], [2]")
    print("--------------------------------------------------------------------------------")
    injector_standard = ContextInjector(
        budget_config=TokenBudgetConfig(total_model_limit=4096, max_answer_tokens=500),
        default_marker_style=SourceMarkerStyle.NUMBERED,
    )
    q1 = "What is the authorization policy for single capital expenditures exceeding $50,000?"
    # Pick relevant chunks
    relevant_chunks_q1 = [c for c in chunks if "$50,000" in c.text or "capital expenditure" in c.text.lower()][:2]
    if not relevant_chunks_q1:
        relevant_chunks_q1 = chunks[:2]

    prompt_q1 = injector_standard.build_augmented_prompt(
        question=q1,
        retrieved_chunks=relevant_chunks_q1,
        role="Banking Regulation & Compliance Specialist",
        marker_style=SourceMarkerStyle.NUMBERED,
    )

    mock_resp_q1 = (
        "According to the banking regulation policy, any single capital expenditure exceeding $50,000 "
        "requires unanimous board approval and an independent audit report prior to disbursement [1]. "
        "Failure to obtain prior authorization results in immediate suspension of procurement privileges [1]."
    )

    gen_q1 = injector_standard.generate_grounded_answer(
        augmented_prompt=prompt_q1,
        llm_client=llm,
        mock_response=mock_resp_q1,
    )

    print(f" -> Question: \"{q1}\"")
    print(f" -> Injected Chunks: {len(prompt_q1.assembled_context.injected_chunks)} (Tokens: {prompt_q1.assembled_context.context_tokens})")
    print(f" -> Model Token Limit: {prompt_q1.token_accounting['model_limit']} | Total Projected Tokens: {prompt_q1.token_accounting['max_projected_total_tokens']}")
    print(f" -> Grounded Answer with Citation:\n    \"{gen_q1['grounded_answer']}\"\n")

    demonstrations.append({
        "scenario_id": "SCENARIO_1_STANDARD_CITATION",
        "title": "Standard Context Injection with Numbered Source Markers [1], [2]",
        "description": "Demonstrates formatting retrieved chunks with numbered brackets [1], [2], injecting grounding rules, and verifying citation in generated answer.",
        "augmented_prompt": prompt_q1.to_dict(),
        "generation_result": gen_q1,
    })

    # --------------------------------------------------------------------------
    # SCENARIO 2: Strict Token Budget Enforcement & Headroom Management (Task 2)
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("SCENARIO 2: Strict Token Budget Enforcement (Limited Context Window)")
    print("--------------------------------------------------------------------------------")
    # Constrain model limit to 500 tokens total, leaving only ~250 tokens for context
    strict_budget = TokenBudgetConfig(
        total_model_limit=500,
        max_answer_tokens=150,
        safety_margin_tokens=30,
        encoding_name="cl100k_base",
    )
    injector_strict = ContextInjector(budget_config=strict_budget)
    q2 = "Summarize the regulatory framework across all banking and data management rules."
    # Provide 8 candidate chunks which would normally consume ~800+ tokens
    many_candidate_chunks = chunks[:8]

    prompt_q2 = injector_strict.build_augmented_prompt(
        question=q2,
        retrieved_chunks=many_candidate_chunks,
        role="Financial Regulatory Officer",
        budget_config=strict_budget,
    )

    mock_resp_q2 = (
        "The regulatory framework mandates strict oversight over transaction authorization thresholds [1] "
        "and imposes mandatory compliance checks [2]."
    )

    gen_q2 = injector_strict.generate_grounded_answer(
        augmented_prompt=prompt_q2,
        llm_client=llm,
        mock_response=mock_resp_q2,
    )

    print(f" -> Total Candidate Chunks Provided: {len(many_candidate_chunks)}")
    print(f" -> Total Available Context Budget: {prompt_q2.assembled_context.available_context_budget} tokens")
    print(f" -> Injected Chunks: {prompt_q2.assembled_context.total_injected_chunks} chunks ({prompt_q2.assembled_context.context_tokens} tokens)")
    print(f" -> Skipped (Over-Budget) Chunks: {prompt_q2.assembled_context.total_skipped_chunks} chunks")
    for skipped in prompt_q2.assembled_context.skipped_chunks:
        print(f"    * Skipped Chunk '{skipped.chunk_id}' (Requires {skipped.token_count} tokens > Remaining {skipped.remaining_budget} tokens)")
    print(f" -> Strict Budget Verified: Max Projected Total ({prompt_q2.token_accounting['max_projected_total_tokens']}) <= Model Limit ({strict_budget.total_model_limit}) -> {prompt_q2.token_accounting['is_within_budget']}\n")

    demonstrations.append({
        "scenario_id": "SCENARIO_2_TOKEN_BUDGET_ENFORCEMENT",
        "title": "Strict Token Budget Enforcement with Chunk Exclusion",
        "description": "Proves that when candidate chunks exceed the calculated context headroom, the engine sequentially fits what it can and cleanly skips overflowing chunks.",
        "augmented_prompt": prompt_q2.to_dict(),
        "generation_result": gen_q2,
    })

    # --------------------------------------------------------------------------
    # SCENARIO 3: Verbose Source Markers & Multi-Document Injection (Task 3)
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("SCENARIO 3: Multi-Document Context Injection with Verbose Source Markers")
    print("--------------------------------------------------------------------------------")
    injector_verbose = ContextInjector(
        budget_config=TokenBudgetConfig(total_model_limit=4096, max_answer_tokens=400),
        default_marker_style=SourceMarkerStyle.VERBOSE,
    )
    q3 = "How are modern AI applications integrated into enterprise customer service?"
    ai_chunks = [c for c in chunks if "AI" in c.doc_id or "doc" in c.filename.lower()][:2]
    if not ai_chunks:
        ai_chunks = chunks[2:4]

    prompt_q3 = injector_verbose.build_augmented_prompt(
        question=q3,
        retrieved_chunks=ai_chunks,
        role="Enterprise AI Architect",
        marker_style=SourceMarkerStyle.VERBOSE,
    )

    mock_resp_q3 = (
        "Modern enterprise AI applications leverage natural language processing models for automated customer "
        "query routing and 24/7 intelligent tier-1 support [Source 1: doc1.txt | Section: Section 1: AI Fundamentals]."
    )

    gen_q3 = injector_verbose.generate_grounded_answer(
        augmented_prompt=prompt_q3,
        llm_client=llm,
        mock_response=mock_resp_q3,
    )

    print(f" -> Marker Format: VERBOSE (e.g. \"{prompt_q3.assembled_context.injected_chunks[0].source_marker}\")")
    print(f" -> Model Response:\n    \"{gen_q3['grounded_answer']}\"\n")

    demonstrations.append({
        "scenario_id": "SCENARIO_3_VERBOSE_SOURCE_MARKERS",
        "title": "Multi-Document Injected Context with Verbose Source Markers",
        "description": "Demonstrates verbose citation tagging including source filename and document section to support formal audit trails.",
        "augmented_prompt": prompt_q3.to_dict(),
        "generation_result": gen_q3,
    })

    # --------------------------------------------------------------------------
    # SCENARIO 4: Grounding Enforcement on Out-of-Scope Query (Task 4)
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("SCENARIO 4: Grounding Instruction Enforcement (Insufficient Context Handling)")
    print("--------------------------------------------------------------------------------")
    q4 = "What is the quantum computing encryption key rotation protocol for Mars orbital satellites?"
    # Provide unrelated banking chunks
    unrelated_chunks = chunks[:2]

    prompt_q4 = injector_standard.build_augmented_prompt(
        question=q4,
        retrieved_chunks=unrelated_chunks,
        role="Aerospace Security Specialist",
        marker_style=SourceMarkerStyle.NUMBERED,
        enforce_grounding=True,
    )

    mock_resp_q4 = (
        "The provided context does not contain sufficient information to answer this question. "
        "The provided documents pertain only to banking regulations and enterprise applications."
    )

    gen_q4 = injector_standard.generate_grounded_answer(
        augmented_prompt=prompt_q4,
        llm_client=llm,
        mock_response=mock_resp_q4,
    )

    print(f" -> Out-of-Scope Question: \"{q4}\"")
    print(f" -> Strict Refusal/Grounding Response:\n    \"{gen_q4['grounded_answer']}\"\n")

    demonstrations.append({
        "scenario_id": "SCENARIO_4_INSUFFICIENT_CONTEXT_REFUSAL",
        "title": "Grounding Refusal on Insufficient Context",
        "description": "Verifies that when the injected context lacks necessary facts, the grounding instructions enforce an honest refusal rather than a hallucination.",
        "augmented_prompt": prompt_q4.to_dict(),
        "generation_result": gen_q4,
    })

    # --------------------------------------------------------------------------
    # TASK 5: Export Sample Artifacts
    # --------------------------------------------------------------------------
    json_path = os.path.join("outputs", "augmented_prompt_sample.json")
    txt_path = os.path.join("outputs", "augmented_prompt_sample.txt")
    md_path = os.path.join("outputs", "context_injection_report.md")

    injector_standard.export_sample_artifacts(
        demonstration_payloads=demonstrations,
        output_json_path=json_path,
        output_txt_path=txt_path,
        output_md_path=md_path,
    )

    print("--------------------------------------------------------------------------------")
    print(f"[Task 5] Artifacts Successfully Exported:")
    print(f" -> Structured JSON: {json_path}")
    print(f" -> Prompt Sample:   {txt_path}")
    print(f" -> Markdown Report: {md_path}")
    print("================================================================================\n")

    return {
        "status": "success",
        "total_demonstrations": len(demonstrations),
        "demonstrations": demonstrations,
        "exported_files": [json_path, txt_path, md_path],
    }


if __name__ == "__main__":
    run_context_injection_demonstration()
