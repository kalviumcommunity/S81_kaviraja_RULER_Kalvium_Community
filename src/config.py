"""
Configuration Module for RAG Service.
Loads all LLM settings, vector database configurations, and server parameters
from environment variables (or .env file) without hardcoding values.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""

    # LLM Settings
    openai_api_base_url: str
    openai_api_key: str
    chat_model: str
    embedding_model: str

    # Vector Database Settings
    chroma_db_path: str
    vector_collection_name: str

    # Server Settings
    server_host: str
    server_port: int
    debug_mode: bool

    # RAG Generation Defaults
    default_top_k: int
    default_temperature: float
    max_answer_tokens: int

    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "AppConfig":
        """Load configuration from environment variables, optionally loading a specific .env file."""
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

        return cls(
            openai_api_base_url=os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1").strip(),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            chat_model=os.getenv("CHAT_MODEL", "gpt-4o-mini").strip(),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip(),
            chroma_db_path=os.getenv("CHROMA_DB_PATH", os.getenv("VECTOR_DB_PATH", "./chroma_db")).strip(),
            vector_collection_name=os.getenv("VECTOR_COLLECTION_NAME", "document_chunks").strip(),
            server_host=os.getenv("SERVER_HOST", "0.0.0.0").strip(),
            server_port=int(os.getenv("SERVER_PORT", "8000")),
            debug_mode=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
            default_top_k=int(os.getenv("DEFAULT_TOP_K", "3")),
            default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.2")),
            max_answer_tokens=int(os.getenv("MAX_ANSWER_TOKENS", "300")),
        )

    def to_dict(self, mask_key: bool = True) -> Dict[str, Any]:
        """Return configuration as dictionary with optional API key masking."""
        api_key_repr = (
            f"{self.openai_api_key[:7]}...{self.openai_api_key[-4:]}"
            if len(self.openai_api_key) > 10
            else ("Set" if self.openai_api_key else "Not Set")
        ) if mask_key else self.openai_api_key

        return {
            "openai_api_base_url": self.openai_api_base_url,
            "openai_api_key": api_key_repr,
            "chat_model": self.chat_model,
            "embedding_model": self.embedding_model,
            "chroma_db_path": self.chroma_db_path,
            "vector_collection_name": self.vector_collection_name,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "debug_mode": self.debug_mode,
            "default_top_k": self.default_top_k,
            "default_temperature": self.default_temperature,
            "max_answer_tokens": self.max_answer_tokens,
        }


# Global default configuration instance
config = AppConfig.from_env()
