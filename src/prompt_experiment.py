import os
from llm_client import LLMClient

def run_experiment():
    """
    Task 1, 2, 3: Compare two prompt variations for a RAG assistant.
    We test a vague prompt against a highly constrained prompt.
    """
    client = LLMClient()
    
    # Task 1 & 2: A clear system message with role, scope, and constraints
    vague_system_message = "You are a helpful assistant for our company. Answer the staff's questions."
    
    constrained_system_message = (
        "You are a polite, concise internal HR assistant for Acme Corp.\n"
        "Your role is to answer staff questions based strictly on company policy.\n"
        "Scope: Only answer questions related to HR, payroll, or IT support.\n"
        "Constraints:\n"
        "1. Keep answers under 3 sentences.\n"
        "2. Maintain a professional, polite tone.\n"
        "3. If you do not know the answer or the question is out of scope, reply exactly with: "
        "'I cannot answer that based on the provided context. Please contact HR directly.'"
    )

    # The user's question with an in-scope and out-of-scope request
    user_message = "Hi! Can you tell me what the company policy is regarding carrying forward unused vacation days to the next year? And also what is the recipe for a chocolate cake?"
    
    print("=== Variation 1: Vague Prompt ===")
    print(f"System: {vague_system_message}")
    print(f"User: {user_message}\n")
    response_1, _ = client.create_chat_completion(
        system_message=vague_system_message,
        user_message=user_message,
        temperature=0.7
    )
    print(f"Response 1:\n{response_1}\n")
    
    print("=== Variation 2: Constrained Prompt ===")
    print(f"System: {constrained_system_message}")
    print(f"User: {user_message}\n")
    response_2, _ = client.create_chat_completion(
        system_message=constrained_system_message,
        user_message=user_message,
        temperature=0.7
    )
    print(f"Response 2:\n{response_2}\n")

    print("=== Task 4: Chosen Prompt Documentation ===")
    documentation = (
        "Chosen Prompt: The constrained system message (Variation 2).\n"
        "Why it works:\n"
        "1. Role: Clearly defines the persona (polite, concise HR assistant).\n"
        "2. Scope: Prevents the model from answering out-of-bounds questions (like the chocolate cake recipe) by restricting to HR/IT.\n"
        "3. Constraints: Enforces length (under 3 sentences) and provides a predictable, exact fallback phrase for unanswerable questions.\n"
        "This makes the output much more reliable and professional compared to the vague prompt."
    )
    print(documentation)

if __name__ == "__main__":
    run_experiment()
