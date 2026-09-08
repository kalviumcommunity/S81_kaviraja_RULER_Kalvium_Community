"""
Context Injection & Prompt Augmentation Module (Tasks 1 to 5).

Implements:
- Task 1: Format and inject retrieved chunks into prompt context.
- Task 2: Dynamically calculate and enforce token budgets (leaving room for system prompt, user question, and answer generation).
- Task 3: Include configurable source markers ([1], [2], [Source X: doc.txt], etc.) for accurate answer citations.
- Task 4: Inject grounding instructions requiring models to answer strictly from context and state when context is insufficient.
- Task 5: Export structured JSON and human-readable augmented prompt artifacts with detailed token accounting.
"""

import os
import sys
import json
import logging
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union, Tuple
import tiktoken

try:
    from citation_attribution import attribute_answer
except ImportError:
    from src.citation_attribution import attribute_answer

try:
    from prompts.templates import (
        PromptTemplate,
        RAG_GROUNDED_SYSTEM_PROMPT,
        RAG_CONTEXT_INJECTION_USER_PROMPT,
        GROUNDING_INSTRUCTIONS,
    )
except ImportError:
    from src.prompts.templates import (
        PromptTemplate,
        RAG_GROUNDED_SYSTEM_PROMPT,
        RAG_CONTEXT_INJECTION_USER_PROMPT,
        GROUNDING_INSTRUCTIONS,
    )


class SourceMarkerStyle(str, Enum):
    """Supported source marker formats for chunk citation."""
    NUMBERED = "numbered"              # [1], [2], [3]
    VERBOSE = "verbose"                # [Source 1: filename.txt | Section: Section 3]
    INLINE_TAG = "inline_tag"          # [DOC_001#chunk_001]
    CITATION_KEY = "citation_key"      # [Source: filename.txt, Page 1]


@dataclass
class TokenBudgetConfig:
    """
    Configuration for model token limits and budget allocation (Task 2).
    """
    total_model_limit: int = 4096       # Maximum context window of target model (e.g., 4096, 8192, 128000)
    max_answer_tokens: int = 600        # Reserved completion tokens for model response
    safety_margin_tokens: int = 50      # Safety headroom for special tokens / formatting overhead
    encoding_name: str = "cl100k_base"  # Tiktoken encoding (cl100k_base for gpt-4, gpt-4o-mini, embeddings)


@dataclass
class InjectedChunkInfo:
    """Detailed record of a chunk injected into the prompt context."""
    chunk_index: int
    source_marker: str
    chunk_id: str
    doc_id: str
    filename: str
    source_path: str
    section: str
    page_number: Optional[int]
    source_chunk_index: Optional[int]
    start_char: Optional[int]
    end_char: Optional[int]
    raw_text: str
    formatted_text: str
    token_count: int
    cumulative_context_tokens: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkippedChunkInfo:
    """Record of a candidate chunk excluded from context due to token budget limits."""
    chunk_index: int
    chunk_id: str
    reason: str
    token_count: int
    required_budget: int
    remaining_budget: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AssembledContext:
    """Result of context assembly and token budget enforcement."""
    formatted_context: str
    injected_chunks: List[InjectedChunkInfo]
    skipped_chunks: List[SkippedChunkInfo]
    total_candidate_chunks: int
    total_injected_chunks: int
    total_skipped_chunks: int
    context_tokens: int
    available_context_budget: int
    remaining_context_budget: int
    budget_breakdown: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "formatted_context": self.formatted_context,
            "injected_chunks": [c.to_dict() for c in self.injected_chunks],
            "skipped_chunks": [c.to_dict() for c in self.skipped_chunks],
            "total_candidate_chunks": self.total_candidate_chunks,
            "total_injected_chunks": self.total_injected_chunks,
            "total_skipped_chunks": self.total_skipped_chunks,
            "context_tokens": self.context_tokens,
            "available_context_budget": self.available_context_budget,
            "remaining_context_budget": self.remaining_context_budget,
            "budget_breakdown": self.budget_breakdown,
        }


@dataclass
class AugmentedPrompt:
    """Complete augmented prompt package ready for LLM generation."""
    system_prompt: str
    user_prompt: str
    question: str
    assembled_context: AssembledContext
    source_marker_style: str
    token_accounting: Dict[str, int]
    grounding_enforced: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "question": self.question,
            "source_marker_style": self.source_marker_style,
            "grounding_enforced": self.grounding_enforced,
            "token_accounting": self.token_accounting,
            "assembled_context": self.assembled_context.to_dict(),
        }


class ContextInjector:
    """
    Context Injection & Prompt Augmentation Engine.
    
    Handles:
    1. Chunk formatting with standardized source markers ([1], [2], etc.)
    2. Dynamic token budget calculation & strict limit enforcement
    3. Grounding instruction integration for hallucination prevention
    4. Generation of ready-to-use augmented prompt payloads
    """

    def __init__(
        self,
        budget_config: Optional[TokenBudgetConfig] = None,
        default_marker_style: SourceMarkerStyle = SourceMarkerStyle.NUMBERED,
        logger: Optional[logging.Logger] = None,
    ):
        self.budget_config = budget_config or TokenBudgetConfig()
        self.default_marker_style = default_marker_style
        self.tokenizer = tiktoken.get_encoding(self.budget_config.encoding_name)
        self.logger = logger or logging.getLogger("ContextInjector")

    def count_tokens(self, text: str) -> int:
        """Returns exact token count of text using configured tokenizer."""
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    def format_source_marker(
        self,
        index: int,
        chunk_metadata: Dict[str, Any],
        style: SourceMarkerStyle = SourceMarkerStyle.NUMBERED,
    ) -> str:
        """
        Task 3: Generates citation source marker according to requested style.
        """
        doc_id = chunk_metadata.get("doc_id", "DOC_UNKNOWN")
        chunk_id = chunk_metadata.get("chunk_id", f"chunk_{index:03d}")
        filename = chunk_metadata.get("filename", "unknown.txt")
        section = chunk_metadata.get("section", "General")
        page = chunk_metadata.get("page_number", 1)

        if style == SourceMarkerStyle.NUMBERED:
            return f"[{index}]"
        elif style == SourceMarkerStyle.VERBOSE:
            page_info = f", Page {page}" if page else ""
            return f"[Source {index}: {filename} | Section: {section}{page_info}]"
        elif style == SourceMarkerStyle.INLINE_TAG:
            return f"[{chunk_id}]"
        elif style == SourceMarkerStyle.CITATION_KEY:
            page_info = f", Page {page}" if page else ""
            return f"[Source: {filename}{page_info}]"
        else:
            return f"[{index}]"

    def format_chunk(
        self,
        chunk: Any,
        index: int,
        style: SourceMarkerStyle = SourceMarkerStyle.NUMBERED,
    ) -> Tuple[str, Dict[str, Any], str]:
        """
        Task 1 & Task 3: Formats a single retrieved chunk with source markers and metadata header.
        
        Returns: (formatted_chunk_str, chunk_meta_dict, source_marker)
        """
        # Extract text and metadata from various chunk object formats
        if hasattr(chunk, "chunk_id") and (hasattr(chunk, "text") or hasattr(chunk, "source_text")):
            text = getattr(chunk, "text", getattr(chunk, "source_text", ""))
            meta = getattr(chunk, "metadata", {})
            if meta and not isinstance(meta, dict):
                meta = meta.to_dict() if hasattr(meta, "to_dict") else vars(meta)
            chunk_id = getattr(chunk, "chunk_id", meta.get("chunk_id", f"chunk_{index:03d}"))
            doc_id = getattr(chunk, "doc_id", meta.get("doc_id", "DOC_UNKNOWN"))
            filename = getattr(chunk, "filename", meta.get("filename", "unknown.txt"))
            section = getattr(chunk, "section", meta.get("section", "General"))
            page_number = getattr(chunk, "page_number", meta.get("page_number", 1))
        elif hasattr(chunk, "text") and hasattr(chunk, "metadata"):
            text = chunk.text
            meta = chunk.metadata if isinstance(chunk.metadata, dict) else (
                chunk.metadata.to_dict() if hasattr(chunk.metadata, "to_dict") else vars(chunk.metadata)
            )
            chunk_id = getattr(chunk, "chunk_id", meta.get("chunk_id", f"chunk_{index:03d}"))
            doc_id = getattr(chunk, "doc_id", meta.get("doc_id", "DOC_UNKNOWN"))
            filename = getattr(chunk, "filename", meta.get("filename", "unknown.txt"))
            section = getattr(chunk, "section", meta.get("section", "General"))
            page_number = getattr(chunk, "page_number", meta.get("page_number", 1))
        elif hasattr(chunk, "source_text") and hasattr(chunk, "metadata"):
            text = chunk.source_text
            meta = chunk.metadata if isinstance(chunk.metadata, dict) else vars(chunk.metadata)
            chunk_id = getattr(chunk, "chunk_id", meta.get("chunk_id", f"chunk_{index:03d}"))
            doc_id = meta.get("doc_id", getattr(chunk, "doc_id", "DOC_UNKNOWN"))
            filename = meta.get("filename", getattr(chunk, "filename", "unknown.txt"))
            section = meta.get("section", getattr(chunk, "section", "General"))
            page_number = meta.get("page_number", getattr(chunk, "page_number", 1))
        elif isinstance(chunk, dict):
            text = chunk.get("text", chunk.get("source_text", chunk.get("content", "")))
            meta = chunk.get("metadata", chunk)
            chunk_id = chunk.get("chunk_id", meta.get("chunk_id", f"chunk_{index:03d}"))
            doc_id = meta.get("doc_id", chunk.get("doc_id", "DOC_UNKNOWN"))
            filename = meta.get("filename", chunk.get("filename", "unknown.txt"))
            section = meta.get("section", chunk.get("section", "General"))
            page_number = meta.get("page_number", chunk.get("page_number", 1))
        else:
            text = str(chunk)
            chunk_id = f"chunk_{index:03d}"
            doc_id = "DOC_UNKNOWN"
            filename = "unknown.txt"
            section = "General"
            page_number = 1
            meta = {}

        chunk_meta = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "filename": filename,
            "source_path": meta.get("source_path", ""),
            "section": section,
            "page_number": page_number,
            "chunk_index": meta.get("chunk_index"),
            "start_char": meta.get("start_char"),
            "end_char": meta.get("end_char"),
        }

        marker = self.format_source_marker(index=index, chunk_metadata=chunk_meta, style=style)
        
        # Assemble formatted chunk block
        page_str = f" | Page: {page_number}" if page_number else ""
        header = f"--- {marker} [Doc: {filename} | Section: {section}{page_str} | ID: {chunk_id}] ---"
        formatted_chunk = f"{header}\n{text.strip()}\n"

        return formatted_chunk, chunk_meta, marker

    def calculate_token_budget(
        self,
        system_prompt: str,
        question: str,
        budget_config: Optional[TokenBudgetConfig] = None,
    ) -> Dict[str, Any]:
        """
        Task 2: Calculates available token headroom for context injection.
        
        Formula:
        available_context_budget = total_model_limit - (system_tokens + question_tokens + max_answer_tokens + safety_margin)
        """
        cfg = budget_config or self.budget_config
        system_tokens = self.count_tokens(system_prompt)
        question_tokens = self.count_tokens(question)
        
        # Base template overhead for [CONTEXT], [QUESTION], [ANSWER] markers
        template_overhead = self.count_tokens(
            RAG_CONTEXT_INJECTION_USER_PROMPT.render(context="", question="")
        )

        fixed_prompt_tokens = system_tokens + question_tokens + template_overhead
        reserved_completion_tokens = cfg.max_answer_tokens
        safety_tokens = cfg.safety_margin_tokens

        non_context_allocation = fixed_prompt_tokens + reserved_completion_tokens + safety_tokens
        available_context_budget = max(0, cfg.total_model_limit - non_context_allocation)

        return {
            "total_model_limit": cfg.total_model_limit,
            "system_prompt_tokens": system_tokens,
            "user_question_tokens": question_tokens,
            "template_overhead_tokens": template_overhead,
            "fixed_prompt_tokens": fixed_prompt_tokens,
            "reserved_answer_tokens": reserved_completion_tokens,
            "safety_margin_tokens": safety_tokens,
            "non_context_allocation_total": non_context_allocation,
            "available_context_budget": available_context_budget,
            "has_sufficient_budget": available_context_budget > 0,
        }

    def assemble_context(
        self,
        chunks: List[Any],
        available_budget: int,
        style: SourceMarkerStyle = SourceMarkerStyle.NUMBERED,
        allow_partial_chunk_truncation: bool = False,
    ) -> AssembledContext:
        """
        Task 1 & Task 2: Assembles retrieved chunks sequentially up to available token budget.
        Rejects/skips chunks that would exceed the token budget.
        """
        injected: List[InjectedChunkInfo] = []
        skipped: List[SkippedChunkInfo] = []
        formatted_blocks: List[str] = []
        current_context_tokens = 0

        for idx, chunk in enumerate(chunks, start=1):
            formatted_text, meta, marker = self.format_chunk(chunk, index=idx, style=style)
            raw_text = (
                chunk.text if hasattr(chunk, "text")
                else (chunk.source_text if hasattr(chunk, "source_text")
                else (chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)))
            )
            
            chunk_token_count = self.count_tokens(formatted_text)
            potential_total = current_context_tokens + chunk_token_count

            if potential_total <= available_budget:
                # Fits completely in budget
                current_context_tokens = potential_total
                formatted_blocks.append(formatted_text)
                injected.append(
                    InjectedChunkInfo(
                        chunk_index=idx,
                        source_marker=marker,
                        chunk_id=meta["chunk_id"],
                        doc_id=meta["doc_id"],
                        filename=meta["filename"],
                        source_path=meta.get("source_path", ""),
                        section=meta["section"],
                        page_number=meta.get("page_number"),
                        source_chunk_index=meta.get("chunk_index"),
                        start_char=meta.get("start_char"),
                        end_char=meta.get("end_char"),
                        raw_text=raw_text,
                        formatted_text=formatted_text,
                        token_count=chunk_token_count,
                        cumulative_context_tokens=current_context_tokens,
                    )
                )
            else:
                # Exceeds token budget
                remaining = max(0, available_budget - current_context_tokens)
                if allow_partial_chunk_truncation and remaining > 50:
                    # Optional truncation if requested and sufficient room remains
                    truncated_tokens = self.tokenizer.encode(formatted_text)[:remaining]
                    truncated_text = self.tokenizer.decode(truncated_tokens) + "\n[... truncated due to token budget ...]\n"
                    actual_tokens = self.count_tokens(truncated_text)
                    current_context_tokens += actual_tokens
                    formatted_blocks.append(truncated_text)
                    injected.append(
                        InjectedChunkInfo(
                            chunk_index=idx,
                            source_marker=marker,
                            chunk_id=meta["chunk_id"],
                            doc_id=meta["doc_id"],
                            filename=meta["filename"],
                            source_path=meta.get("source_path", ""),
                            section=meta["section"],
                            page_number=meta.get("page_number"),
                            source_chunk_index=meta.get("chunk_index"),
                            start_char=meta.get("start_char"),
                            end_char=meta.get("end_char"),
                            raw_text=raw_text,
                            formatted_text=truncated_text,
                            token_count=actual_tokens,
                            cumulative_context_tokens=current_context_tokens,
                        )
                    )
                else:
                    skipped.append(
                        SkippedChunkInfo(
                            chunk_index=idx,
                            chunk_id=meta["chunk_id"],
                            reason="EXCEEDED_TOKEN_BUDGET",
                            token_count=chunk_token_count,
                            required_budget=potential_total,
                            remaining_budget=remaining,
                        )
                    )

        full_context_str = "\n".join(formatted_blocks) if formatted_blocks else "No relevant context found."
        actual_context_tokens = self.count_tokens(full_context_str)

        budget_summary = {
            "initial_budget": available_budget,
            "used_tokens": actual_context_tokens,
            "remaining_tokens": max(0, available_budget - actual_context_tokens),
            "utilization_rate_pct": round((actual_context_tokens / available_budget * 100), 2) if available_budget > 0 else 0.0,
        }

        return AssembledContext(
            formatted_context=full_context_str,
            injected_chunks=injected,
            skipped_chunks=skipped,
            total_candidate_chunks=len(chunks),
            total_injected_chunks=len(injected),
            total_skipped_chunks=len(skipped),
            context_tokens=actual_context_tokens,
            available_context_budget=available_budget,
            remaining_context_budget=max(0, available_budget - actual_context_tokens),
            budget_breakdown=budget_summary,
        )

    def build_augmented_prompt(
        self,
        question: str,
        retrieved_chunks: List[Any],
        role: str = "Banking Regulation & Financial Compliance",
        custom_system_prompt: Optional[str] = None,
        marker_style: Optional[SourceMarkerStyle] = None,
        budget_config: Optional[TokenBudgetConfig] = None,
        enforce_grounding: bool = True,
    ) -> AugmentedPrompt:
        """
        Tasks 1 to 4: Builds complete augmented prompt with grounding instructions,
        formatted context chunks, source markers, and strict token budget enforcement.
        """
        style = marker_style or self.default_marker_style
        cfg = budget_config or self.budget_config

        # 1. System Prompt with Grounding Instructions (Task 4)
        if custom_system_prompt:
            system_prompt = custom_system_prompt
            if enforce_grounding and "GROUNDING RULES" not in system_prompt:
                system_prompt = f"{system_prompt}\n\n{GROUNDING_INSTRUCTIONS}"
        else:
            if enforce_grounding:
                system_prompt = RAG_GROUNDED_SYSTEM_PROMPT.render(role=role)
            else:
                system_prompt = f"You are an expert AI assistant specialized in {role}."

        # 2. Compute Token Budget (Task 2)
        budget_calc = self.calculate_token_budget(
            system_prompt=system_prompt,
            question=question,
            budget_config=cfg,
        )

        # 3. Assemble Context Chunks with Source Markers (Task 1 & Task 3)
        assembled_ctx = self.assemble_context(
            chunks=retrieved_chunks,
            available_budget=budget_calc["available_context_budget"],
            style=style,
        )

        # 4. Render Final User Prompt with Injected Context
        user_prompt = RAG_CONTEXT_INJECTION_USER_PROMPT.render(
            context=assembled_ctx.formatted_context,
            question=question.strip(),
        )

        # 5. Token Accounting Summary
        total_prompt_tokens = self.count_tokens(system_prompt) + self.count_tokens(user_prompt)
        max_possible_total = total_prompt_tokens + cfg.max_answer_tokens

        token_accounting = {
            "model_limit": cfg.total_model_limit,
            "system_prompt_tokens": self.count_tokens(system_prompt),
            "context_tokens": assembled_ctx.context_tokens,
            "question_and_wrapper_tokens": self.count_tokens(user_prompt) - assembled_ctx.context_tokens,
            "total_prompt_tokens": total_prompt_tokens,
            "reserved_answer_tokens": cfg.max_answer_tokens,
            "safety_margin_tokens": cfg.safety_margin_tokens,
            "max_projected_total_tokens": max_possible_total,
            "remaining_headroom_tokens": max(0, cfg.total_model_limit - max_possible_total),
            "is_within_budget": max_possible_total <= cfg.total_model_limit,
        }

        return AugmentedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            question=question,
            assembled_context=assembled_ctx,
            source_marker_style=style.value,
            token_accounting=token_accounting,
            grounding_enforced=enforce_grounding,
        )

    def generate_grounded_answer(
        self,
        augmented_prompt: AugmentedPrompt,
        llm_client: Any,
        mock_response: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes chat completion with the augmented prompt and logs source tracing.
        """
        content, usage = llm_client.create_chat_completion(
            system_message=augmented_prompt.system_prompt,
            user_message=augmented_prompt.user_prompt,
            temperature=0.0,  # Deterministic, grounded generation
            max_tokens=augmented_prompt.token_accounting["reserved_answer_tokens"],
            mock_response=mock_response,
        )

        injected_sources = [
            {
                "marker": chunk.source_marker,
                "doc_id": chunk.doc_id,
                "filename": chunk.filename,
                "source_path": chunk.source_path,
                "section": chunk.section,
                "page_number": chunk.page_number,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.source_chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "raw_text": chunk.raw_text,
            }
            for chunk in augmented_prompt.assembled_context.injected_chunks
        ]
        attribution = attribute_answer(content or "", injected_sources)

        return {
            "question": augmented_prompt.question,
            "grounded_answer": attribution["answer"],
            "is_grounded": attribution["is_grounded"],
            "citation_status": attribution["citation_status"],
            "citations": attribution["citations"],
            "invalid_citations": attribution["invalid_citations"],
            "token_usage": usage,
            "injected_sources": injected_sources,
            "skipped_sources_count": len(augmented_prompt.assembled_context.skipped_chunks),
            "token_accounting": augmented_prompt.token_accounting,
        }

    def export_sample_artifacts(
        self,
        demonstration_payloads: List[Dict[str, Any]],
        output_json_path: str = os.path.join("outputs", "augmented_prompt_sample.json"),
        output_txt_path: str = os.path.join("outputs", "augmented_prompt_sample.txt"),
        output_md_path: str = os.path.join("outputs", "context_injection_report.md"),
    ):
        """
        Task 5: Exports structured JSON, human-readable prompt sample, and detailed markdown report.
        """
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

        # 1. Export JSON Artifact
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "milestone": "Context-Injection & Prompt-Augmentation",
                "tasks_covered": ["Task 1 - Inject Chunks", "Task 2 - Enforce Token Budget", "Task 3 - Source Markers", "Task 4 - Grounding Instructions", "Task 5 - Output Artifacts"],
                "total_demonstrations": len(demonstration_payloads),
                "demonstrations": demonstration_payloads,
            }, f, indent=2)

        # 2. Export Human-Readable TXT Prompt Sample
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write("================================================================================\n")
            f.write("        RAG CONTEXT INJECTION & PROMPT AUGMENTATION SAMPLE OUTPUT               \n")
            f.write("================================================================================\n\n")

            for idx, demo in enumerate(demonstration_payloads, 1):
                f.write(f"################################################################################\n")
                f.write(f"DEMONSTRATION #{idx}: {demo.get('title', 'Scenario ' + str(idx))}\n")
                f.write(f"Description: {demo.get('description', '')}\n")
                f.write(f"################################################################################\n\n")

                prompt_dict = demo.get("augmented_prompt", {})
                f.write("--- [SYSTEM PROMPT WITH GROUNDING INSTRUCTIONS (Task 4)] ---\n")
                f.write(prompt_dict.get("system_prompt", "") + "\n\n")

                f.write("--- [USER PROMPT WITH INJECTED CONTEXT & SOURCE MARKERS (Task 1 & 3)] ---\n")
                f.write(prompt_dict.get("user_prompt", "") + "\n\n")

                f.write("--- [TOKEN BUDGET ACCOUNTING (Task 2)] ---\n")
                accounting = prompt_dict.get("token_accounting", {})
                for k, v in accounting.items():
                    f.write(f"  * {k}: {v}\n")
                f.write("\n")

                f.write("--- [MODEL GROUNDED RESPONSE & CITATIONS] ---\n")
                gen_result = demo.get("generation_result", {})
                f.write(f"{gen_result.get('grounded_answer', 'N/A')}\n\n")
                f.write("================================================================================\n\n")

        # 3. Export Markdown Report
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write("# Context Injection & Prompt Augmentation Report\n\n")
            f.write("## Overview\n\n")
            f.write("This report documents the implementation and verification of the **Context Injection and Prompt Augmentation Engine**.\n\n")
            f.write("### Tasks Implemented\n\n")
            f.write("- **Task 1 — Inject Retrieved Chunks**: Formats retrieved chunks with clean metadata demarcation and injects them into the prompt's `[CONTEXT]` section.\n")
            f.write("- **Task 2 — Enforce Token Budget**: Calculates token consumption dynamically using `tiktoken` (`cl100k_base`), guaranteeing that context + system instructions + user question + answer reserves never exceed model context windows.\n")
            f.write("- **Task 3 — Include Source Markers**: Injects standardized citation markers (`[1]`, `[2]`, `[Source X: filename | Section]`) to enable direct, verifiable source citations in generated responses.\n")
            f.write("- **Task 4 — Add Grounding Instructions**: Enforces strict instructions preventing hallucinations and mandating clear statements when the context is insufficient.\n")
            f.write("- **Task 5 — Output Artifacts & Reproducibility**: Generates structured JSON samples (`outputs/augmented_prompt_sample.json`) and prompt inspection logs (`outputs/augmented_prompt_sample.txt`).\n\n")

            f.write("## Token Budget Allocation Formula (Task 2)\n\n")
            f.write("$$\\text{Available Context Budget} = \\text{Total Model Limit} - (\\text{System Tokens} + \\text{Question Tokens} + \\text{Template Overhead} + \\text{Max Answer Tokens} + \\text{Safety Margin})$$\n\n")

            f.write("## Demonstration Scenarios\n\n")
            for idx, demo in enumerate(demonstration_payloads, 1):
                f.write(f"### Scenario {idx}: {demo.get('title', '')}\n\n")
                f.write(f"{demo.get('description', '')}\n\n")
                acc = demo.get("augmented_prompt", {}).get("token_accounting", {})
                f.write("| Metric | Tokens |\n")
                f.write("| :--- | :--- |\n")
                f.write(f"| Model Limit | `{acc.get('model_limit', 'N/A')}` |\n")
                f.write(f"| System Prompt | `{acc.get('system_prompt_tokens', 'N/A')}` |\n")
                f.write(f"| Injected Context | `{acc.get('context_tokens', 'N/A')}` |\n")
                f.write(f"| Reserved Answer | `{acc.get('reserved_answer_tokens', 'N/A')}` |\n")
                f.write(f"| Total Projected Usage | `{acc.get('max_projected_total_tokens', 'N/A')}` |\n")
                f.write(f"| Within Budget? | **`{'YES' if acc.get('is_within_budget') else 'NO'}`** |\n\n")

                f.write("#### Generated Grounded Answer & Source Citations\n\n")
                f.write(f"> {demo.get('generation_result', {}).get('grounded_answer', '').replace(chr(10), chr(10) + '> ')}\n\n")
                f.write("---\n\n")

            f.write("## Conclusion\n\n")
            f.write("The context-injection engine successfully manages token headroom, prevents context-window overflow, incorporates traceable source markers, and strictly grounds LLM responses.\n")
