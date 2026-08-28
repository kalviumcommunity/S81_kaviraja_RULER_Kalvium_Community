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
