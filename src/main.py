"""
RAG Application Starter - Multi-Turn Conversation & History Management
Demonstrates history tracking, token measurement before requests,
and trimming/summarising strategies to keep requests within token budgets.
"""

import os
import json
from llm_client import LLMClient
from history_manager import HistoryManager


def run_overflowing_conversation_demo(strategy: str = "trim", token_budget: int = 600, log_file: str = "outputs/sample_output.txt"):
    """
    Executes a multi-turn conversation scenario with retrieved document chunks.
    Demonstrates token measurement before each call and budget enforcement via trim/summarise.
    """
    print(f"\n==================================================================")
    print(f"   DEMONSTRATING MULTI-TURN HISTORY MANAGEMENT ({strategy.upper()} STRATEGY)")
    print(f"   Token Budget Threshold: {token_budget} tokens")
    print(f"==================================================================\n")

    client = LLMClient(log_file=log_file)
    system_prompt = (
        "You are an expert AI assistant specializing in analyzing regulatory compliance "
        "and Community Standard guidelines for organizational policies."
    )

    history_mgr = HistoryManager(
        system_prompt=system_prompt,
        max_token_budget=token_budget,
        strategy=strategy,
        model_name=client.model_name,
        logger=client.logger,
    )

    # Multi-turn conversation data containing queries and retrieved document chunks
    turns_data = [
        {
            "query": "What are the core requirements for data privacy compliance?",
            "chunks": [
                "Document Regulatory Ref #101: All organizations processing user data must maintain strict end-to-end encryption at rest and in transit. Access permissions must follow the principle of least privilege, requiring quarterly access reviews.",
                "Document Compliance Ref #102: Data retention policies specify that user identification log files must be scrubbed or anonymized after 90 days unless subject to a legal legal hold.",
            ],
            "mock_reply": "Core data privacy requirements include end-to-end encryption at rest and in transit, least-privilege access control with quarterly reviews, and anonymization of user logs after 90 days."
        },
        {
            "query": "How are security breaches reported and handled under these standards?",
            "chunks": [
                "Incident Response Clause #201: Any suspected or confirmed data breach must be reported to the compliance officer within 24 hours of discovery. Affected users and relevant authorities must be notified within 72 hours.",
                "Incident Response Clause #202: A post-incident post-mortem root cause analysis report must be finalized within 14 business days of incident resolution.",
            ],
            "mock_reply": "Security breaches must be reported to the compliance officer within 24 hours and affected users within 72 hours. A full post-mortem report is required within 14 business days."
        },
        {
            "query": "What are the audit penalties for failing quarterly access reviews?",
            "chunks": [
                "Audit Enforcement Policy #301: Failure to conduct quarterly access reviews results in a Tier-2 compliance violation. Organizations face mandatory mandatory remediation within 30 days and temporary suspension of administrative API access.",
                "Audit Enforcement Policy #302: Repeated non-compliance across two consecutive audit cycles escalates the penalty to Tier-1, resulting in formal regulatory review and potential certification revocation.",
            ],
            "mock_reply": "Failing quarterly access reviews results in a Tier-2 violation requiring remediation within 30 days and temporary API suspension. Repeated failure escalates to Tier-1 with potential certification revocation."
        },
        {
            "query": "Can you summarize our discussion on incident reporting times and audit penalties?",
            "chunks": [
                "Summary Query Context: User requests cross-turn synthesis of breach reporting timelines (24h internal, 72h external) and audit failure escalation steps (Tier-2 30-day fix vs Tier-1 revocation).",
            ],
            "mock_reply": "In summary: Incidents require internal notification in 24h and external in 72h. Failing access reviews starts at Tier-2 (30-day fix + API pause) and escalates to Tier-1 (revocation) if repeated."
        },
        {
            "query": "What is the final escalation step if Tier-1 violations are not addressed?",
            "chunks": [
                "Audit Enforcement Policy #303: Unresolved Tier-1 violations lead to immediate revocation of operational credentials, mandatory public disclosure, and referral to statutory enforcement agencies.",
            ],
            "mock_reply": "If Tier-1 violations remain unresolved, final escalation involves immediate revocation of operational credentials, mandatory public disclosure, and statutory enforcement referral."
        }
    ]

    # Task 1 & Task 4: Execute multi-turn chat loop
    for turn_num, turn in enumerate(turns_data, 1):
        print(f"\n------------------------------------------------------------------")
        print(f"[TURN {turn_num}]: Processing User Request")
        print(f"------------------------------------------------------------------")

        # Task 1: Add user message with retrieved document chunks
        history_mgr.add_user_message(user_query=turn["query"], doc_chunks=turn["chunks"])

        # Task 2: Measure total token count of history BEFORE sending request
        naive_tokens = history_mgr.get_total_tokens()
        print(f"[PRE-CALL MEASUREMENT] Naive History Message Count: {len(history_mgr.get_history())}")
        print(f"[PRE-CALL MEASUREMENT] Total Naive Token Count: {naive_tokens} tokens (Budget: {token_budget} tokens)")

        # Task 3: Enforce token budget (Trim or Summarise older turns, ALWAYS preserving system message)
        was_managed, pre_tokens, post_tokens = history_mgr.enforce_budget()

        if was_managed:
            print(f"[HISTORY MANAGEMENT APPLIED - {strategy.upper()}]:")
            print(f"   - Naive token count of {pre_tokens} exceeded budget of {token_budget}.")
            print(f"   - Preserved system message at index 0.")
            print(f"   - Adjusted message count to {len(history_mgr.get_history())} | New token count: {post_tokens} tokens.")
        else:
            print(f"[OK] Token count ({post_tokens}) is within budget limit ({token_budget}). No trimming needed.")

        # Send request with active managed history payload
        current_messages = history_mgr.get_history()
        print(f"\n[Sending Request to LLM API with {len(current_messages)} messages...]")

        content, usage = client.create_chat_completion(
            messages=current_messages,
            temperature=0.7,
            mock_response=turn["mock_reply"],
        )

        if content:
            # Task 1: Add assistant response to history for next turn
            history_mgr.add_assistant_message(content)
            print(f"ASSISTANT REPLY:\n{content}")
            print(f"Request Token Usage: {usage}")
        else:
            print("Request failed.")

    print(f"\n==================================================================")
    print(f"   END OF {strategy.upper()} DEMONSTRATION")
    print(f"   Final History Message Count: {len(history_mgr.get_history())}")
    print(f"   Final Total Tokens: {history_mgr.get_total_tokens()} tokens")
    print(f"==================================================================\n")


def main():
    log_output_path = os.path.join("outputs", "sample_output.txt")
    os.makedirs("outputs", exist_ok=True)
    if os.path.exists(log_output_path):
        os.remove(log_output_path)

    print("==================================================================")
    print("   RAG Assistant - Multi-Turn History Management & Token Budget   ")
    print("==================================================================")

    # Task 4 & Task 5: Demonstrate on overflowing conversation using Trimming strategy
    run_overflowing_conversation_demo(strategy="trim", token_budget=500, log_file=log_output_path)

    # Demonstrate on overflowing conversation using Summarising strategy
    run_overflowing_conversation_demo(strategy="summarize", token_budget=500, log_file=log_output_path)

    print(f"\n[SUCCESS] All tasks completed successfully. Sample run log saved to: '{log_output_path}'")



if __name__ == "__main__":
    main()
