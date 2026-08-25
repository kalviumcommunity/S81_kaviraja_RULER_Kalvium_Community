import os
import json
from llm_client import LLMClient

def main():
    client = LLMClient()
    
    # Task 3: Compare two prompt variations
    user_question = "What is our policy on remote work?"
    
    print("=== Variation 1: Vague Prompt ===")
    system_prompt_v1 = "You are an assistant that helps staff."
    print("System:", system_prompt_v1)
    print("User:", user_question)
    
    content_v1, _ = client.create_chat_completion(
        system_message=system_prompt_v1,
        user_message=user_question,
        temperature=0.7,
        mock_response="Employees are allowed to work remotely. Please coordinate with your manager to figure out a suitable schedule."
    )
    print("Response V1:", content_v1)
    print("\n")
    
    print("=== Variation 2: Clear and Constrained Prompt ===")
    system_prompt_v2 = (
        "You are an internal HR assistant for our company. Your role is to answer staff questions clearly and safely.\n"
        "Scope: Only answer questions related to company policies, benefits, and HR procedures. Do not answer technical questions.\n"
        "Constraints:\n"
        "- Keep the answer under 3 sentences.\n"
        "- Maintain a professional and empathetic tone.\n"
        "- Fallback: If you don't know the answer or it is outside your scope, reply exactly with: \"I'm sorry, I don't have that information. Please contact HR directly.\""
    )
    print("System:", system_prompt_v2)
    print("User:", user_question)
    
    content_v2, _ = client.create_chat_completion(
        system_message=system_prompt_v2,
        user_message=user_question,
        temperature=0.7,
        mock_response="Our remote work policy allows up to 3 days of remote work per week with manager approval. Core hours for availability are 10 AM to 3 PM local time. Please refer to the HR handbook for more details on eligible roles."
    )
    print("Response V2:", content_v2)
    print("\n")

if __name__ == "__main__":
    main()
