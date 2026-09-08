"""
Unit Tests for Hallucination Guardrails & Refusal Handling Engine (Tasks 1 to 5).
"""

import os
import sys
import unittest
import json
from unittest.mock import MagicMock

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from hallucination_guardrails import (
    HallucinationGuardrail,
    GuardrailConfig,
    GuardrailDecision,
    GuardrailResult,
    RetrievalQualitySignals,
)
from token_chunker import TokenChunk


class TestHallucinationGuardrails(unittest.TestCase):
    """Test suite covering Task 1 to Task 5 of Hallucination Guardrails."""

    def setUp(self):
        self.config = GuardrailConfig(
            min_similarity_threshold=0.35,
            min_chunks_above_threshold=1,
            min_keyword_overlap_ratio=0.15,
            min_context_character_length=40,
            standard_refusal_message="I do not have sufficient information to answer.",
        )
        self.mock_llm = MagicMock()
        self.mock_llm.create_chat_completion.return_value = (
            "According to the policy, expenditures over $50,000 require unanimous board approval [1].",
            {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        )
        self.guardrail = HallucinationGuardrail(config=self.config, llm_client=self.mock_llm)

        self.strong_chunks = [
            TokenChunk(
                chunk_id="chunk_001",
                text="Single capital expenditures exceeding $50,000 require unanimous board approval.",
                token_count=16,
                start_token=0,
                end_token=16,
                overlap_tokens=0,
                doc_id="DOC_001",
                filename="banking_policy.txt",
                section="Section 3: High-Value Thresholds",
            ),
            TokenChunk(
                chunk_id="chunk_002",
                text="Customer financial data must be encrypted at rest using AES-256 and in transit using TLS 1.3 or higher. Any data breach must be reported within 24 hours.",
                token_count=30,
                start_token=16,
                end_token=46,
                overlap_tokens=0,
                doc_id="DOC_001",
                filename="banking_policy.txt",
                section="Section 3: Data Protection",
            ),
        ]

    # --------------------------------------------------------------------------
    # TASK 1: Detect Weak Retrieval Tests
    # --------------------------------------------------------------------------
    def test_task_1_detect_empty_retrieval(self):
        """Verify empty retrieval (0 chunks) triggers safe refusal with proper signal flags."""
        decision = self.guardrail.evaluate_retrieval_quality(
            query="What are the Mars mining rules?",
            retrieved_chunks=[],
            similarity_scores=[],
        )

        self.assertTrue(decision.should_refuse)
        self.assertEqual(decision.verdict, "SAFE_REFUSAL")
        self.assertTrue(decision.quality_signals.is_empty_retrieval)
        self.assertIn("EMPTY_RETRIEVAL_RESULTS", decision.refusal_reasons[0])

    def test_task_1_detect_low_similarity_score(self):
        """Verify chunks with similarity score below threshold trigger refusal."""
        decision = self.guardrail.evaluate_retrieval_quality(
            query="What is the quantum satellite key rotation protocol?",
            retrieved_chunks=self.strong_chunks,
            similarity_scores=[0.15],  # Below 0.35 threshold
        )

        self.assertTrue(decision.should_refuse)
        self.assertTrue(decision.quality_signals.is_low_similarity)
        self.assertIn("LOW_SIMILARITY_SCORE", decision.refusal_reasons[0])

    def test_task_1_detect_insufficient_chunks_above_threshold(self):
        """Verify when too few chunks meet threshold, refusal is triggered."""
        strict_config = GuardrailConfig(min_similarity_threshold=0.50, min_chunks_above_threshold=2)
        strict_guardrail = HallucinationGuardrail(config=strict_config, llm_client=self.mock_llm)

        decision = strict_guardrail.evaluate_retrieval_quality(
            query="What is the high-value capital policy?",
            retrieved_chunks=self.strong_chunks,
            similarity_scores=[0.60],  # Only 1 chunk >= 0.50, but 2 required
        )

        self.assertTrue(decision.should_refuse)
        self.assertTrue(decision.quality_signals.is_insufficient_chunks)

    # --------------------------------------------------------------------------
    # TASK 2: Safe Refusal Generation Tests
    # --------------------------------------------------------------------------
    def test_task_2_safe_refusal_generation_without_llm_call(self):
        """Verify weak retrieval returns safe refusal message without invoking generative LLM."""
        result = self.guardrail.process_query(
            query="What are the deep space communication protocols?",
            retrieved_chunks=[],
            similarity_scores=[],
        )

        self.assertTrue(result.is_refusal)
        self.assertEqual(result.final_answer, self.config.standard_refusal_message)
        self.assertEqual(len(result.cited_sources), 0)
        self.assertEqual(result.token_usage["total_tokens"], 0)
        self.mock_llm.create_chat_completion.assert_not_called()

    # --------------------------------------------------------------------------
    # TASK 3: Relevance Thresholds & Quality Checks Tests
    # --------------------------------------------------------------------------
    def test_task_3_weak_keyword_overlap_trigger(self):
        """Verify query terms not appearing in retrieved text trigger weak lexical alignment refusal."""
        unrelated_text_chunk = [
            TokenChunk(
                chunk_id="chunk_unrelated",
                text="The local sports tournament concluded with high attendance across all city stadiums.",
                token_count=15,
                start_token=0,
                end_token=15,
                overlap_tokens=0,
                doc_id="DOC_NEWS",
                filename="news.txt",
                section="Sports",
            )
        ]

        decision = self.guardrail.evaluate_retrieval_quality(
            query="Explain cryptocurrency liquidity staking yields and decentralized token bridges.",
            retrieved_chunks=unrelated_text_chunk,
            similarity_scores=[0.38],  # Score above threshold, but 0% keyword overlap
        )

        self.assertTrue(decision.should_refuse)
        self.assertTrue(decision.quality_signals.is_weak_lexical_alignment)

    # --------------------------------------------------------------------------
    # TASK 4: Preserve Confident Answers Tests
    # --------------------------------------------------------------------------
    def test_task_4_preserve_confident_grounded_answer(self):
        """Verify strong context proceeds to confident grounded generation with citations."""
        self.mock_llm.create_chat_completion.return_value = (
            "According to the policy, expenditures over $50,000 require unanimous board approval [1].",
            {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        )

        result = self.guardrail.process_query(
            query="What is the authorization threshold for capital expenditures?",
            retrieved_chunks=self.strong_chunks,
            similarity_scores=[0.85],
        )

        self.assertFalse(result.is_refusal)
        self.assertEqual(result.decision.verdict, "PROCEED_CONFIDENT_ANSWER")
        self.assertIn("[1]", result.final_answer)
        self.assertGreater(len(result.cited_sources), 0)

    # --------------------------------------------------------------------------
    # TASK 5: Artifact Export Tests
    # --------------------------------------------------------------------------
    def test_task_5_export_sample_artifacts(self):
        """Verify export_sample_artifacts writes valid JSON, TXT, and Markdown files."""
        demo_summary = self.guardrail.run_demonstration_suite(sample_chunks=self.strong_chunks)

        test_json = os.path.join("outputs", "test_guardrail_results.json")
        test_txt = os.path.join("outputs", "test_guardrail_sample.txt")
        test_md = os.path.join("outputs", "test_guardrail_report.md")

        self.guardrail.export_sample_artifacts(
            demo_summary=demo_summary,
            output_json_path=test_json,
            output_txt_path=test_txt,
            output_md_path=test_md,
        )

        self.assertTrue(os.path.exists(test_json))
        self.assertTrue(os.path.exists(test_txt))
        self.assertTrue(os.path.exists(test_md))

        with open(test_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertGreater(data["total_cases_evaluated"], 0)
            self.assertGreater(data["refusal_cases_count"], 0)
            self.assertGreater(data["confident_cases_count"], 0)

        # Cleanup
        for p in [test_json, test_txt, test_md]:
            if os.path.exists(p):
                os.remove(p)


if __name__ == "__main__":
    unittest.main()
