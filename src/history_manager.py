"""
History Manager Module for RAG Multi-Turn Conversations.

Provides multi-turn conversation tracking, accurate token measurement before requests,
and history management strategies (trimming / summarising) to keep requests within
the context token budget while preserving system messages.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Literal

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class HistoryManager:
    """
    Manages multi-turn conversation history for RAG applications.
    Tracks token counts and applies trimming or summarisation strategies
    to prevent context window overflow while ensuring system prompt persistence.
    """

    def __init__(
        self,
        system_prompt: str,
        max_token_budget: int = 800,
        strategy: Literal["trim", "summarize"] = "trim",
        model_name: str = "gpt-4o-mini",
        logger: Optional[logging.Logger] = None,
    ):
        self.system_prompt = system_prompt
        self.max_token_budget = max_token_budget
        self.strategy = strategy
        self.model_name = model_name
        self.logger = logger or logging.getLogger("HistoryManager")

        # Initialize encoder if tiktoken is available
        self.encoder = None
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoder = tiktoken.encoding_for_model(self.model_name)
            except KeyError:
                try:
                    self.encoder = tiktoken.get_encoding("cl100k_base")
                except Exception:
                    self.encoder = None

        # Task 1: Maintain multi-turn history with system message at index 0
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

    def count_tokens(self, text: str) -> int:
        """
        Task 2: Compute token count for a text string.
        Uses tiktoken when available, with accurate word/character fallback estimation.
        """
        if not text:
            return 0
        if self.encoder:
            return len(self.encoder.encode(text))
        # Fallback estimation: average 4 chars per token + word-length weighting
        return max(1, len(text) // 4 + len(text.split()) // 4)

    def compute_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Task 2: Compute exact token count for a list of conversation messages
        including OpenAI per-message formatting overhead (4 tokens per message + 3 tokens reply priming).
        """
        total_tokens = 0
        for msg in messages:
            total_tokens += 4  # Overhead per message (role header, tokens)
            total_tokens += self.count_tokens(msg.get("content", ""))
            if "name" in msg:
                total_tokens += 1
        total_tokens += 3  # Conversation response priming overhead
        return total_tokens

    def get_total_tokens(self) -> int:
        """Task 2: Get current total token count of the active conversation history."""
        return self.compute_messages_tokens(self.history)

    def add_user_message(self, user_query: str, doc_chunks: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Task 1: Add a user message with optional retrieved document chunks (RAG context).
        """
        content_parts = []
        if doc_chunks:
            content_parts.append("--- RETRIEVED DOCUMENT CONTEXT ---")
            for idx, chunk in enumerate(doc_chunks, 1):
                content_parts.append(f"[Chunk {idx}]: {chunk}")
            content_parts.append("--- END CONTEXT ---\n")
        
        content_parts.append(f"User Query: {user_query}")
        full_content = "\n".join(content_parts)

        msg = {"role": "user", "content": full_content}
        self.history.append(msg)
        return msg

    def add_assistant_message(self, assistant_reply: str) -> Dict[str, str]:
        """Task 1: Add assistant turn message to history."""
        msg = {"role": "assistant", "content": assistant_reply}
        self.history.append(msg)
        return msg

    def get_history(self) -> List[Dict[str, str]]:
        """Returns the current list of messages in history."""
        return list(self.history)

    def trim_history(self) -> Tuple[bool, int, int, int]:
        """
        Task 3: Trim strategy implementation.
        Removes oldest non-system turn messages when history exceeds token budget.
        ALWAYS preserves system message at index 0.
        Returns: (was_trimmed, original_token_count, final_token_count, turns_removed)
        """
        original_tokens = self.get_total_tokens()
        if original_tokens <= self.max_token_budget:
            return False, original_tokens, original_tokens, 0

        turns_removed = 0
        # Preserve system message at index 0 (self.history[0])
        # Trim non-system messages starting from index 1
        while len(self.history) > 2 and self.get_total_tokens() > self.max_token_budget:
            # Pop the oldest non-system message (at index 1)
            removed = self.history.pop(1)
            turns_removed += 1
            self.logger.info(
                f"[TRIM STRATEGY] Removed message role '{removed['role']}' "
                f"({self.count_tokens(removed['content'])} tokens) to stay within budget."
            )

        final_tokens = self.get_total_tokens()
        self.logger.info(
            f"[TRIMMING APPLIED]: Preserved system message. Tokens reduced from "
            f"{original_tokens} -> {final_tokens} (Budget limit: {self.max_token_budget})."
        )
        return True, original_tokens, final_tokens, turns_removed

    def summarize_history(self) -> Tuple[bool, int, int, int]:
        """
        Task 3: Summarisation strategy implementation.
        Summarises older non-system turns into a single summary message when budget is exceeded.
        ALWAYS preserves system message at index 0 and latest turn at the end.
        Returns: (was_summarised, original_token_count, final_token_count, turns_summarised)
        """
        original_tokens = self.get_total_tokens()
        if original_tokens <= self.max_token_budget:
            return False, original_tokens, original_tokens, 0

        # We need at least system message + 2 older turns + 1 latest turn to summarise
        if len(self.history) < 4:
            # If not enough turns to summarise, fall back to trimming
            return self.trim_history()

        # Preserve system prompt (index 0) and latest turn (last 2 messages: user + assistant or user)
        # Summarise messages between index 1 and len(history)-2
        system_msg = self.history[0]
        recent_turns = self.history[-2:]  # Keep latest user turn & optional reply
        older_messages = self.history[1:-2]

        turns_summarised = len(older_messages)

        # Build a concise domain summary of the older turns
        summary_lines = []
        for msg in older_messages:
            role = msg['role'].capitalize()
            # Extract main query/text without long context blocks for compact representation
            text = msg['content']
            if "User Query:" in text:
                text = text.split("User Query:")[-1].strip()
            summary_lines.append(f"{role}: {text[:120]}...")

        summary_content = (
            "[SUMMARY OF PRIOR CONVERSATION TURNS]:\n"
            + "\n".join(summary_lines)
            + "\n(System note: Older detailed document context was condensed to maintain context budget)."
        )

        summary_msg = {"role": "user", "content": summary_content}

        # Reconstruct history: System Message + Summary Message + Recent Turns
        self.history = [system_msg, summary_msg] + recent_turns
        final_tokens = self.get_total_tokens()

        self.logger.info(
            f"[SUMMARISATION APPLIED]: Preserved system message. Summarised {turns_summarised} older messages. "
            f"Tokens reduced from {original_tokens} -> {final_tokens} (Budget limit: {self.max_token_budget})."
        )

        # If summary is still over budget (e.g. recent turn was huge), trim further if needed
        if final_tokens > self.max_token_budget:
            _, _, final_tokens, extra_trimmed = self.trim_history()

        return True, original_tokens, final_tokens, turns_summarised

    def enforce_budget(self) -> Tuple[bool, int, int]:
        """
        Task 3: Enforces token budget using configured strategy ('trim' or 'summarize').
        ALWAYS preserves system prompt.
        """
        current_tokens = self.get_total_tokens()
        self.logger.info(f"[TOKEN MEASUREMENT] History contains {len(self.history)} messages | Current Tokens: {current_tokens} | Budget Limit: {self.max_token_budget}")

        if current_tokens > self.max_token_budget:
            self.logger.warning(
                f"[BUDGET EXCEEDED] Token budget exceeded ({current_tokens} > {self.max_token_budget}). "
                f"Applying strategy '{self.strategy.upper()}'..."
            )
            if self.strategy == "summarize":
                managed, orig, final, _ = self.summarize_history()
            else:
                managed, orig, final, _ = self.trim_history()
            return managed, orig, final
        else:
            self.logger.info(f"[WITHIN BUDGET] Token count ({current_tokens}) is within budget ({self.max_token_budget}). No action required.")
            return False, current_tokens, current_tokens

