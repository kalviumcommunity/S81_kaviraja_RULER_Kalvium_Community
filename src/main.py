"""
RAG Application Starter - Main Entry Point
"""

import os
from dotenv import load_dotenv


def main():
    # Load environment variables from .env if present
    load_dotenv()

    print("RAG Application Starter Initialized Successfully.")

    base_url = os.getenv("OPENAI_API_BASE_URL", "Not configured")
    chat_model = os.getenv("CHAT_MODEL", "Not configured")
    embedding_model = os.getenv("EMBEDDING_MODEL", "Not configured")

    print("Configuration Status:")
    print(f" - Base URL: {base_url}")
    print(f" - Chat Model: {chat_model}")
    print(f" - Embedding Model: {embedding_model}")
    print("Environment setup is complete and ready for RAG development.")


if __name__ == "__main__":
    main()
