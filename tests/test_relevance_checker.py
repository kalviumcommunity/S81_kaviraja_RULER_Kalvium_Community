"""
Unit and Integration Tests for Relevance Quality Check and Sanity Suite (Tasks 1 - 5).

Validates:
1. Task 1: Default test suite generation with known query-chunk pairs.
2. Task 2: Ranking related chunks above unrelated chunks and calculating score margins.
3. Task 3: Identifying and diagnosing failing/surprising edge cases (e.g. vector negation blindspot).
4. Task 4: Compiling summary sanity statistics (test counts, pass rates, diagnostic notes).
5. Task 5: File persistence for relevance sanity report (TXT and JSON).
"""

import os
import json
import pytest
from typing import List

from src.relevance_checker import (
    RelevanceSanityChecker,
    RelevanceTestCase,
    TestCaseResult,
)
from src.similarity_ranker import SimilarityRanker
from src.chunk_embedding_pipeline import EmbeddedChunk


class MockLLMClient:
    """Mock LLMClient for deterministic relevance testing without external API calls."""

    class Logger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    def __init__(self):
        self.logger = self.Logger()
        self.base_url = "https://mock.api/v1"
        self.embedding_model = "mock-embedding-model"

    def generate_embeddings(self, texts: List[str], model=None):
        embeddings = []
        for t in texts:
            t_lower = t.lower()
            if "suspicious" in t_lower or "aml" in t_lower or "country risk" in t_lower:
                embeddings.append([0.9, 0.1, 0.0, 0.0])
            elif "basel" in t_lower or "tier 1" in t_lower or "capital ratio" in t_lower:
                embeddings.append([0.0, 0.9, 0.1, 0.0])
            elif "disbursements" in t_lower or "unanimous board" in t_lower or "high-value" in t_lower or "thresholds" in t_lower:
                embeddings.append([0.0, 0.0, 0.9, 0.1])
            else:
                embeddings.append([0.1, 0.1, 0.1, 0.1])
        usage = {"prompt_tokens": 10, "total_tokens": 10}
        return embeddings, usage


@pytest.fixture
def sample_embedded_chunks():
    return [
        EmbeddedChunk(
            chunk_id="chunk_aml_001",
            source_text="Financial institutions must establish automated compliance monitoring systems for suspicious transactions under Anti-Money Laundering (AML) directives.",
            embedding=[0.9, 0.1, 0.0, 0.0],
            dimension=4,
            metadata={"filename": "regulation.txt", "section": "Section 1: Executive Summary & Overview"}
        ),
        EmbeddedChunk(
            chunk_id="chunk_capital_002",
            source_text="Under Basel IV standards, Tier 1 common equity capital ratio must remain above 10.5% of total risk-weighted assets.",
            embedding=[0.0, 0.9, 0.1, 0.0],
            dimension=4,
            metadata={"filename": "regulation.txt", "section": "Section 2: Capital Reserves & Liquidity Ratios"}
        ),
        EmbeddedChunk(
            chunk_id="chunk_payments_003",
            source_text="Vendor disbursements exceeding $50,000 require unanimous board authorization and audit report prior to disbursement.",
            embedding=[0.0, 0.0, 0.9, 0.1],
            dimension=4,
            metadata={"filename": "regulation.txt", "section": "Section 3: High-Value Transaction Authorization Thresholds"}
        ),
    ]


def test_get_default_test_suite():
    checker = RelevanceSanityChecker(ranker=SimilarityRanker(client=MockLLMClient()))
    suite = checker.get_default_test_suite()

    assert len(suite) >= 5
    test_ids = [tc.test_id for tc in suite]
    assert "TEST-001" in test_ids
    assert "TEST-002" in test_ids
    assert "TEST-003" in test_ids
    assert "TEST-004" in test_ids  # Negation case
    assert "TEST-005" in test_ids  # Lexical distractor case


def test_evaluate_standard_test_case_pass(sample_embedded_chunks):
    mock_client = MockLLMClient()
    ranker = SimilarityRanker(client=mock_client, metric="cosine")
    checker = RelevanceSanityChecker(ranker=ranker)

    test_case = RelevanceTestCase(
        test_id="TEST-001",
        query="How are suspicious transactions monitored?",
        category="Standard Relevance",
        target_keywords=["suspicious transactions", "AML"],
        target_section="Section 1: Executive Summary & Overview",
        is_surprising_case=False
    )

    res = checker.evaluate_test_case(test_case, sample_embedded_chunks)

    assert res.passed is True
    assert res.actual_top_chunk_id == "chunk_aml_001"
    assert res.actual_top_score > 0.8
    assert res.score_margin_over_runner_up > 0.0
    assert "PASS" in res.diagnostic_note


def test_evaluate_failing_negation_case(sample_embedded_chunks):
    mock_client = MockLLMClient()
    ranker = SimilarityRanker(client=mock_client, metric="cosine")
    checker = RelevanceSanityChecker(ranker=ranker)

    negation_test_case = RelevanceTestCase(
        test_id="TEST-004",
        query="Which vendor disbursements do NOT require unanimous board approval?",
        category="Failing / Surprising Case (Negation)",
        target_keywords=["under $50,000", "approved directly"],
        target_section="Section 3: High-Value Transaction Authorization Thresholds",
        is_surprising_case=True
    )

    res = checker.evaluate_test_case(negation_test_case, sample_embedded_chunks)

    assert res.passed is False
    assert res.is_surprising_case is True
    assert "Vector Negation Blindspot" in res.diagnostic_note
    assert "NOT" in res.diagnostic_note


def test_run_sanity_check_with_mock_chunks(sample_embedded_chunks):
    mock_client = MockLLMClient()
    ranker = SimilarityRanker(client=mock_client, metric="cosine")
    checker = RelevanceSanityChecker(ranker=ranker)

    summary = checker.run_sanity_check(embedded_chunks=sample_embedded_chunks)

    assert summary["total_test_count"] == 5
    assert summary["standard_tests_count"] == 3
    assert summary["standard_passes"] == 3
    assert summary["pass_rate_percentage"] == 100.0
    assert summary["surprising_cases_count"] == 2
    assert "failing_or_surprising_case_summary" in summary
    assert summary["failing_or_surprising_case_summary"]["case_id"] == "TEST-004"


def test_generate_sanity_report_files(tmp_path, sample_embedded_chunks):
    mock_client = MockLLMClient()
    ranker = SimilarityRanker(client=mock_client, metric="cosine")
    checker = RelevanceSanityChecker(ranker=ranker)

    summary = checker.run_sanity_check(embedded_chunks=sample_embedded_chunks)

    txt_file = os.path.join(tmp_path, "relevance_sanity_report.txt")
    json_file = os.path.join(tmp_path, "relevance_sanity_results.json")

    checker.generate_sanity_report(summary, output_txt_path=txt_file, output_json_path=json_file)

    assert os.path.exists(txt_file)
    assert os.path.exists(json_file)

    with open(txt_file, "r", encoding="utf-8") as f:
        txt_content = f.read()
    assert "RAG PIPELINE RELEVANCE SANITY REPORT" in txt_content
    assert "TASK 3: FAILING OR SURPRISING CASE DETAILED ANALYSIS" in txt_content

    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    assert json_data["total_test_count"] == 5
    assert len(json_data["test_results"]) == 5
