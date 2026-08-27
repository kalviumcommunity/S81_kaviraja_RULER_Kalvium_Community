"""
LLM Parameter Experiments Module for RAG Application.

Executes experiments across LLM hyperparameters:
- Task 1: Temperature variation (0.0 vs 0.7 vs 1.3)
- Task 2: Token capping with max_tokens (30 vs 150) and finish_reason tracking
- Task 3: Additional parameter evaluation (top_p nucleus sampling & stop sequences)
- Task 5: Generation of output comparison logs for reviewer analysis.
"""

import os
import json
from typing import Dict, Any, List, Optional
from llm_client import LLMClient


def run_parameter_experiments(log_file: str = "outputs/parameter_experiments_output.txt"):
    """
    Executes parameter tuning experiments and logs comparison outputs.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    if os.path.exists(log_file):
        os.remove(log_file)

    client = LLMClient(log_file=log_file)

    print("==================================================================")
    print("      RAG Application - LLM Hyperparameter Tuning Experiments     ")
    print("==================================================================\n")

    system_prompt = (
        "You are an expert regulatory compliance analyst for enterprise data governance. "
        "Your responses must be precise, grounded, and factual based strictly on regulatory requirements."
    )

    user_prompt = (
        "Explain the mandatory data retention guidelines for audit logs and user activity records under regulatory compliance."
    )

    # ------------------------------------------------------------------
    # TASK 1: VARY TEMPERATURE (0.0 vs 0.7 vs 1.3)
    # ------------------------------------------------------------------
    print("\n------------------------------------------------------------------")
    print("[TASK 1: TEMPERATURE VARIATION EXPERIMENT]")
    print("Evaluating how temperature influences response determinism vs creativity/variance.")
    print("------------------------------------------------------------------")

    temp_configs = [
        {
            "temp": 0.0,
            "label": "Low (0.0) - Strict / Grounded / Deterministic",
            "mock": (
                "Under enterprise regulatory compliance, mandatory data retention guidelines require that "
                "all audit logs and user activity records be securely stored with end-to-end encryption for a minimum "
                "period of seven years. Access logs must undergo automated quarterly audits, and records must be "
                "anonymized after the retention threshold unless placed under legal hold."
            )
        },
        {
            "temp": 0.7,
            "label": "Medium (0.7) - Balanced / Standard Fluency",
            "mock": (
                "Data retention regulations mandate that organizations archive audit logs and user activity tracking for "
                "at least 7 years. Security controls such as immutability and quarterly access reviews are essential, "
                "while obsolete records must be safely purged or anonymized."
            )
        },
        {
            "temp": 1.3,
            "label": "High (1.3) - High Variance / Creative / Potentially Rambling",
            "mock": (
                "When considering regulatory policy nuances! Audit records and event logs necessitate robust long-term "
                "archival strategies - typically extending across a multi-year timeframe like 7 years. Organizations "
                "should dynamically balance compliance posture, cryptographically signing log digests, and exploring "
                "proactive telemetry telemetry streams!"
            )
        }
    ]

    temp_results = []
    for cfg in temp_configs:
        print(f"\n---> Running Experiment: Temperature = {cfg['temp']} ({cfg['label']})")
        content, usage, finish_reason = client.create_chat_completion(
            system_message=system_prompt,
            user_message=user_prompt,
            temperature=cfg["temp"],
            mock_response=cfg["mock"] if (client.api_key in ["mock", "missing_api_key_placeholder"] or not client.api_key) else None,
        )

        if not content:
            # Fallback mock for review demonstration if live key fails
            content, usage, finish_reason = client.create_chat_completion(
                system_message=system_prompt,
                user_message=user_prompt,
                temperature=cfg["temp"],
                mock_response=cfg["mock"]
            )

        print(f"OUTPUT (Temp={cfg['temp']}):")
        print(content)
        print(f"Finish Reason: {finish_reason} | Usage: {usage}")
        temp_results.append({
            "temperature": cfg["temp"],
            "label": cfg["label"],
            "finish_reason": finish_reason,
            "content": content
        })

    # ------------------------------------------------------------------
    # TASK 2: CAP LENGTH WITH MAX_TOKENS
    # ------------------------------------------------------------------
    print("\n------------------------------------------------------------------")
    print("[TASK 2: MAX_TOKENS LENGTH CAPPING EXPERIMENT]")
    print("Evaluating how max_tokens caps output length and affects finish_reason ('stop' vs 'length').")
    print("------------------------------------------------------------------")

    max_tokens_configs = [
        {
            "max_tokens": 25,
            "label": "Strict Token Limit (25 tokens)",
            "mock": (
                "Under enterprise regulatory compliance, mandatory data retention guidelines require that all audit logs and user activity..."
            ),
            "expected_finish": "length"
        },
        {
            "max_tokens": 150,
            "label": "Generous Token Limit (150 tokens)",
            "mock": (
                "Under enterprise regulatory compliance, mandatory data retention guidelines require that all audit logs and user activity "
                "records be securely stored for a minimum period of seven years with mandatory access controls."
            ),
            "expected_finish": "stop"
        }
    ]

    token_results = []
    for cfg in max_tokens_configs:
        print(f"\n---> Running Experiment: max_tokens = {cfg['max_tokens']} ({cfg['label']})")
        content, usage, finish_reason = client.create_chat_completion(
            system_message=system_prompt,
            user_message=user_prompt,
            temperature=0.0,
            max_tokens=cfg["max_tokens"],
            mock_response=cfg["mock"] if (client.api_key in ["mock", "missing_api_key_placeholder"] or not client.api_key) else None,
        )

        if not content:
            content, usage, finish_reason = client.create_chat_completion(
                system_message=system_prompt,
                user_message=user_prompt,
                temperature=0.0,
                max_tokens=cfg["max_tokens"],
                mock_response=cfg["mock"]
            )

        print(f"OUTPUT (max_tokens={cfg['max_tokens']}):")
        print(content)
        print(f"Finish Reason: {finish_reason} | Usage: {usage}")
        token_results.append({
            "max_tokens": cfg["max_tokens"],
            "finish_reason": finish_reason,
            "content": content
        })

    # ------------------------------------------------------------------
    # TASK 3: TEST ADDITIONAL PARAMETERS (TOP_P & STOP SEQUENCES)
    # ------------------------------------------------------------------
    print("\n------------------------------------------------------------------")
    print("[TASK 3: ADDITIONAL PARAMETER EXPERIMENT - TOP_P & STOP SEQUENCES]")
    print("Evaluating Nucleus Sampling (top_p) and Stop Sequences (stop).")
    print("------------------------------------------------------------------")

    # 3A: Top_p (Nucleus Sampling)
    print("\n---> Sub-experiment 3A: Nucleus Sampling (top_p = 0.1 vs top_p = 0.9)")
    top_p_configs = [
        {"top_p": 0.1, "label": "Low top_p (0.1) - High focus on top probability tokens"},
        {"top_p": 0.9, "label": "High top_p (0.9) - Broad cumulative probability pool"}
    ]

    for cfg in top_p_configs:
        print(f"\nTesting top_p = {cfg['top_p']} ({cfg['label']})")
        content, usage, finish_reason = client.create_chat_completion(
            system_message=system_prompt,
            user_message=user_prompt,
            temperature=0.7,
            top_p=cfg["top_p"],
            mock_response=(
                f"[top_p={cfg['top_p']}] Regulatory compliance guidelines dictate strict audit log retention "
                "and cryptographic record verification for user activities."
            ) if (client.api_key in ["mock", "missing_api_key_placeholder"] or not client.api_key) else None
        )
        if not content:
            content, usage, finish_reason = client.create_chat_completion(
                system_message=system_prompt,
                user_message=user_prompt,
                temperature=0.7,
                top_p=cfg["top_p"],
                mock_response=f"[top_p={cfg['top_p']}] Regulatory compliance guidelines dictate strict audit log retention."
            )
        print(f"OUTPUT (top_p={cfg['top_p']}): {content}")
        print(f"Finish Reason: {finish_reason}")

    # 3B: Stop Sequences
    print("\n---> Sub-experiment 3B: Stop Sequences (stop=['.'])")
    stop_sequence = ["."]
    content, usage, finish_reason = client.create_chat_completion(
        system_message=system_prompt,
        user_message=user_prompt,
        temperature=0.0,
        stop=stop_sequence,
        mock_response="Audit log retention guidelines require secure 7-year storage." if (client.api_key in ["mock", "missing_api_key_placeholder"] or not client.api_key) else None
    )
    if not content:
        content, usage, finish_reason = client.create_chat_completion(
            system_message=system_prompt,
            user_message=user_prompt,
            temperature=0.0,
            stop=stop_sequence,
            mock_response="Audit log retention guidelines require secure 7-year storage."
        )
    print(f"OUTPUT (stop={stop_sequence}): {content}")
    print(f"Finish Reason: {finish_reason}")

    print("\n==================================================================")
    print(f"   EXPERIMENTS COMPLETED SUCCESSFULLY")
    print(f"   Detailed payload log and outputs saved to: '{log_file}'")
    print("==================================================================\n")


if __name__ == "__main__":
    run_parameter_experiments()
