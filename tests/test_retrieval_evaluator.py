"""
Unit and Integration Test Suite for Retrieval Evaluation Suite (Tasks 1 to 5).

Validates:
1. Task 1: Labelled query dataset loading and schema validation.
2. Task 2: Recall@K and Hit@K mathematical accuracy.
3. Task 3: Precision@K, MRR, F1, and graded relevance scoring.
4. Task 4: Failure inspector root cause categorization (negation, cross-section distraction, fragmentation).
5. Task 5: Report generation, summary export, and file persistence.
"""

import os
import json
import pytest
from typing import List

from src.retrieval_evaluator import (
    LabelledQuery,
    load_labelled_queries,
    calculate_recall_at_k,
    calculate_hit_at_k,
    calculate_precision_at_k,
    calculate_reciprocal_rank,
    calculate_f1_score,
    assign_graded_relevance,
    FailureInspector,
    RetrievalEvaluator,
)
from src.similarity_ranker import SimilarityRanker
from src.chunk_embedding_pipeline import EmbeddedChunk


class MockLLMClient:
    """Mock client for fast, deterministic, offline test runs."""

    class Logger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    def __init__(self):
        self.logger = self.Logger()
        self.base_url = "https://mock.api/v1"
        self.embedding_model = "mock-model"

    def generate_embeddings(self, texts: List[str], model=None):
        embeddings = []
        for t in texts:
            t_lower = t.lower()
            if "suspicious" in t_lower or "aml" in t_lower or "sanction" in t_lower:
                embeddings.append([0.9, 0.1, 0.0, 0.0])
            elif "basel" in t_lower or "tier 1" in t_lower or "capital" in t_lower or "liquidity coverage" in t_lower:
                embeddings.append([0.0, 0.9, 0.1, 0.0])
            elif "disbursements" in t_lower or "high-value" in t_lower or "$50,000" in t_lower:
                embeddings.append([0.0, 0.0, 0.9, 0.1])
            else:
                embeddings.append([0.2, 0.2, 0.2, 0.2])
        return embeddings, {"prompt_tokens": 10, "total_tokens": 10}


@pytest.fixture
def mock_corpus() -> List[EmbeddedChunk]:
    return [
        EmbeddedChunk(
            chunk_id="chunk_sec1_001",
            source_text="AML directives and transaction monitoring for suspicious transactions.",
            embedding=[0.9, 0.1, 0.0, 0.0],
            dimension=4,
            metadata={"section": "Section 1: Executive Summary & Overview", "filename": "reg.txt"}
        ),
        EmbeddedChunk(
            chunk_id="chunk_sec2_002",
            source_text="Basel IV Tier 1 capital adequacy standards and Liquidity Coverage Ratio.",
            embedding=[0.0, 0.9, 0.1, 0.0],
            dimension=4,
            metadata={"section": "Section 2: Capital Reserves & Liquidity Ratios", "filename": "reg.txt"}
        ),
        EmbeddedChunk(
            chunk_id="chunk_sec3_003",
            source_text="Routine payments under $50,000 approved directly by department heads.",
            embedding=[0.0, 0.0, 0.85, 0.15],
            dimension=4,
            metadata={"section": "Section 3: High-Value Transaction Authorization Thresholds", "filename": "reg.txt"}
        ),
        EmbeddedChunk(
            chunk_id="chunk_sec3_004",
            source_text="High-value disbursements exceeding $50,000 require unanimous board approval.",
            embedding=[0.0, 0.0, 0.95, 0.05],
            dimension=4,
            metadata={"section": "Section 3: High-Value Transaction Authorization Thresholds", "filename": "reg.txt"}
        ),
    ]


# ==============================================================================
# TASK 1 TESTS: LABELLED QUERIES
# ==============================================================================

def test_load_labelled_queries():
    queries = load_labelled_queries()
    assert len(queries) >= 8
    q_ids = [q.query_id for q in queries]
    assert "Q-001" in q_ids
    assert "Q-002" in q_ids
    assert "Q-003" in q_ids
    assert "Q-004" in q_ids

    # Verify query attributes
    q1 = next(q for q in queries if q.query_id == "Q-001")
    assert len(q1.expected_chunk_ids) > 0
    assert q1.target_section != ""
    assert q1.category != ""


# ==============================================================================
# TASK 2 TESTS: RECALL@K & HIT@K
# ==============================================================================

def test_calculate_recall_at_k():
    retrieved = ["c1", "c2", "c3", "c4"]
    expected = ["c2", "c3"]

    # K=1: retrieved ["c1"], hits = 0 -> Recall = 0.0
    assert calculate_recall_at_k(retrieved, expected, k=1) == 0.0

    # K=2: retrieved ["c1", "c2"], hits = 1/2 -> Recall = 0.5
    assert calculate_recall_at_k(retrieved, expected, k=2) == 0.5

    # K=3: retrieved ["c1", "c2", "c3"], hits = 2/2 -> Recall = 1.0
    assert calculate_recall_at_k(retrieved, expected, k=3) == 1.0


def test_calculate_hit_at_k():
    retrieved = ["c1", "c2", "c3"]
    expected = ["c2"]

    assert calculate_hit_at_k(retrieved, expected, k=1) == 0
    assert calculate_hit_at_k(retrieved, expected, k=2) == 1
    assert calculate_hit_at_k(retrieved, expected, k=3) == 1


# ==============================================================================
# TASK 3 TESTS: PRECISION@K, MRR, F1 & QUALITY SIGNALS
# ==============================================================================

def test_calculate_precision_at_k():
    retrieved = ["c1", "c2", "c3"]
    expected = ["c1", "c3"]

    assert calculate_precision_at_k(retrieved, expected, k=1) == 1.0  # 1/1
    assert calculate_precision_at_k(retrieved, expected, k=2) == 0.5  # 1/2
    assert calculate_precision_at_k(retrieved, expected, k=3) == 0.6667  # 2/3


def test_calculate_reciprocal_rank():
    assert calculate_reciprocal_rank(["c1", "c2", "c3"], ["c1"]) == 1.0
    assert calculate_reciprocal_rank(["c1", "c2", "c3"], ["c2"]) == 0.5
    assert calculate_reciprocal_rank(["c1", "c2", "c3"], ["c3"]) == 0.3333
    assert calculate_reciprocal_rank(["c1", "c2", "c3"], ["c99"]) == 0.0


def test_calculate_f1_score():
    assert calculate_f1_score(1.0, 1.0) == 1.0
    assert calculate_f1_score(0.0, 0.0) == 0.0
    assert pytest.approx(calculate_f1_score(0.5, 1.0), 0.001) == 0.6667


def test_assign_graded_relevance():
    meta_sec1 = {"section": "Section 1: Executive Summary & Overview"}
    meta_sec3 = {"section": "Section 3: High-Value Transaction Authorization Thresholds"}

    # Highly relevant (exact chunk match) -> 2
    assert assign_graded_relevance("c1", ["c1"], "Section 1: Executive Summary & Overview", meta_sec1) == 2

    # Partially relevant (same section, different chunk) -> 1
    assert assign_graded_relevance("c2", ["c1"], "Section 1: Executive Summary & Overview", meta_sec1) == 1

    # Irrelevant (different section) -> 0
    assert assign_graded_relevance("c3", ["c1"], "Section 1: Executive Summary & Overview", meta_sec3) == 0


# ==============================================================================
# TASK 4 TESTS: FAILURE INSPECTOR
# ==============================================================================

def test_failure_inspector_diagnoses_negation():
    lq = LabelledQuery(
        query_id="Q-004",
        query="Which vendor disbursements do NOT require unanimous board approval?",
        category="Negation Blindspot",
        target_section="Section 3: High-Value Transaction Authorization Thresholds",
        expected_chunk_ids=["chunk_sec3_003"],
        min_acceptable_rank=1
    )
    # Simulated failure: Chunk 4 ranked #1, target Chunk 3 ranked #2
    ranked_chunks = [
        {"chunk_id": "chunk_sec3_004", "metadata": {"section": "Section 3: High-Value Transaction Authorization Thresholds"}},
        {"chunk_id": "chunk_sec3_003", "metadata": {"section": "Section 3: High-Value Transaction Authorization Thresholds"}}
    ]
    retrieved_ids = ["chunk_sec3_004", "chunk_sec3_003"]

    report = FailureInspector.inspect_query_result(lq, ranked_chunks, retrieved_ids)
    assert report.is_failure is True
    assert report.failure_type == "EMBEDDING_NEGATION_BLINDSPOT"
    assert "logical negation" in report.root_cause.lower()
    assert report.top_rank_achieved == 2


def test_failure_inspector_diagnoses_cross_section_distraction():
    lq = LabelledQuery(
        query_id="Q-TEST",
        query="What audit compliance requirements apply to payment authorization?",
        category="Cross-Section Lexical Distractor",
        target_section="Section 3: High-Value Transaction Authorization Thresholds",
        expected_chunk_ids=["chunk_sec3_003"],
        min_acceptable_rank=1
    )
    # Simulated failure: Section 1 chunk ranked #1 instead of Section 3
    ranked_chunks = [
        {"chunk_id": "chunk_sec1_001", "metadata": {"section": "Section 1: Executive Summary & Overview"}},
        {"chunk_id": "chunk_sec3_003", "metadata": {"section": "Section 3: High-Value Transaction Authorization Thresholds"}}
    ]
    retrieved_ids = ["chunk_sec1_001", "chunk_sec3_003"]

    report = FailureInspector.inspect_query_result(lq, ranked_chunks, retrieved_ids)
    assert report.is_failure is True
    assert report.failure_type == "CROSS_SECTION_LEXICAL_DISTRACTION"
    assert "Shared vocabulary" in report.root_cause


# ==============================================================================
# TASK 5 TESTS: END-TO-END SUITE & PERSISTENCE
# ==============================================================================

def test_retrieval_evaluator_end_to_end(mock_corpus):
    mock_client = MockLLMClient()
    evaluator = RetrievalEvaluator(client=mock_client)

    queries = [
        LabelledQuery(
            query_id="T-01",
            query="AML compliance monitoring for suspicious transactions",
            category="Standard",
            target_section="Section 1: Executive Summary & Overview",
            expected_chunk_ids=["chunk_sec1_001"],
            min_acceptable_rank=1
        ),
        LabelledQuery(
            query_id="T-02",
            query="Basel IV Tier 1 capital adequacy ratio",
            category="Standard",
            target_section="Section 2: Capital Reserves & Liquidity Ratios",
            expected_chunk_ids=["chunk_sec2_002"],
            min_acceptable_rank=1
        ),
    ]

    summary = evaluator.run_evaluation_suite(
        embedded_chunks=mock_corpus,
        queries=queries,
        mode="vector",
        k_values=[1, 2, 3]
    )

    meta = summary["evaluation_metadata"]
    agg = summary["aggregate_metrics"]

    assert meta["total_queries_evaluated"] == 2
    assert agg["mean_reciprocal_rank_mrr"] > 0.0
    assert "k_1" in agg["metrics_by_depth"]
    assert "k_2" in agg["metrics_by_depth"]
    assert "k_3" in agg["metrics_by_depth"]


def test_export_evaluation_reports(tmp_path, mock_corpus):
    mock_client = MockLLMClient()
    evaluator = RetrievalEvaluator(client=mock_client)

    queries = [
        LabelledQuery(
            query_id="T-01",
            query="AML compliance monitoring",
            category="Standard",
            target_section="Section 1",
            expected_chunk_ids=["chunk_sec1_001"]
        )
    ]

    eval_summary = evaluator.run_evaluation_suite(mock_corpus, queries=queries, k_values=[1, 2])

    out_txt = str(tmp_path / "eval_report.txt")
    out_json = str(tmp_path / "eval_results.json")
    fail_txt = str(tmp_path / "fail_report.txt")
    fail_json = str(tmp_path / "fail_results.json")

    evaluator.export_evaluation_reports(
        eval_summary=eval_summary,
        output_txt_path=out_txt,
        output_json_path=out_json,
        failure_txt_path=fail_txt,
        failure_json_path=fail_json
    )

    assert os.path.exists(out_txt)
    assert os.path.exists(out_json)
    assert os.path.exists(fail_txt)
    assert os.path.exists(fail_json)

    with open(out_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "aggregate_metrics" in data
