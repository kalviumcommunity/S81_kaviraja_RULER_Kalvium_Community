"""
RAG Application Starter - Main Entry Point
Demonstrates Task 1 to Task 5:
- Task 1: Prompt for defined JSON structure using response_format mode
- Task 2: Parse JSON response into a usable Python dict object
- Task 3: Detect & handle malformed JSON gracefully with recovery
- Task 4: Validate required fields (reject or recover if missing)
- Task 5: Save sample parsed results to outputs/structured_output_sample.json
"""

import os
import json
from llm_client import LLMClient
from structured_output import parse_json_response, validate_required_fields
from prompts.templates import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT


def main():
    log_output_path = os.path.join("outputs", "sample_output.txt")
    sample_results_path = os.path.join("outputs", "structured_output_sample.json")

    # Clear previous output files for clean run
    os.makedirs("outputs", exist_ok=True)
    if os.path.exists(log_output_path):
        os.remove(log_output_path)

    print("==================================================")
    print("  RAG Application - Structured JSON Output Demo   ")
    print("==================================================\n")

    client = LLMClient(log_file=log_output_path)
    sample_results = {}

    # ----------------------------------------------------
    # TASK 1 & 2: Prompt for Defined JSON & Parse into Dict (Chat Path)
    # ----------------------------------------------------
    print("[Task 1 & 2] Executing Structured JSON Completion & Parsing (Chat Path)...")
    system_prompt = RAG_SYSTEM_PROMPT.render(role="RAG")
    user_prompt = RAG_USER_PROMPT.render(topic="Retrieval-Augmented Generation (RAG)", length="two")
    required_fields = ["answer", "source", "confidence"]
    defaults = {"source": "RAG_Knowledge_Base_v1", "confidence": 0.95}

    structured_result, usage = client.create_structured_completion(
        system_message=system_prompt,
        user_message=user_prompt,
        required_fields=required_fields,
        default_values=defaults,
        temperature=0.2,
    )

    # If live API returns error (e.g. placeholder API key), generate demonstration mock output
    if not structured_result:
        print("\n[Notice]: Live API returned error (e.g. invalid API key). Generating mock structured response for demonstration...")
        mock_payload = json.dumps({
            "answer": "Retrieval-Augmented Generation (RAG) enhances LLMs by retrieving relevant document context before generating answers.",
            "source": "RAG_Technical_Spec_v1.pdf",
            "confidence": 0.98
        }, indent=2)

        structured_result, usage = client.create_structured_completion(
            system_message=system_prompt,
            user_message=user_prompt,
            required_fields=required_fields,
            default_values=defaults,
            temperature=0.2,
            mock_response=mock_payload,
        )

    sample_results["task_1_and_2_structured_parse"] = {
        "status": "success" if structured_result else "failed",
        "response_format_mode": {"type": "json_object"},
        "required_fields_schema": required_fields,
        "parsed_object": structured_result,
        "token_usage": usage,
    }

    print(f"Parsed Dict Object (Type: {type(structured_result).__name__}):")
    print(json.dumps(structured_result, indent=2))
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

    print("Raw Malformed Input (Contains Markdown & Trailing Comma):")
    print(malformed_json_input)

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

    print(f"\nRecovered Object (Type: {type(validated_malformed).__name__}, Was Recovered: {was_recovered}):")
    print(json.dumps(validated_malformed, indent=2))
    print("--------------------------------------------------\n")

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

    print(f"Unrecoverable Handling Result: parsed_object={parsed_invalid}, error='{parse_err_inv}'")
    print("--------------------------------------------------\n")

    # ----------------------------------------------------
    # TASK 4: Validate Required Fields (Missing Field Recovery)
    # ----------------------------------------------------
    print("[Task 4] Testing Required Fields Validation & Recovery...")
    incomplete_dict = {
        "answer": "RAG grounds model completions in custom knowledge bases to prevent hallucinations."
        # "source" field is missing!
    }

    print("Input Dict Missing 'source' Field:")
    print(json.dumps(incomplete_dict, indent=2))

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

    print(f"\nValidated Recovered Object (Missing Fields: {missing_list}):")
    print(json.dumps(recovered_dict, indent=2))
    print("--------------------------------------------------\n")

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
    print("  ALL 5 TASKS EXECUTED SUCCESSFULLY!              ")
    print(f"  - Structured Results JSON saved to: {sample_results_path}")
    print(f"  - Execution Log saved to: {log_output_path}")
    print("==================================================")


if __name__ == "__main__":
    main()
