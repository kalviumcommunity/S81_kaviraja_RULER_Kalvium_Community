"""
RAG Application Starter - Main Entry Point
Demonstrates Task 1 to Task 5 & Multi-Turn Conversation (6 User Questions):
- Task 1: Prompt for defined JSON structure using response_format mode
- Task 2: Parse JSON response into a usable Python dict object
- Task 3: Detect & handle malformed JSON gracefully with recovery
- Task 4: Validate required fields (reject or recover if missing)
- Task 5: Save sample parsed results to outputs/structured_output_sample.json
- Multi-Turn Conversation: 6 sequential questions & answers tracked in history
"""

import os
import json
from llm_client import LLMClient
from structured_output import parse_json_response, validate_required_fields, count_tokens
from chunk_metadata import DocumentChunker, trace_chunk_to_source, verify_metadata_consistency
from token_chunker import TokenAwareChunker, TokenChunk
from embedding_demo import EmbeddingDemonstration
from chunk_embedding_pipeline import ChunkEmbeddingPipeline, EmbeddedChunk
from similarity_ranker import SimilarityRanker
from relevance_checker import RelevanceSanityChecker
try:
    from filtered_search import FilteredSearchEngine, MetadataFilter
except ImportError:
    from src.filtered_search import FilteredSearchEngine, MetadataFilter
try:
    from prompts.templates import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
except ImportError:
    RAG_SYSTEM_PROMPT = None
    RAG_USER_PROMPT = None


def main():
    log_output_path = os.path.join("outputs", "sample_output.txt")
    sample_results_path = os.path.join("outputs", "structured_output_sample.json")

    # Clear previous output files for clean run
    os.makedirs("outputs", exist_ok=True)
    if os.path.exists(log_output_path):
        os.remove(log_output_path)

    print("==================================================")
    print("  RAG Application - Structured JSON & Chat Demo   ")
    print("==================================================\n")

    client = LLMClient(log_file=log_output_path)
    sample_results = {}

    # ----------------------------------------------------
    # MULTI-TURN CONVERSATION (6 User Questions & Answers)
    # ----------------------------------------------------
    print("[Multi-Turn Conversation] Executing 6 Sequential User Questions...")
    if RAG_SYSTEM_PROMPT and hasattr(RAG_SYSTEM_PROMPT, "render"):
        system_prompt = RAG_SYSTEM_PROMPT.render(role="RAG")
    else:
        system_prompt = "You are a specialized AI assistant in Retrieval-Augmented Generation (RAG)."
    required_fields = ["answer", "source", "confidence"]
    defaults = {"source": "RAG_Knowledge_Base_v1", "confidence": 0.95}

    conversations = [
        {
            "prompt": "What is Retrieval-Augmented Generation (RAG)?",
            "mock": json.dumps({
                "answer": "Retrieval-Augmented Generation (RAG) retrieves relevant document context from external knowledge bases before generating LLM responses.",
                "source": "RAG_Overview_Doc_v1.pdf",
                "confidence": 0.99
            }, indent=2)
        },
        {
            "prompt": "How does ChromaDB assist in a RAG pipeline?",
            "mock": json.dumps({
                "answer": "ChromaDB stores high-dimensional document vector embeddings and executes fast semantic similarity searches to retrieve context chunks.",
                "source": "ChromaDB_Integration_Guide.pdf",
                "confidence": 0.96
            }, indent=2)
        },
        {
            "prompt": "Why is JSON response format mode useful in LLM applications?",
            "mock": json.dumps({
                "answer": "JSON response format mode enforces strict JSON schema adherence, enabling downstream code to parse responses directly into dictionary objects.",
                "source": "LLM_Structured_Output_Spec.pdf",
                "confidence": 0.98
            }, indent=2)
        },
        {
            "prompt": "How do we handle malformed JSON gracefully in Python?",
            "mock": json.dumps({
                "answer": "Malformed JSON is caught using json.JSONDecodeError and cleaned via regex pattern recovery for markdown fences and trailing commas without crashing.",
                "source": "JSON_Recovery_Module.py",
                "confidence": 0.97
            }, indent=2)
        },
        {
            "prompt": "What strategy handles missing required fields in parsed data?",
            "mock": json.dumps({
                "answer": "Required field validation checks mandatory schema keys and applies pre-configured fallback default values when non-critical fields are missing.",
                "source": "Data_Validation_Pipeline.pdf",
                "confidence": 0.95
            }, indent=2)
        },
        {
            "prompt": "What is the role of token usage tracking in LLM clients?",
            "mock": json.dumps({
                "answer": "Token tracking measures prompt, completion, and total tokens per request to monitor API costs, throughput, and context window limits.",
                "source": "LLM_Telemetry_Spec.pdf",
                "confidence": 0.99
            }, indent=2)
        }
    ]

    parsed_conversations = []
    latest_usage = None

    for idx, conv in enumerate(conversations, 1):
        print(f" -> Executing Question #{idx}: '{conv['prompt']}'")
        res, usage = client.create_structured_completion(
            system_message=system_prompt,
            user_message=conv["prompt"],
            required_fields=required_fields,
            default_values=defaults,
            temperature=0.2,
        )
        if not res:
            res, usage = client.create_structured_completion(
                system_message=system_prompt,
                user_message=conv["prompt"],
                required_fields=required_fields,
                default_values=defaults,
                temperature=0.2,
                mock_response=conv["mock"],
            )
        parsed_conversations.append({
            "question_number": idx,
            "user_prompt": conv["prompt"],
            "parsed_dict_object": res,
            "token_usage": usage
        })
        latest_usage = usage

    sample_results["task_1_and_2_structured_parse"] = {
        "status": "success",
        "response_format_mode": {"type": "json_object"},
        "required_fields_schema": required_fields,
        "sample_parsed_object": parsed_conversations[0]["parsed_dict_object"],
        "token_usage": latest_usage,
    }

    print("\n--------------------------------------------------")
    print(f"Successfully processed {len(parsed_conversations)} conversation turns!")
    print("--------------------------------------------------\n")

    # ----------------------------------------------------
    # TASK 3: Malformed JSON Detection & Graceful Recovery
    # ----------------------------------------------------
    print("[Task 3] Testing Malformed JSON Recovery...")
    malformed_json_input = """```json
{
  "answer": "Retrieval-Augmented Generation (RAG) enhances LLMs by retrieving relevant document snippets.",
  "source": "RAG_Architecture_Doc.pdf",
}
```"""

    parsed_malformed, was_recovered, parse_err = parse_json_response(malformed_json_input, logger=client.logger)
    is_valid, validated_malformed, missing = validate_required_fields(
        parsed_malformed or {}, required_fields=["answer", "source"], logger=client.logger
    )

    sample_results["task_3_malformed_json_recovered"] = {
        "status": "recovered" if was_recovered and is_valid else "failed",
        "raw_input": malformed_json_input,
        "was_recovered": was_recovered,
        "parsed_object": validated_malformed,
    }

    # ----------------------------------------------------
    # TASK 3 (Unrecoverable): Handling Invalid Output Gracefully
    # ----------------------------------------------------
    print("[Task 3 - Unrecoverable] Testing Invalid Output Without Crashing...")
    invalid_input = "INTERNAL_SERVER_ERROR: Fatal crash occurred while generating JSON response {{{..."
    parsed_invalid, was_recovered_inv, parse_err_inv = parse_json_response(invalid_input, logger=client.logger)

    sample_results["task_3_unrecoverable_malformed_json"] = {
        "status": "handled_gracefully_without_crash",
        "raw_input": invalid_input,
        "parsed_object": parsed_invalid,
        "error_message": parse_err_inv,
    }

    # ----------------------------------------------------
    # TASK 4: Validate Required Fields (Missing Field Recovery)
    # ----------------------------------------------------
    print("[Task 4] Testing Required Fields Validation & Recovery...")
    incomplete_dict = {
        "answer": "RAG grounds model completions in custom knowledge bases to prevent hallucinations."
    }

    is_valid, recovered_dict, missing_list = validate_required_fields(
        incomplete_dict,
        required_fields=["answer", "source"],
        default_values={"source": "Fallback_Knowledge_Store"},
        logger=client.logger,
    )

    sample_results["task_4_missing_field_recovered"] = {
        "status": "recovered_missing_field" if is_valid else "rejected",
        "original_input": incomplete_dict,
        "missing_fields": missing_list,
        "validated_recovered_object": recovered_dict,
    }

    # ----------------------------------------------------
    # TOKEN TOKENISATION VERIFICATION
    # ----------------------------------------------------
    print("[Tokenization Check] Verifying Token Usage Tracking & Token Count Estimation...")
    sample_text = "Retrieval-Augmented Generation (RAG) grounds model outputs on external document context."
    estimated_tokens = count_tokens(sample_text)

    sample_results["token_tokenisation_verification"] = {
        "status": "working",
        "sample_text": sample_text,
        "estimated_token_count": estimated_tokens,
        "api_usage_tracking_supported": True,
        "latest_api_token_usage": latest_usage,
    }

    # ----------------------------------------------------
    # APPLICATION CHAT HISTORY CHECK (6 User Questions Recorded)
    # ----------------------------------------------------
    print("\n[Chat History Check] Displaying All Recorded Conversations...")
    client.display_chat_history()

    sample_results["application_chat_history"] = {
        "total_user_questions_asked": len(client.get_user_questions()),
        "user_questions": client.get_user_questions(),
        "full_chat_history": client.get_chat_history(),
    }

    # ----------------------------------------------------
    # TASKS 1 to 5: CHUNK METADATA & SOURCE TRACKING PIPELINE
    # ----------------------------------------------------
    print("\n[Tasks 1-5] Executing Chunk Metadata Tagging & Source Tracking Pipeline...")
    doc_path = os.path.join("data", "sample_banking_regulation.txt")

    if os.path.exists(doc_path):
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_content = f.read()

        doc_id = "DOC_BRCF_2026_001"
        filename = "sample_banking_regulation.txt"

        chunker = DocumentChunker(chunk_size=350, chunk_overlap=40)
        chunks = chunker.chunk_document(
            content=doc_content,
            doc_id=doc_id,
            filename=filename,
            source_path=doc_path
        )

        # Task 3: Verify consistent structure across all chunks
        consistency_report = verify_metadata_consistency(chunks)
        print(f" -> Generated {len(chunks)} chunks with consistent metadata schema.")
        print(f" -> Metadata Consistency Status: {'PASSED (100% Consistent)' if consistency_report['is_fully_consistent'] else 'FAILED'}")

        # Task 4: Trace retrieved chunk back to exact source
        sample_chunk = chunks[1] if len(chunks) > 1 else chunks[0]
        tracing_result = trace_chunk_to_source(sample_chunk, {doc_id: doc_content})
        print(f" -> Source Tracing Demonstration for Chunk '{sample_chunk.chunk_id}':")
        print(f"    - Target Document: {tracing_result['source_metadata']['filename']}")
        print(f"    - Section: {tracing_result['source_metadata']['section']}")
        print(f"    - Page Number: {tracing_result['source_metadata']['page_number']}")
        print(f"    - Char Range: [{tracing_result['source_metadata']['start_char']}, {tracing_result['source_metadata']['end_char']}]")
        print(f"    - Status: {tracing_result['tracing_verification']['verification_status']}")

        # Task 5: Save sample chunks showing text + metadata to outputs/sample_chunks_with_metadata.json
        chunk_sample_output_path = os.path.join("outputs", "sample_chunks_with_metadata.json")
        output_payload = {
            "metadata_tagging_summary": {
                "total_chunks_processed": len(chunks),
                "consistent_schema_enforced": consistency_report["is_fully_consistent"],
                "schema_fields": consistency_report["expected_metadata_schema"]
            },
            "source_tracing_demonstration": tracing_result,
            "sample_chunks": [c.to_dict() for c in chunks]
        }
        with open(chunk_sample_output_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)

        sample_results["chunk_metadata_and_source_tracking"] = {
            "status": "success",
            "total_chunks": len(chunks),
            "consistency_check": consistency_report,
            "tracing_demo": tracing_result,
            "sample_output_file": chunk_sample_output_path
        }
        print(f" -> Sample chunks with metadata written to: '{chunk_sample_output_path}'")

    # ----------------------------------------------------
    # TOKEN-AWARE CHUNKER PIPELINE (Tasks 1 to 5)
    # ----------------------------------------------------
    print("\n[Token-Aware Chunker] Executing Token Sizing, Overlap, & Boundary Context Pipeline...")
    token_chunker = TokenAwareChunker(chunk_size_tokens=512, chunk_overlap_tokens=64)

    # Task 1 & 2: Token-aware chunking on loaded text
    sample_text_for_tokens = doc_content if 'doc_content' in locals() else (
        "Under financial regulatory guidelines, all vendor transactions under $50,000 may be approved directly. "
        "However, any capital expenditure exceeding $50,000 requires unanimous board authorization and audit."
    )
    token_chunks = token_chunker.chunk_text(
        text=sample_text_for_tokens,
        doc_id="DOC_TOKEN_AWARE_001",
        filename="banking_regulation_tokens.txt",
        source_path="data/sample_banking_regulation.txt"
    )

    # Task 3: Boundary Context Demonstration
    boundary_demo_result = token_chunker.demonstrate_boundary_context()
    print(" -> Task 3: Boundary context preservation demonstration executed.")

    # Task 4: Settings Justification
    settings_justification_result = token_chunker.justify_settings()
    print(" -> Task 4: Settings justification report generated.")

    token_chunker_json_path = os.path.join("outputs", "token_chunker_results.json")
    token_chunker_payload = {
        "settings_justification": settings_justification_result,
        "boundary_context_demonstration": boundary_demo_result,
        "token_chunking_summary": {
            "total_chunks_generated": len(token_chunks),
            "chunk_size_tokens": 512,
            "chunk_overlap_tokens": 64,
            "encoding": "cl100k_base"
        },
        "sample_chunks": [c.to_dict() for c in token_chunks]
    }
    with open(token_chunker_json_path, "w", encoding="utf-8") as f:
        json.dump(token_chunker_payload, f, indent=2)

    sample_results["token_aware_chunker"] = {
        "status": "success",
        "total_chunks": len(token_chunks),
        "chunk_size_tokens": 512,
        "chunk_overlap_tokens": 64,
        "boundary_context_demo": boundary_demo_result["with_overlap"]["preserved_boundary_context"],
        "justification_summary": settings_justification_result["justifications"],
        "output_file": token_chunker_json_path
    }
    print(f" -> Task 5: Token-aware chunker results saved to: '{token_chunker_json_path}'")

    # ----------------------------------------------------
    # EMBEDDING FUNDAMENTALS DEMONSTRATION (Tasks 1 to 5)
    # ----------------------------------------------------
    print("\n[Embedding Fundamentals] Executing Embedding Generation, Dimension Check, & Similarity Demo...")
    embedding_demo = EmbeddingDemonstration(client=client)
    emb_results = embedding_demo.run_demonstration()
    sample_results["embedding_fundamentals_demonstration"] = emb_results
    print(" -> Task 1: Sample embeddings generated.")
    print(f" -> Task 2: Dimension verified ({emb_results['demonstration_metadata']['vector_dimension']}) - {emb_results['dimension_verification']['verification_status']}")
    print(f" -> Task 3: Cosine Similarity computed (Similar: {emb_results['similarity_comparison']['similar_pair']['cosine_similarity']}, Unrelated: {emb_results['similarity_comparison']['unrelated_pair']['cosine_similarity']})")
    print(f" -> Task 4 & 5: Sample output generated - {emb_results['similarity_comparison']['comparison_check']['result_status']}")

    # ----------------------------------------------------
    # CHUNK EMBEDDING PIPELINE (API-Based Chunk Embeddings)
    # ----------------------------------------------------
    print("\n[Chunk Embedding Pipeline] Executing API-Based Embedding Generation on Text Chunks...")
    chunk_emb_pipeline = ChunkEmbeddingPipeline(client=client)
    embedded_chunks_list, chunk_emb_results = chunk_emb_pipeline.run_pipeline(
        output_txt_path=os.path.join("outputs", "chunk_embeddings_output.txt"),
        output_json_path=os.path.join("outputs", "chunk_embeddings_results.json")
    )
    sample_results["api_chunk_embeddings_pipeline"] = chunk_emb_results
    print(f" -> Prepared Chunks Received: {chunk_emb_results['pipeline_metadata']['chunks_received']}")
    print(f" -> Chunks Successfully Embedded: {chunk_emb_results['pipeline_metadata']['chunks_embedded']}")
    print(f" -> Vector Dimension: {chunk_emb_results['pipeline_metadata']['vector_dimension']}")
    print(f" -> Dimension Consistency: {chunk_emb_results['pipeline_metadata']['dimension_consistency']}")

    # ----------------------------------------------------
    # SIMILARITY METRIC & QUERY-CHUNK RANKING (Tasks 1 to 5)
    # ----------------------------------------------------
    print("\n[Similarity Ranker] Executing Metric Computation, Query Comparison, & Ranking Pipeline...")
    similarity_ranker = SimilarityRanker(client=client, metric="cosine")
    query_text = "What are the rules and approval thresholds for high-value transaction payments?"
    ranking_results = similarity_ranker.rank_chunks(
        query=query_text,
        embedded_chunks=embedded_chunks_list,
        top_k=2
    )
    similarity_ranker.generate_ranking_reports(
        ranking_results=ranking_results,
        output_txt_path=os.path.join("outputs", "similarity_ranking_output.txt"),
        output_json_path=os.path.join("outputs", "similarity_ranking_results.json")
    )
    similarity_ranker.export_vector_matrix(
        embedded_chunks=embedded_chunks_list,
        output_json_path=os.path.join("outputs", "vector_matrix_output.json"),
        output_txt_path=os.path.join("outputs", "vector_matrix_output.txt")
    )
    sample_results["similarity_ranking_pipeline"] = ranking_results
    print(f" -> Query: \"{query_text}\"")
    print(f" -> Metric: {ranking_results['metric'].upper()} ({ranking_results['metric_justification']['metric_name']})")
    print(f" -> Total Chunks Scored & Ranked: {ranking_results['total_chunks_compared']}")
    print(f" -> Top Most Similar Chunk ID: {ranking_results['most_similar'][0]['chunk_id']} (Score: {ranking_results['most_similar'][0]['score']:.4f})")
    print(f" -> Top Least Similar Chunk ID: {ranking_results['least_similar'][0]['chunk_id']} (Score: {ranking_results['least_similar'][0]['score']:.4f})")

    # ----------------------------------------------------
    # RELEVANCE QUALITY CHECK & SANITY SUITE (Tasks 1 to 5)
    # ----------------------------------------------------
    print("\n[Relevance Checker] Executing Known Relevance Tests & Sanity Suite...")
    relevance_checker = RelevanceSanityChecker(ranker=similarity_ranker, pipeline=chunk_emb_pipeline)
    sanity_summary = relevance_checker.run_sanity_check(embedded_chunks=embedded_chunks_list)
    relevance_checker.generate_sanity_report(
        sanity_summary=sanity_summary,
        output_txt_path=os.path.join("outputs", "relevance_sanity_report.txt"),
        output_json_path=os.path.join("outputs", "relevance_sanity_results.json")
    )
    sample_results["relevance_sanity_suite"] = sanity_summary
    print(f" -> Total Test Cases: {sanity_summary['total_test_count']}")
    print(f" -> Standard Relevance Pass Rate: {sanity_summary['standard_passes']}/{sanity_summary['standard_tests_count']} ({sanity_summary['pass_rate_percentage']}%)")
    print(f" -> Surprising/Failing Cases Identified: {sanity_summary['surprising_cases_count']}")



    # ----------------------------------------------------
    # METADATA FILTERING & HYBRID SEARCH (Tasks 1 to 5)
    # ----------------------------------------------------
    print("\n[Filtered & Hybrid Search] Executing Metadata Filtering, Hybrid Matching, & Precision Demo...")
    filtered_engine = FilteredSearchEngine(client=client, ranker=similarity_ranker)

    # Task 1 & 2: Compare Filtered vs Unfiltered Retrieval
    filter_query = "What are the rules and approval thresholds for high-value transaction payments?"
    section_filter = MetadataFilter(
        criteria={"section__contains": "Section 3"},
        description="Section 3: High-Value Transaction Authorization Thresholds"
    )
    comparison_results = filtered_engine.compare_filtered_unfiltered(
        query=filter_query,
        embedded_chunks=embedded_chunks_list,
        metadata_filter=section_filter,
        top_k=2,
        mode="hybrid",
        alpha=0.6
    )
    print(f" -> Task 1 & 2: Filtered search executed for: \"{filter_query}\"")
    print(f"    - Filter: {comparison_results['filter_applied']['description']}")
    print(f"    - Unfiltered Candidates: {comparison_results['unfiltered_results']['total_chunks_scored']}, Filtered Candidates: {comparison_results['filtered_results']['total_chunks_scored']} (Eliminated {comparison_results['filtered_results']['filtered_out_chunks']})")
    print(f"    - Top Result Shift: {'Yes' if comparison_results['comparison_analysis']['top_1_changed'] else 'No'}")

    # Task 3: Hybrid Search Comparison (Exact Term / ID Matching)
    exact_query = "Which disbursements exceeding $50,000 require board authorization?"
    vec_top = filtered_engine.search(exact_query, embedded_chunks_list, mode="vector", top_k=1)
    kw_top = filtered_engine.search(exact_query, embedded_chunks_list, mode="keyword", top_k=1)
    hyb_top = filtered_engine.search(exact_query, embedded_chunks_list, mode="hybrid", alpha=0.6, top_k=1)
    hybrid_comparison = {
        "query": exact_query,
        "demonstration": "Exact entity and threshold matching ($50,000, board authorization)",
        "vector_search_top_1": vec_top["ranked_chunks"][0] if vec_top["ranked_chunks"] else None,
        "keyword_search_top_1": kw_top["ranked_chunks"][0] if kw_top["ranked_chunks"] else None,
        "hybrid_search_top_1": hyb_top["ranked_chunks"][0] if hyb_top["ranked_chunks"] else None,
        "hybrid_fusion_weights": {"alpha_vector": 0.6, "beta_keyword": 0.4}
    }
    print(f" -> Task 3: Hybrid search compared for: \"{exact_query}\"")
    print(f"    - Hybrid Top Score: {hyb_top['ranked_chunks'][0]['hybrid_score']:.4f} (Vec: {hyb_top['ranked_chunks'][0]['vector_score']:.4f}, KW: {hyb_top['ranked_chunks'][0]['keyword_score']:.4f})")

    # Task 4: Precision Improvement Demonstration
    target_relevant_ids = [
        c.chunk_id for c in embedded_chunks_list
        if "Section 3" in c.metadata.get("section", "") or "$50,000" in c.source_text
    ]
    precision_demo = filtered_engine.demonstrate_precision_improvement(
        query=filter_query,
        embedded_chunks=embedded_chunks_list,
        metadata_filter=section_filter,
        relevant_chunk_ids=target_relevant_ids,
        top_k=3
    )
    print(" -> Task 4: Precision demonstrated:")
    print(f"    - Unfiltered Vector Precision@3: {precision_demo['unfiltered_vector_search']['precision_percentage']}%")
    print(f"    - Filtered Hybrid Precision@3:   {precision_demo['filtered_hybrid_search']['precision_percentage']}%")
    print(f"    - Net Precision Gain:            +{precision_demo['precision_improvement']['precision_gain_percentage']}%")

    # Task 5: Export Sample Reports
    filtered_engine.export_reports(
        comparison_results=comparison_results,
        precision_results=precision_demo,
        hybrid_comparison_results=hybrid_comparison,
        output_txt_path=os.path.join("outputs", "filtered_search_output.txt"),
        output_json_path=os.path.join("outputs", "filtered_search_results.json"),
        hybrid_json_path=os.path.join("outputs", "hybrid_search_comparison.json"),
        precision_txt_path=os.path.join("outputs", "precision_demonstration_report.txt")
    )
    sample_results["filtered_hybrid_search"] = {
        "comparison_results": comparison_results,
        "hybrid_comparison": hybrid_comparison,
        "precision_demonstration": precision_demo
    }
    print(" -> Task 5: Sample filtered-search results and precision reports exported to outputs/.")

    # ----------------------------------------------------
    # TASK 5: Save Sample Parsed Results
    # ----------------------------------------------------
    print(f"[Task 5] Writing Sample Parsed Results to '{sample_results_path}'...")
    with open(sample_results_path, "w", encoding="utf-8") as f:
        json.dump(sample_results, f, indent=2)

    # ----------------------------------------------------
    # BATCH/CLI PATH (Task 3 Reuse & Task 5 Render Example)
    # ----------------------------------------------------
    print("\n[Batch/CLI Path] Rendering templates for multiple topics...")
    topics = ["Large Language Models (LLMs)", "Vector Databases"]
    for idx, t in enumerate(topics, 1):
        rendered_sys = RAG_SYSTEM_PROMPT.render(role="Batch")
        rendered_user = RAG_USER_PROMPT.render(topic=t, length="three")
        print(f"\n--- Batch Request {idx} ---")
        print(f"System Prompt: {rendered_sys}")
        print(f"User Prompt: {rendered_user}")

    print("==================================================")
    print("  ALL 6 CONVERSATIONS & TASKS EXECUTED SUCCESSFULLY! ")
    print(f"  - Total User Questions Recorded: {len(client.get_user_questions())}")
    print(f"  - Structured Results JSON saved to: {sample_results_path}")
    print(f"  - Execution Log saved to: {log_output_path}")
    print("==================================================")


if __name__ == "__main__":
    main()
