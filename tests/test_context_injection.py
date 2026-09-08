"""
Unit Tests for Context Injection & Prompt Augmentation Engine (Tasks 1 to 5).
"""

import os
import sys
import unittest
import json
from unittest.mock import MagicMock

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from context_injection import (
    ContextInjector,
    TokenBudgetConfig,
    SourceMarkerStyle,
    InjectedChunkInfo,
    SkippedChunkInfo,
    AssembledContext,
    AugmentedPrompt,
)
from token_chunker import TokenChunk
from prompts.templates import (
    GROUNDING_INSTRUCTIONS,
    RAG_GROUNDED_SYSTEM_PROMPT,
    RAG_CONTEXT_INJECTION_USER_PROMPT,
)


class TestContextInjection(unittest.TestCase):
    """Test suite covering Task 1 to Task 5 of Context Injection & Prompt Augmentation."""

    def setUp(self):
        self.injector = ContextInjector(
            budget_config=TokenBudgetConfig(total_model_limit=2000, max_answer_tokens=300),
            default_marker_style=SourceMarkerStyle.NUMBERED,
        )
        self.sample_chunks = [
            TokenChunk(
                chunk_id="DOC_001#chunk_001",
                text="Vendor transactions under $50,000 may be approved directly by department heads.",
                token_count=16,
                start_token=0,
                end_token=16,
                overlap_tokens=0,
                doc_id="DOC_001",
                filename="banking_policy.txt",
                section="Section 1: General Authorizations",
                page_number=1,
            ),
            TokenChunk(
                chunk_id="DOC_001#chunk_002",
                text="Single capital expenditures exceeding $50,000 require unanimous board approval.",
                token_count=14,
                start_token=16,
                end_token=30,
                overlap_tokens=0,
                doc_id="DOC_001",
                filename="banking_policy.txt",
                section="Section 2: High-Value Thresholds",
                page_number=2,
            ),
            TokenChunk(
                chunk_id="DOC_002#chunk_001",
                text="Data breaches must be reported to the regulatory authority within 24 hours of discovery.",
                token_count=17,
                start_token=0,
                end_token=17,
                overlap_tokens=0,
                doc_id="DOC_002",
                filename="data_security.txt",
                section="Section 4: Incident Response",
                page_number=5,
            ),
        ]

    # --------------------------------------------------------------------------
    # TASK 1: Inject Retrieved Chunks Tests
    # --------------------------------------------------------------------------
    def test_task_1_chunk_formatting_and_injection(self):
        """Verify chunks are cleanly formatted with metadata and injected into context."""
        chunk = self.sample_chunks[0]
        formatted_str, meta, marker = self.injector.format_chunk(
            chunk=chunk,
            index=1,
            style=SourceMarkerStyle.NUMBERED,
        )

        self.assertIn("[1]", marker)
        self.assertIn("--- [1]", formatted_str)
        self.assertIn("banking_policy.txt", formatted_str)
        self.assertIn("Section 1: General Authorizations", formatted_str)
        self.assertIn("Vendor transactions under $50,000", formatted_str)
        self.assertEqual(meta["chunk_id"], "DOC_001#chunk_001")

    def test_task_1_dict_and_string_chunk_injection(self):
        """Verify context injector accepts dictionary and raw string chunk formats."""
        dict_chunk = {
            "chunk_id": "DICT_001",
            "text": "Artificial Intelligence revolutionizes search through semantic embeddings.",
            "doc_id": "DOC_AI",
            "filename": "ai_overview.txt",
            "section": "Intro",
        }
        formatted_str, meta, marker = self.injector.format_chunk(dict_chunk, index=2)
        self.assertIn("DICT_001", formatted_str)
        self.assertIn("ai_overview.txt", formatted_str)
        self.assertEqual(marker, "[2]")

    # --------------------------------------------------------------------------
    # TASK 2: Enforce Token Budget Tests
    # --------------------------------------------------------------------------
    def test_task_2_token_budget_calculation(self):
        """Verify dynamic token budget calculation leaves guaranteed room for answer and prompt."""
        budget_calc = self.injector.calculate_token_budget(
            system_prompt="You are a helpful assistant.",
            question="What is the high-value transaction threshold?",
        )

        self.assertEqual(budget_calc["total_model_limit"], 2000)
        self.assertEqual(budget_calc["reserved_answer_tokens"], 300)
        self.assertGreater(budget_calc["available_context_budget"], 0)
        self.assertLess(budget_calc["available_context_budget"], 2000)
        
        # Verify formula exactness: available = model_limit - non_context_allocation
        expected_available = 2000 - budget_calc["non_context_allocation_total"]
        self.assertEqual(budget_calc["available_context_budget"], expected_available)

    def test_task_2_strict_token_budget_skipping_overflow_chunks(self):
        """Verify candidate chunks exceeding budget are skipped without crashing."""
        # Create a very tight budget of 50 tokens
        tiny_budget = 50
        assembled = self.injector.assemble_context(
            chunks=self.sample_chunks,
            available_budget=tiny_budget,
        )

        self.assertLessEqual(assembled.context_tokens, tiny_budget)
        self.assertGreater(assembled.total_skipped_chunks, 0)
        self.assertEqual(assembled.total_injected_chunks + assembled.total_skipped_chunks, len(self.sample_chunks))
        self.assertEqual(assembled.skipped_chunks[0].reason, "EXCEEDED_TOKEN_BUDGET")

    def test_task_2_full_prompt_stays_within_model_limit(self):
        """Verify the built AugmentedPrompt strictly satisfies model context window constraints."""
        aug_prompt = self.injector.build_augmented_prompt(
            question="What are the approval thresholds and incident response rules?",
            retrieved_chunks=self.sample_chunks,
        )

        acc = aug_prompt.token_accounting
        self.assertTrue(acc["is_within_budget"])
        self.assertLessEqual(acc["max_projected_total_tokens"], acc["model_limit"])

    # --------------------------------------------------------------------------
    # TASK 3: Source Markers Tests
    # --------------------------------------------------------------------------
    def test_task_3_numbered_source_markers(self):
        """Verify [1], [2], [3] numbered source marker formatting."""
        marker_1 = self.injector.format_source_marker(1, {"filename": "doc.txt"}, SourceMarkerStyle.NUMBERED)
        marker_2 = self.injector.format_source_marker(2, {"filename": "doc.txt"}, SourceMarkerStyle.NUMBERED)
        self.assertEqual(marker_1, "[1]")
        self.assertEqual(marker_2, "[2]")

    def test_task_3_verbose_and_inline_source_markers(self):
        """Verify verbose and inline tag marker styles."""
        meta = {
            "chunk_id": "CHK_999",
            "filename": "annual_report.pdf",
            "section": "Financial Highlights",
            "page_number": 12,
        }
        verbose_marker = self.injector.format_source_marker(1, meta, SourceMarkerStyle.VERBOSE)
        inline_marker = self.injector.format_source_marker(1, meta, SourceMarkerStyle.INLINE_TAG)
        citation_marker = self.injector.format_source_marker(1, meta, SourceMarkerStyle.CITATION_KEY)

        self.assertIn("Source 1: annual_report.pdf", verbose_marker)
        self.assertIn("Section: Financial Highlights", verbose_marker)
        self.assertIn("Page 12", verbose_marker)
        self.assertEqual(inline_marker, "[CHK_999]")
        self.assertIn("[Source: annual_report.pdf, Page 12]", citation_marker)

    # --------------------------------------------------------------------------
    # TASK 4: Grounding Instructions Tests
    # --------------------------------------------------------------------------
    def test_task_4_grounding_rules_in_system_prompt(self):
        """Verify grounding instructions and refusal mandate are injected into system prompt."""
        aug_prompt = self.injector.build_augmented_prompt(
            question="What is the interest rate?",
            retrieved_chunks=self.sample_chunks,
            enforce_grounding=True,
        )

        sys_prompt = aug_prompt.system_prompt
        self.assertIn("GROUNDING RULES:", sys_prompt)
        self.assertIn("Answer the user's question ONLY using the factual information provided in the [CONTEXT]", sys_prompt)
        self.assertIn("Do NOT assume, extrapolate, or invent facts", sys_prompt)
        self.assertIn("The provided context does not contain sufficient information to answer this question", sys_prompt)
        self.assertIn("Cite your sources using the chunk markers", sys_prompt)

    def test_task_4_grounded_answer_generation_with_citations(self):
        """Verify generate_grounded_answer properly uses LLM client and records source tracing."""
        mock_llm = MagicMock()
        mock_llm.create_chat_completion.return_value = (
            "According to [1], transactions under $50,000 can be approved directly.",
            {"prompt_tokens": 120, "completion_tokens": 25, "total_tokens": 145},
        )

        aug_prompt = self.injector.build_augmented_prompt(
            question="What can be approved directly?",
            retrieved_chunks=[self.sample_chunks[0]],
        )

        result = self.injector.generate_grounded_answer(aug_prompt, mock_llm)
        self.assertIn("[1]", result["grounded_answer"])
        self.assertEqual(len(result["injected_sources"]), 1)
        self.assertEqual(result["injected_sources"][0]["doc_id"], "DOC_001")
        mock_llm.create_chat_completion.assert_called_once()

    # --------------------------------------------------------------------------
    # TASK 5: Output Artifacts & JSON Export Tests
    # --------------------------------------------------------------------------
    def test_task_5_export_sample_artifacts(self):
        """Verify export_sample_artifacts produces valid JSON, TXT, and Markdown files."""
        aug_prompt = self.injector.build_augmented_prompt(
            question="Summarize compliance rules.",
            retrieved_chunks=self.sample_chunks[:2],
        )

        demo_payload = {
            "scenario_id": "TEST_DEMO",
            "title": "Unit Test Demo",
            "description": "Test description",
            "augmented_prompt": aug_prompt.to_dict(),
            "generation_result": {
                "grounded_answer": "Grounded answer text [1].",
            },
        }

        test_json = os.path.join("outputs", "test_augmented_prompt_sample.json")
        test_txt = os.path.join("outputs", "test_augmented_prompt_sample.txt")
        test_md = os.path.join("outputs", "test_context_injection_report.md")

        self.injector.export_sample_artifacts(
            demonstration_payloads=[demo_payload],
            output_json_path=test_json,
            output_txt_path=test_txt,
            output_md_path=test_md,
        )

        self.assertTrue(os.path.exists(test_json))
        self.assertTrue(os.path.exists(test_txt))
        self.assertTrue(os.path.exists(test_md))

        with open(test_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["total_demonstrations"], 1)
            self.assertIn("augmented_prompt", data["demonstrations"][0])

        # Cleanup test files
        for p in [test_json, test_txt, test_md]:
            if os.path.exists(p):
                os.remove(p)


if __name__ == "__main__":
    unittest.main()
