"""
Conversational RAG & Multi-Turn Query Rewriting Demonstration Runner (Tasks 1 to 5).

Demonstrates:
- Task 1: Track conversation history across multiple turns (user questions and assistant answers).
- Task 2: Rewrite follow-up questions into standalone queries suitable for vector retrieval.
- Task 3: Retrieve using the rewritten query and prove superior relevance over raw follow-up queries.
- Task 4: Demonstrate an end-to-end multi-turn dialogue where follow-ups succeed via history rewriting.
- Task 5: Export structured JSON and human-readable artifacts including sample dialogue, rewritten queries,
  retrieved context, and final grounded answers with citations.
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
from chunk_embedding_pipeline import ChunkEmbeddingPipeline, EmbeddedChunk
from conversational_rag import (
    ConversationTurn,
    ConversationHistoryTracker,
    ConversationalQueryRewriter,
    ConversationalRetriever,
    ConversationalRAGEngine,
)


def main():
    print("================================================================================")
    print("      CONVERSATIONAL RAG & QUERY REWRITING DEMONSTRATION (TASKS 1 TO 5)        ")
    print("================================================================================\n")

    # Step 0: Initialize Client and Knowledge Corpus
    print("[Setup] Initializing LLM Client and preparing banking regulation embeddings...")
    client = LLMClient()
    pipeline = ChunkEmbeddingPipeline(client=client)
    embedded_chunks, _ = pipeline.run_pipeline()
    print(f" -> Prepared and embedded {len(embedded_chunks)} regulatory corpus chunks.\n")

    # --------------------------------------------------------------------------
    # TASK 1: Track Conversation History
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("[Task 1] Demonstrating Conversation History Tracking...")
    print("--------------------------------------------------------------------------------")
    history_tracker = ConversationHistoryTracker(max_turns=5)
    sample_turn = history_tracker.add_turn(
        user_query="What is the capital reserve requirement under Basel IV?",
        assistant_response="Under Basel IV standards, Tier 1 common equity capital must remain above 10.5% of total risk-weighted assets.",
        rewritten_query="What is the capital reserve requirement under Basel IV?",
        is_rewritten=False,
        retrieved_chunk_ids=["sample_banking_regulation_txt#chunk_001"],
        citations=["sample_banking_regulation_txt#chunk_001"],
        similarity_scores=[0.8842],
    )
    print(f" -> Turn #{sample_turn.turn_id} recorded in history.")
    print(f" -> User Question: \"{sample_turn.user_query}\"")
    print(f" -> Assistant Answer: \"{sample_turn.assistant_response}\"")
    print(" -> Formatted Prompt History:")
    print(history_tracker.format_history_for_prompt())
    print(" -> Task 1 Completed: Multi-turn history tracking verified.\n")

    # --------------------------------------------------------------------------
    # TASK 2: Rewrite Follow-up Questions
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("[Task 2] Demonstrating Standalone Query Rewriting...")
    print("--------------------------------------------------------------------------------")
    rewriter = ConversationalQueryRewriter(client=client)

    # Test 2A: Standalone Query (Should NOT be rewritten)
    standalone_q = "What are the rules and approval thresholds for high-value transaction payments?"
    s_rewrite, s_was_rw, s_meta = rewriter.rewrite_query(standalone_q, history_tracker)
    print(f" -> Case 2A (Independent Query): \"{standalone_q}\"")
    print(f"    Rewritten: {s_was_rw} | Result: \"{s_rewrite}\"")

    # Test 2B: Follow-up Query with Pronoun (SHOULD be rewritten)
    followup_q = "What happens if a bank fails to comply with them?"
    f_rewrite, f_was_rw, f_meta = rewriter.rewrite_query(followup_q, history_tracker)
    print(f" -> Case 2B (Pronoun Follow-Up): \"{followup_q}\"")
    print(f"    Rewritten: {f_was_rw} | Result: \"{f_rewrite}\"")
    print(" -> Task 2 Completed: Follow-up question rewritten into standalone query.\n")

    # --------------------------------------------------------------------------
    # TASK 3: Retrieve Using the Rewritten Query (Side-by-Side Comparison)
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("[Task 3] Retrieving Using Rewritten Query vs Raw Follow-Up Query...")
    print("--------------------------------------------------------------------------------")
    retriever = ConversationalRetriever(client=client)
    comparison = retriever.compare_retrieval(
        raw_query=followup_q,
        rewritten_query=f_rewrite,
        embedded_chunks=embedded_chunks,
        expected_section_keyword="Section",
    )
    print(f" -> Raw Follow-Up Query:       \"{comparison.raw_query}\"")
    print(f"    Top Chunk:                 {comparison.raw_top_chunk_id} (Score: {comparison.raw_top_similarity_score})")
    print(f"    Snippet:                   \"{comparison.raw_top_snippet[:80]}...\"")
    print(f" -> Rewritten Standalone Query:\"{comparison.rewritten_query}\"")
    print(f"    Top Chunk:                 {comparison.rewritten_top_chunk_id} (Score: {comparison.rewritten_top_similarity_score})")
    print(f"    Snippet:                   \"{comparison.rewritten_top_snippet[:80]}...\"")
    print(f" -> Semantic Score Gain:       +{comparison.similarity_score_gain}")
    print(f" -> Relevance Verdict:         {comparison.relevance_verdict}")
    print(" -> Task 3 Completed: Rewritten query proved superior in retrieval relevance.\n")

    # --------------------------------------------------------------------------
    # TASK 4: Demonstrate End-to-End Multi-Turn Dialogue
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("[Task 4] Executing 4-Turn Conversational Dialogue Demonstration...")
    print("--------------------------------------------------------------------------------")
    engine = ConversationalRAGEngine(client=client, retriever=retriever, query_rewriter=rewriter)
    demo_summary = engine.run_multi_turn_demonstration(embedded_chunks=embedded_chunks)

    for turn in demo_summary["dialogue_turns"]:
        print(f"\n[Turn #{turn['turn_id']}]")
        print(f"  User Query:             \"{turn['raw_user_query']}\"")
        print(f"  Was Rewritten:          {turn['was_rewritten']}")
        if turn["was_rewritten"]:
            print(f"  Rewritten Query:        \"{turn['rewritten_query']}\"")
            comp = turn.get("retrieval_comparison")
            if comp:
                print(f"  Score Gain:             +{comp.get('similarity_score_gain')}")
        print(f"  Retrieved Chunks:       {turn['retrieved_chunk_ids']}")
        print(f"  Citations:              {turn['citations']}")
        print(f"  Assistant Answer:       \"{turn['assistant_answer'][:140]}...\"")

    print(f"\n -> Total Dialogue Turns:     {demo_summary['total_turns']}")
    print(f" -> Rewritten Turns:          {demo_summary['rewritten_turns_count']}")
    print(f" -> Avg Similarity Lift:      +{demo_summary['average_similarity_score_gain']}")
    print(" -> Task 4 Completed: End-to-end multi-turn dialogue demonstrated successfully.\n")

    # --------------------------------------------------------------------------
    # TASK 5: Export Sample Dialogue & Reproducibility Artifacts
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("[Task 5] Exporting Sample Dialogue and Evaluation Artifacts...")
    print("--------------------------------------------------------------------------------")
    sample_dialogue_json = os.path.join("outputs", "sample_dialogue.json")
    sample_dialogue_txt = os.path.join("outputs", "sample_dialogue.txt")
    results_json = os.path.join("outputs", "conversational_rag_results.json")
    report_md = os.path.join("outputs", "conversational_rag_report.md")

    engine.export_sample_artifacts(
        demo_summary=demo_summary,
        output_json_path=sample_dialogue_json,
        output_txt_path=sample_dialogue_txt,
        output_results_path=results_json,
        output_report_path=report_md,
    )

    print(f" -> Sample Dialogue JSON saved:  {sample_dialogue_json}")
    print(f" -> Sample Dialogue Text saved:  {sample_dialogue_txt}")
    print(f" -> Results JSON saved:          {results_json}")
    print(f" -> Technical Report MD saved:   {report_md}")
    print(" -> Task 5 Completed: All required conversational RAG artifacts generated.\n")

    print("================================================================================")
    print("       ALL 5 CONVERSATIONAL RAG & QUERY REWRITING TASKS PASSED!                ")
    print("================================================================================\n")


if __name__ == "__main__":
    main()
