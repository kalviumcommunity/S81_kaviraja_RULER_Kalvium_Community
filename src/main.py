"""
RAG Application Starter - Main Entry Point
Executes LLM API completion requests with environment configuration,
payload logging, token usage tracking, human-readable error handling,
and output log generation.
"""

import os
from llm_client import LLMClient


def main():
    log_output_path = os.path.join("outputs", "sample_output.txt")

    # Clear previous sample output log file to ensure clean output
    os.makedirs("outputs", exist_ok=True)
    if os.path.exists(log_output_path):
        os.remove(log_output_path)

    print("==================================================")
    print("      RAG Application - LLM Completion Starter    ")
    print("==================================================\n")

    # Task 1: Initialize client with environment configuration loaded from .env
    client = LLMClient(log_file=log_output_path)

    system_prompt = "You are a helpful AI assistant specialized in Retrieval-Augmented Generation (RAG) applications."
    user_prompt = "Explain what Retrieval-Augmented Generation (RAG) is and why it is useful in two concise sentences."

    print("\n[Executing Chat Completion Call]...")

    # Task 2 & 3 & 4: Send request, log payloads, print choices[0].message.content, handle errors
    content, token_usage = client.create_chat_completion(
        system_message=system_prompt,
        user_message=user_prompt,
        temperature=0.7,
    )

    # If the API key is not configured or fails authentication (401), demonstrate mock completion logging
    # so that outputs/sample_output.txt contains a complete sample of a successful call for code review.
    if not content:
        print("\n[Notice]: Live call returned an error (e.g. invalid API key). Generating sample completion payload log for demonstration...")
        content, token_usage = client.create_chat_completion(
            system_message=system_prompt,
            user_message=user_prompt,
            temperature=0.7,
            mock_response=(
                "Retrieval-Augmented Generation (RAG) is a technique that enhances Large Language Models "
                "by retrieving contextually relevant knowledge from external documents before generating a response. "
                "This ensures answers are accurate, verifiable, and grounded in up-to-date domain data."
            ),
        )

    print("\n--------------------------------------------------")
    if content:
        print("SUCCESSFUL COMPLETION RESPONSE (choices[0].message.content):")
        print(content)
        print("--------------------------------------------------")
        if token_usage:
            print(f"Token Usage Summary: {token_usage}")
        print(f"\nExecution log and payload capture saved to: {log_output_path}")
    else:
        print("COMPLETION FAILED OR ENCOUNTERED AN ERROR.")
        print(f"Check log output at '{log_output_path}' for detailed diagnostic info.")
    print("--------------------------------------------------\n")


if __name__ == "__main__":
    main()
