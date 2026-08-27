"""
LLM Client Module for RAG Application starter.
Handles environment configuration, chat completion calls, payload logging,
token usage tracking, and human-readable error handling.
"""

import os
import json
import logging
from types import SimpleNamespace
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI, APIError, AuthenticationError, RateLimitError, APIConnectionError


def setup_logger(log_file_path: Optional[str] = None) -> logging.Logger:
    """Configures structured logging to stdout and optionally to an output log file."""
    logger = logging.getLogger("LLMClient")
    logger.setLevel(logging.INFO)
    logger.handlers = []  # Reset existing handlers to prevent duplicates

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Stream / Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    if log_file_path:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        fh = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


class LLMClient:
    """OpenAI-compatible LLM client configured via environment variables."""

    def __init__(self, env_path: Optional[str] = None, log_file: Optional[str] = None):
        # Task 1: Load environment variables from .env file — never hard-coded
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

        self.logger = setup_logger(log_file)

        # Read base URL, API key, and model name from environment config
        self.base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1").strip()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model_name = os.getenv("CHAT_MODEL", "gpt-4o-mini").strip()

        self.logger.info("Initializing LLM Client with environment configuration:")
        self.logger.info(f" - Base URL: {self.base_url}")
        self.logger.info(f" - Model Name: {self.model_name}")
        masked_key = f"{self.api_key[:7]}...{self.api_key[-4:]}" if len(self.api_key) > 10 else ("Set" if self.api_key else "NOT SET")
        self.logger.info(f" - API Key: {masked_key}")

        client_kwargs: Dict[str, Any] = {}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
        else:
            client_kwargs["api_key"] = "missing_api_key_placeholder"

        self.client = OpenAI(**client_kwargs)

    def create_chat_completion(
        self,
        system_message: Optional[str] = None,
        user_message: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        mock_response: Optional[str] = None,
        simulate_error: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Task 2, 3, & 4: Send chat completion request, log request/response payloads,
        track token usage, return choices[0].message.content, and handle errors clearly.
        Supports both single-turn (system_message + user_message) and multi-turn (messages list).
        """
        if messages is None:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            if user_message:
                messages.append({"role": "user", "content": user_message})

        # Task 3: Log outgoing request payload
        self.logger.info("--- OUTGOING REQUEST PAYLOAD ---")
        self.logger.info(f"Target Model: {self.model_name}")
        self.logger.info(f"Outgoing Messages ({len(messages)} items):\n{json.dumps(messages, indent=2)}")

        try:
            # Handle simulated errors for testing error handlers cleanly
            if simulate_error == "401":
                raise AuthenticationError(
                    message="Incorrect API key provided.",
                    response=SimpleNamespace(status_code=401, headers={}),
                    body=None,
                )
            elif simulate_error == "429":
                raise RateLimitError(
                    message="You exceeded your current quota.",
                    response=SimpleNamespace(status_code=429, headers={}),
                    body=None,
                )

            # Handle mock response mode if specified or if API key is set to "mock"
            if mock_response or self.api_key == "mock":
                mock_text = mock_response or (
                    "Retrieval-Augmented Generation (RAG) combines document retrieval with text generation "
                    "to provide precise, up-to-date answers. It grounds LLM responses in trusted source data, "
                    "significantly reducing hallucinations."
                )
                response = SimpleNamespace(
                    id="chatcmpl-mock-987654321",
                    model=self.model_name,
                    choices=[
                        SimpleNamespace(
                            index=0,
                            finish_reason="stop",
                            message=SimpleNamespace(role="assistant", content=mock_text),
                        )
                    ],
                    usage=SimpleNamespace(
                        prompt_tokens=42,
                        completion_tokens=36,
                        total_tokens=78,
                    ),
                )
            else:
                kwargs: Dict[str, Any] = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                }
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens

                # Task 2: Send completion request to live API
                response = self.client.chat.completions.create(**kwargs)

            # Task 2: Extract choices[0].message.content
            content = response.choices[0].message.content if response.choices else None
            finish_reason = response.choices[0].finish_reason if response.choices else "unknown"

            # Task 3: Extract token usage metadata if available
            token_usage = {}
            if hasattr(response, "usage") and response.usage:
                token_usage = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }

            # Task 3: Log response payload & usage
            self.logger.info("--- INCOMING RESPONSE PAYLOAD ---")
            self.logger.info(f"Response ID: {getattr(response, 'id', 'N/A')}")
            self.logger.info(f"Response Model: {getattr(response, 'model', self.model_name)}")
            self.logger.info(f"Finish Reason: {finish_reason}")
            self.logger.info(f"Token Usage: {json.dumps(token_usage, indent=2) if token_usage else 'N/A'}")
            self.logger.info("--- MODEL REPLY (choices[0].message.content) ---")
            self.logger.info(f"{content}\n")

            return content, token_usage

        # Task 4: Catch and report common failures with human-readable error messages
        except AuthenticationError:
            self.logger.error("❌ [401 Authentication Error]: Invalid or missing API key.")
            self.logger.error("   Action Required: Please set a valid OPENAI_API_KEY in your .env configuration file.\n")
            return None, None

        except RateLimitError:
            self.logger.error("❌ [429 Rate Limit Error]: Rate limit or usage quota exceeded.")
            self.logger.error("   Action Required: Check your API plan, billing details, or retry after a cooldown period.\n")
            return None, None

        except APIConnectionError as e:
            self.logger.error(f"❌ [Connection Error]: Failed to reach the LLM endpoint at '{self.base_url}'.")
            self.logger.error(f"   Details: {getattr(e, 'message', str(e))}\n")
            return None, None

        except APIError as e:
            status = getattr(e, "status_code", "N/A")
            self.logger.error(f"❌ [API Error {status}]: {getattr(e, 'message', str(e))}\n")
            return None, None

        except Exception as e:
            self.logger.error(f"❌ [Unexpected Error]: {type(e).__name__} - {str(e)}\n")
            return None, None
