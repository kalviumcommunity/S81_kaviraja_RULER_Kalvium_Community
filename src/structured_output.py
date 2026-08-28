"""
Structured Output Module for RAG Application.
Provides robust parsing of JSON responses, graceful recovery from malformed JSON strings,
and strict validation of required payload fields.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple


def count_tokens(text: str) -> int:
    """
    Estimates or calculates the token count for a text payload.
    Uses tiktoken if installed; otherwise falls back to standard LLM token estimation heuristic (~1.3 tokens per word).
    """
    if not text or not isinstance(text, str):
        return 0
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Standard tokenization heuristic: ~4 characters per token or ~1.3 tokens per word
        words = text.split()
        return max(1, int(len(words) * 1.3))



def parse_json_response(
    raw_text: str, logger: Optional[logging.Logger] = None
) -> Tuple[Optional[Dict[str, Any]], bool, Optional[str]]:
    """
    Task 2 & Task 3: Parse JSON response string into a usable Python dictionary object.
    Detects and handles invalid or malformed JSON gracefully without crashing.
    
    Returns:
        (parsed_dict, was_recovered, error_message)
    """
    if not raw_text or not isinstance(raw_text, str):
        err_msg = "Received empty or non-string response payload."
        if logger:
            logger.error(f"❌ [Malformed JSON Error]: {err_msg}")
        return None, False, err_msg

    # Task 2: Attempt standard JSON parsing
    try:
        parsed = json.loads(raw_text.strip())
        if isinstance(parsed, dict):
            if logger:
                logger.info("✅ [JSON Parse Success]: Raw response successfully parsed into Python dict.")
            return parsed, False, None
    except json.JSONDecodeError:
        pass

    # Task 3: Gracefully handle malformed JSON via recovery patterns
    if logger:
        logger.warning("⚠️ [Malformed JSON Detected]: Raw output is invalid JSON. Attempting graceful recovery...")

    cleaned = raw_text.strip()

    # Pattern A: Strip Markdown code block encodings (```json ... ``` or ``` ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # Pattern B: Isolate JSON object between outermost '{' and '}'
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    # Pattern C: Remove trailing commas before closing braces/brackets
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Attempt parsing on cleaned string
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            if logger:
                logger.info("✅ [Malformed JSON Recovered]: Successfully cleaned and parsed malformed JSON object.")
            return parsed, True, None
    except json.JSONDecodeError as err:
        err_msg = f"Failed to parse JSON after recovery attempts: {str(err)}"
        if logger:
            logger.error(f"❌ [Malformed JSON Error]: {err_msg}")
        return None, False, err_msg


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str],
    default_values: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Task 4: Validate that all required fields are present before data is used.
    Rejects or recovers missing fields using default values if provided.
    
    Returns:
        (is_valid, validated_dict, missing_fields_list)
    """
    if not isinstance(data, dict):
        if logger:
            logger.error("❌ [Validation Error]: Input data object is not a dictionary.")
        return False, {}, required_fields

    missing = []
    for field in required_fields:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)

    if not missing:
        if logger:
            logger.info(f"✅ [Validation Passed]: All required fields present: {required_fields}")
        return True, data, []

    if logger:
        logger.warning(f"⚠️ [Validation Warning]: Missing required field(s): {missing}")

    # Recover missing fields if default values are available
    if default_values:
        recovered_data = dict(data)
        for field in list(missing):
            if field in default_values:
                recovered_data[field] = default_values[field]

        still_missing = [
            f for f in missing
            if f not in recovered_data or recovered_data[f] is None or (isinstance(recovered_data[f], str) and not recovered_data[f].strip())
        ]

        if not still_missing:
            if logger:
                logger.info(f"✅ [Validation Recovered]: Successfully recovered missing field(s) with defaults: {default_values}")
            return True, recovered_data, missing
        else:
            if logger:
                logger.error(f"❌ [Validation Error]: Data rejected; unrecoverable missing field(s): {still_missing}")
            return False, recovered_data, still_missing

    if logger:
        logger.error(f"❌ [Validation Error]: Data rejected; missing required field(s): {missing}")
    return False, data, missing
