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
from structured_output import parse_json_response, validate_required_fields


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
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        mock_response: Optional[str] = None,
        simulate_error: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Send chat completion request, log request/response payloads,
        track token usage, return choices[0].message.content, and handle errors clearly.
        Supports response_format={"type": "json_object"}.
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

        # Task 3: Log outgoing request payload
        self.logger.info("--- OUTGOING REQUEST PAYLOAD ---")
        self.logger.info(f"Target Model: {self.model_name}")
        self.logger.info(f"Response Format Mode: {response_format or 'default'}")
        self.logger.info(f"Outgoing Messages:\n{json.dumps(messages, indent=2)}")

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
                if mock_response:
                    mock_text = mock_response
                elif response_format and response_format.get("type") == "json_object":
                    mock_text = json.dumps({
                        "answer": "Retrieval-Augmented Generation (RAG) enhances LLMs by retrieving contextually relevant knowledge from external documents before generating a response.",
                        "source": "RAG Architecture Specification v1.0",
                        "confidence": 0.98
                    }, indent=2)
                else:
                    mock_text = (
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
                if response_format:
                    kwargs["response_format"] = response_format

                # Send completion request to live API
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

    def create_structured_completion(
        self,
        system_message: str,
        user_message: str,
        required_fields: List[str],
        default_values: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
        mock_response: Optional[str] = None,
        simulate_error: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Tasks 1-4: Pipeline method for structured JSON completions.
        - Task 1: Prompt for defined JSON structure with response_format mode
        - Task 2: Parse raw JSON into Python dict object
        - Task 3: Detect & handle malformed JSON gracefully (recover or report clearly)
        - Task 4: Validate required fields (reject or recover if missing)
        """
        self.logger.info("==================================================")
        self.logger.info("     EXECUTING STRUCTURED JSON COMPLETION CALL    ")
        self.logger.info("==================================================")

        # Task 1: Instruct model to return defined JSON structure
        json_instruction = (
            f"\n\nCRITICAL OUTPUT REQUIREMENT: You MUST return a JSON object matching this structure: "
            f"{json.dumps({field: f'<{field}_value>' for field in required_fields})}. "
            f"Required keys: {json.dumps(required_fields)}."
        )
        full_system_message = system_message + json_instruction

        # Task 1: Execute call with response_format={"type": "json_object"}
        raw_content, token_usage = self.create_chat_completion(
            system_message=full_system_message,
            user_message=user_message,
            temperature=temperature,
            response_format={"type": "json_object"},
            mock_response=mock_response,
            simulate_error=simulate_error,
        )

        if not raw_content:
            return None, token_usage

        # Task 2 & 3: Parse JSON response & handle malformed JSON gracefully
        parsed_dict, was_recovered, parse_err = parse_json_response(raw_content, logger=self.logger)
        if not parsed_dict:
            self.logger.error("❌ [Structured Output Failed]: Could not obtain valid JSON object from response.")
            return None, token_usage

        # Task 4: Validate required fields (recover with defaults or reject)
        is_valid, final_dict, missing_fields = validate_required_fields(
            parsed_dict, required_fields, default_values=default_values, logger=self.logger
        )

        if is_valid:
            self.logger.info("🎉 [Structured Output Success]: JSON parsed, recovered, and validated successfully.")
            return final_dict, token_usage
        else:
            self.logger.error("❌ [Structured Output Failed]: Payload rejected due to unrecoverable missing required fields.")
            return None, token_usage

