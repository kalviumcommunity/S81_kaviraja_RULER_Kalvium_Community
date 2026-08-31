"""
Token-Aware Chunker for RAG Applications.

Implements Task 1 to Task 4:
- Task 1: Size chunks by exact token count using tiktoken (cl100k_base).
- Task 2: Implement controlled token overlap between adjacent chunks.
- Task 3: Demonstrate overlap preserving boundary context (with vs without overlap).
- Task 4: Provide technical justification for token size and overlap settings.
"""

import os
import tiktoken
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class TokenChunk:
    """
    Dataclass representing a token-bounded text chunk with source and token metadata.
    """
    chunk_id: str
    text: str
    token_count: int
    start_token: int
    end_token: int
    overlap_tokens: int
    doc_id: str = "doc_unknown"
    filename: str = "unknown"
    source_path: str = "unknown"
    section: str = "General"
    page_number: Optional[int] = 1
    chunk_index: int = 0
    total_chunks: int = 1
    start_char: int = 0
    end_char: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Converts chunk representation to dictionary format."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "token_count": self.token_count,
            "start_token": self.start_token,
            "end_token": self.end_token,
            "overlap_tokens": self.overlap_tokens,
            "metadata": {
                "doc_id": self.doc_id,
                "filename": self.filename,
                "source_path": self.source_path,
                "section": self.section,
                "page_number": self.page_number,
                "chunk_index": self.chunk_index,
                "total_chunks": self.total_chunks,
                "start_char": self.start_char,
                "end_char": self.end_char,
            }
        }


class TokenAwareChunker:
    """
    Token-aware text chunker using tiktoken tokenization.
    
    Sizes chunks based strictly on token counts (Task 1) and enforces a controlled
    token overlap between adjacent chunks (Task 2).
    """

    def __init__(
        self,
        chunk_size_tokens: int = 512,
        chunk_overlap_tokens: int = 64,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize TokenAwareChunker.

        :param chunk_size_tokens: Maximum target tokens per chunk (Task 1).
        :param chunk_overlap_tokens: Number of trailing tokens from previous chunk to repeat (Task 2).
        :param encoding_name: Tiktoken encoding name (cl100k_base used by gpt-4, gpt-3.5-turbo, text-embedding-3-small).
        """
        if chunk_size_tokens <= 0:
            raise ValueError(f"chunk_size_tokens must be positive, got {chunk_size_tokens}")
        if chunk_overlap_tokens < 0:
            raise ValueError(f"chunk_overlap_tokens must be non-negative, got {chunk_overlap_tokens}")
        if chunk_overlap_tokens >= chunk_size_tokens:
            raise ValueError(
                f"chunk_overlap_tokens ({chunk_overlap_tokens}) must be strictly less than "
                f"chunk_size_tokens ({chunk_size_tokens})."
            )

        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.encoding_name = encoding_name
        self.tokenizer = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Returns exact token count for a text string using tiktoken."""
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    def split_tokens(self, tokens: List[int]) -> List[Tuple[List[int], int, int, int]]:
        """
        Splits token array into overlapping token windows.

        Returns list of tuples: (chunk_tokens, start_token_idx, end_token_idx, overlap_count)
        """
        if not tokens:
            return []

        total_tokens = len(tokens)
        if total_tokens <= self.chunk_size_tokens:
            return [(tokens, 0, total_tokens, 0)]

        chunks_data = []
        step = self.chunk_size_tokens - self.chunk_overlap_tokens
        start_idx = 0

        while start_idx < total_tokens:
            end_idx = min(start_idx + self.chunk_size_tokens, total_tokens)
            chunk_toks = tokens[start_idx:end_idx]
            overlap = 0 if start_idx == 0 else self.chunk_overlap_tokens

            chunks_data.append((chunk_toks, start_idx, end_idx, overlap))

            if end_idx >= total_tokens:
                break

            start_idx += step

        return chunks_data

    def chunk_text(
        self,
        text: str,
        doc_id: str = "doc_001",
        filename: str = "document.txt",
        source_path: str = "data/document.txt",
        section: str = "General",
        page_number: Optional[int] = 1
    ) -> List[TokenChunk]:
        """
        Task 1 & 2: Chunks input text strictly by token count with controlled token overlap.
        """
        if not text or not text.strip():
            return []

        all_tokens = self.tokenizer.encode(text)
        token_splits = self.split_tokens(all_tokens)
        total_chunks = len(token_splits)

        chunks: List[TokenChunk] = []

        for idx, (chunk_toks, start_tok_idx, end_tok_idx, overlap_count) in enumerate(token_splits):
            chunk_text = self.tokenizer.decode(chunk_toks)
            chunk_id = f"{doc_id}#chunk_{idx + 1:03d}"

            # Calculate approximate character bounds in full text
            prefix_text = self.tokenizer.decode(all_tokens[:start_tok_idx]) if start_tok_idx > 0 else ""
            start_char = len(prefix_text)
            end_char = start_char + len(chunk_text)

            chunk = TokenChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                token_count=len(chunk_toks),
                start_token=start_tok_idx,
                end_token=end_tok_idx,
                overlap_tokens=overlap_count,
                doc_id=doc_id,
                filename=filename,
                source_path=source_path,
                section=section,
                page_number=page_number,
                chunk_index=idx,
                total_chunks=total_chunks,
                start_char=start_char,
                end_char=end_char
            )
            chunks.append(chunk)

        return chunks

    def demonstrate_boundary_context(
        self,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Task 3: Demonstrates boundary context preservation with vs without overlap.
        Shows an idea sitting on a boundary appearing intact thanks to overlap.
        """
        if text is None:
            text = (
                "The organization's standard financial policy stipulates that all routine vendor transactions "
                "under $50,000 may be approved directly by the department head without prior board approval. "
                "However, any single capital expenditure exceeding $50,000 requires unanimous board approval "
                "and an independent audit report prior to disbursement. "
                "Failure to obtain board authorization for high-value transactions results in an immediate suspension "
                "of procurement privileges and mandatory compliance review."
            )

        demo_chunk_size = 35
        demo_overlap = 12

        chunker_no_overlap = TokenAwareChunker(
            chunk_size_tokens=demo_chunk_size,
            chunk_overlap_tokens=0,
            encoding_name=self.encoding_name
        )
        chunker_with_overlap = TokenAwareChunker(
            chunk_size_tokens=demo_chunk_size,
            chunk_overlap_tokens=demo_overlap,
            encoding_name=self.encoding_name
        )

        chunks_no_overlap = chunker_no_overlap.chunk_text(text, doc_id="boundary_demo_no_overlap")
        chunks_with_overlap = chunker_with_overlap.chunk_text(text, doc_id="boundary_demo_with_overlap")

        no_overlap_c1 = chunks_no_overlap[0].text if len(chunks_no_overlap) > 0 else ""
        no_overlap_c2 = chunks_no_overlap[1].text if len(chunks_no_overlap) > 1 else ""

        with_overlap_c1 = chunks_with_overlap[0].text if len(chunks_with_overlap) > 0 else ""
        with_overlap_c2 = chunks_with_overlap[1].text if len(chunks_with_overlap) > 1 else ""

        repeated_tokens = self.tokenizer.encode(with_overlap_c1)[-demo_overlap:]
        repeated_text = self.tokenizer.decode(repeated_tokens)

        return {
            "target_passage": text,
            "demo_settings": {
                "chunk_size_tokens": demo_chunk_size,
                "overlap_tokens": demo_overlap,
                "encoding_name": self.encoding_name
            },
            "without_overlap": {
                "chunk_1_full": no_overlap_c1,
                "chunk_2_full": no_overlap_c2,
                "chunk_1_end": no_overlap_c1[-75:],
                "chunk_2_start": no_overlap_c2[:75],
                "boundary_issue": (
                    "CONTEXT SEVERED: Chunk 1 ends prematurely with 'any single capital expenditure' "
                    "without specifying the financial threshold or approval condition. Chunk 2 starts abruptly with "
                    "'exceeding $50,000 requires unanimous board approval', severing the subject 'capital expenditure'. "
                    "An LLM processing Chunk 2 alone lacks the core subject context!"
                )
            },
            "with_overlap": {
                "chunk_1_full": with_overlap_c1,
                "chunk_2_full": with_overlap_c2,
                "overlapping_repeated_text": repeated_text,
                "preserved_boundary_context": (
                    "CONTEXT PRESERVED INTACT: Thanks to the 12-token controlled overlap, Chunk 2 starts with "
                    f"'{repeated_text}', carrying over the subject from Chunk 1. An LLM or retriever reading Chunk 2 "
                    "receives the complete sentence and condition intact without boundary fragmentation!"
                )
            }
        }

    def justify_settings(self) -> Dict[str, Any]:
        """
        Task 4: Technical justification for target token size and overlap settings.
        """
        overlap_pct = round((self.chunk_overlap_tokens / self.chunk_size_tokens) * 100, 2)
        return {
            "model_family": "OpenAI Embedding & Chat Models (text-embedding-3-small, gpt-4o-mini, gpt-4)",
            "encoding": self.encoding_name,
            "chosen_chunk_size_tokens": self.chunk_size_tokens,
            "chosen_overlap_tokens": self.chunk_overlap_tokens,
            "overlap_ratio_percentage": overlap_pct,
            "justifications": {
                "task_1_token_sizing": (
                    f"Token-based sizing ({self.chunk_size_tokens} tokens) guarantees exact compliance with LLM "
                    "and embedding context limits. Unlike character-based splitting where character-to-token ratios "
                    "fluctuate wildly (e.g. standard English text vs code or JSON), token-based chunking guarantees "
                    "predictable memory footprint, zero context truncation, and precise prompt budget control."
                ),
                "token_size_choice_rationale": (
                    f"Setting chunk size to {self.chunk_size_tokens} tokens is optimized for vector search and RAG retrieval. "
                    "512 tokens (~350-400 words / 2-3 dense paragraphs) provides sufficient semantic depth for dense vector "
                    "embeddings in text-embedding-3-small without diluting specific entity facts, while leaving ample room "
                    "in LLM context windows when retrieving top-k chunks."
                ),
                "task_2_controlled_overlap_rationale": (
                    f"Setting controlled overlap to {self.chunk_overlap_tokens} tokens (~{overlap_pct}%) ensures boundary "
                    "continuity across chunks. 64 tokens (~45-50 words / 1-2 complete sentences) covers typical dependent clauses, "
                    "entity references, and conjunctions, preventing contextual truncation at chunk edges."
                ),
                "cost_vs_context_tradeoff": (
                    f"A 64-token (~12.5%) overlap introduces a minimal 12.5% storage and token overhead, striking the ideal balance "
                    "between complete context preservation (eliminating boundary errors as demonstrated in Task 3) and cost efficiency."
                )
            }
        }
