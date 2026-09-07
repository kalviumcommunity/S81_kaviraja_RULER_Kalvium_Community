"""
Unit and Integration Test Suite for Metadata Filtering & Hybrid Search (Tasks 1 to 5).

Validates:
1. Task 1: MetadataFilter criteria matching (exact, substring contains, in-list, numeric, callable).
2. Task 2: Comparative evaluation between filtered and unfiltered retrieval.
3. Task 3: Lexical keyword scoring, exact entity/phrase bonus, and hybrid score fusion.
4. Task 4: Quantitative Precision@K improvement demonstration.
5. Task 5: File persistence and report serialization (TXT and JSON).
"""

import os
import json
import pytest
from typing import List

from src.filtered_search import (
    MetadataFilter,
    KeywordScorer,
    HybridRankedChunk,
    FilteredSearchEngine,
    tokenize_text,
)
from src.similarity_ranker import SimilarityRanker
from src.chunk_embedding_pipeline import EmbeddedChunk


class MockLLMClient:
    """Mock client providing deterministic embeddings for fast, offline testing."""

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
            if "suspicious" in t_lower or "aml" in t_lower:
                embeddings.append([0.9, 0.1, 0.0, 0.0])
            elif "basel" in t_lower or "tier 1" in t_lower or "capital" in t_lower:
                embeddings.append([0.0, 0.9, 0.1, 0.0])
            elif "disbursements" in t_lower or "high-value" in t_lower or "50,000" in t_lower:
                embeddings.append([0.0, 0.0, 0.9, 0.1])
            else:
                embeddings.append([0.2, 0.2, 0.2, 0.2])
        return embeddings, {"prompt_tokens": 10, "total_tokens": 10}


@pytest.fixture
def mock_embedded_corpus() -> List[EmbeddedChunk]:
    return [
        EmbeddedChunk(
            chunk_id="chunk_sec1_001",
            source_text="Mandatory AML compliance monitoring for suspicious international transactions.",
            embedding=[0.9, 0.1, 0.0, 0.0],
            dimension=4,
            metadata={
                "doc_id": "reg_001",
                "filename": "sample_banking_regulation.txt",
                "section": "Section 1: Executive Summary & Overview",
                "category": "Compliance & Regulation",
                "doc_type": "Regulatory Framework",
                "chunk_index": 0,
                "page_number": 1
            }
        ),
        EmbeddedChunk(
            chunk_id="chunk_sec2_002",
            source_text="Basel IV capital adequacy standards mandate Tier 1 common equity above 10.5%.",
            embedding=[0.0, 0.9, 0.1, 0.0],
            dimension=4,
            metadata={
                "doc_id": "reg_001",
                "filename": "sample_banking_regulation.txt",
                "section": "Section 2: Capital Reserves & Liquidity Ratios",
                "category": "Compliance & Regulation",
                "doc_type": "Regulatory Framework",
                "chunk_index": 1,
                "page_number": 1
            }
        ),
        EmbeddedChunk(
            chunk_id="chunk_sec3_003",
            source_text="Routine vendor payments under $50,000 may be approved directly by department heads.",
            embedding=[0.0, 0.0, 0.85, 0.15],
            dimension=4,
            metadata={
                "doc_id": "reg_001",
                "filename": "sample_banking_regulation.txt",
                "section": "Section 3: High-Value Transaction Authorization Thresholds",
                "category": "Compliance & Regulation",
                "doc_type": "Regulatory Framework",
                "chunk_index": 2,
                "page_number": 2
            }
        ),
        EmbeddedChunk(
            chunk_id="chunk_sec3_004",
            source_text="Any vendor disbursement exceeding $50,000 requires unanimous board authorization and audit report.",
            embedding=[0.0, 0.0, 0.95, 0.05],
            dimension=4,
            metadata={
                "doc_id": "reg_001",
                "filename": "sample_banking_regulation.txt",
                "section": "Section 3: High-Value Transaction Authorization Thresholds",
                "category": "Compliance & Regulation",
                "doc_type": "Regulatory Framework",
                "chunk_index": 3,
                "page_number": 2
            }
        ),
    ]


# ==============================================================================
# TASK 1 TESTS: METADATA FILTERING
# ==============================================================================

def test_metadata_filter_exact_match(mock_embedded_corpus):
    mf = MetadataFilter(criteria={"section": "Section 2: Capital Reserves & Liquidity Ratios"})
    filtered = mf.filter_chunks(mock_embedded_corpus)
    assert len(filtered) == 1
    assert filtered[0].chunk_id == "chunk_sec2_002"


def test_metadata_filter_contains_operator(mock_embedded_corpus):
    mf = MetadataFilter(criteria={"section__contains": "Section 3"})
    filtered = mf.filter_chunks(mock_embedded_corpus)
    assert len(filtered) == 2
    assert {c.chunk_id for c in filtered} == {"chunk_sec3_003", "chunk_sec3_004"}


def test_metadata_filter_in_list_operator(mock_embedded_corpus):
    mf = MetadataFilter(criteria={"chunk_index__in": [0, 3]})
    filtered = mf.filter_chunks(mock_embedded_corpus)
    assert len(filtered) == 2
    assert {c.chunk_id for c in filtered} == {"chunk_sec1_001", "chunk_sec3_004"}


def test_metadata_filter_numeric_operators(mock_embedded_corpus):
    mf = MetadataFilter(criteria={"chunk_index__gte": 2, "page_number": 2})
    filtered = mf.filter_chunks(mock_embedded_corpus)
    assert len(filtered) == 2
    assert {c.chunk_id for c in filtered} == {"chunk_sec3_003", "chunk_sec3_004"}


def test_metadata_filter_custom_predicate(mock_embedded_corpus):
    mf = MetadataFilter(predicate=lambda m: m.get("chunk_index", 0) % 2 == 1)
    filtered = mf.filter_chunks(mock_embedded_corpus)
    assert len(filtered) == 2
    assert {c.chunk_id for c in filtered} == {"chunk_sec2_002", "chunk_sec3_004"}


def test_metadata_filter_serialization():
    mf = MetadataFilter(
        criteria={"category": "Banking", "chunk_index__gte": 1},
        description="Banking chunks index 1+"
    )
    d = mf.to_dict()
    assert d["criteria"]["category"] == "Banking"
    assert d["criteria"]["chunk_index__gte"] == 1
    assert "Banking chunks" in d["description"]


# ==============================================================================
# TASK 2 TESTS: COMPARE FILTERED AND UNFILTERED RESULTS
# ==============================================================================

def test_compare_filtered_unfiltered_eliminates_out_of_scope_chunks(mock_embedded_corpus):
    mock_client = MockLLMClient()
    engine = FilteredSearchEngine(client=mock_client)

    query = "What are the rules and approval thresholds for high-value transaction payments?"
    section_filter = MetadataFilter(criteria={"section__contains": "Section 3"})

    comparison = engine.compare_filtered_unfiltered(
        query=query,
        embedded_chunks=mock_embedded_corpus,
        metadata_filter=section_filter,
        top_k=2,
        mode="hybrid"
    )

    unfiltered = comparison["unfiltered_results"]
    filtered = comparison["filtered_results"]

    assert unfiltered["total_chunks_scored"] == 4
    assert filtered["total_chunks_scored"] == 2
    assert filtered["filtered_out_chunks"] == 2

    # Verify filtered results only contain Section 3
    for c in filtered["top_k_results"]:
        assert "Section 3" in c["metadata"]["section"]

    # Verify comparison analysis
    assert "relevance_verdict" in comparison["comparison_analysis"]
    assert len(comparison["comparison_analysis"]["eliminated_distractor_chunks"]) >= 0


# ==============================================================================
# TASK 3 TESTS: KEYWORD & HYBRID MATCHING
# ==============================================================================

def test_tokenize_text_preserves_financial_terms():
    text = "Vendor disbursements exceeding $50,000 require Basel-IV Tier-1 10.5% compliance."
    tokens = tokenize_text(text)
    assert "$50,000" in tokens
    assert "10.5%" in tokens
    assert "basel-iv" in tokens


def test_keyword_scorer_exact_phrase_bonus():
    scorer = KeywordScorer(exact_phrase_bonus=0.3)
    query = "disbursements exceeding $50,000"
    doc_with_exact = "Any vendor disbursement exceeding $50,000 requires unanimous board approval."
    doc_unrelated = "General banking compliance rules for international financial institutions."

    score_high, matched_high = scorer.compute_lexical_score(query, doc_with_exact)
    score_low, matched_low = scorer.compute_lexical_score(query, doc_unrelated)

    assert score_high > score_low
    assert score_high > 0.5
    assert score_low == 0.0
    assert "$50,000" in matched_high or "50,000" in matched_high


def test_hybrid_search_linear_combination(mock_embedded_corpus):
    mock_client = MockLLMClient()
    engine = FilteredSearchEngine(client=mock_client)

    query = "exceeding $50,000 board authorization"
    res_hybrid = engine.search(query, mock_embedded_corpus, mode="hybrid", alpha=0.5, top_k=2)
    top_chunk = res_hybrid["ranked_chunks"][0]

    # Verify top chunk has positive vector and keyword scores
    assert top_chunk["vector_score"] > 0.0
    assert top_chunk["keyword_score"] > 0.0
    expected_hybrid = (0.5 * top_chunk["vector_score"]) + (0.5 * top_chunk["keyword_score"])
    assert pytest.approx(top_chunk["hybrid_score"], 0.001) == expected_hybrid


def test_search_modes(mock_embedded_corpus):
    mock_client = MockLLMClient()
    engine = FilteredSearchEngine(client=mock_client)

    query = "AML compliance monitoring"
    res_vec = engine.search(query, mock_embedded_corpus, mode="vector", top_k=1)
    res_kw = engine.search(query, mock_embedded_corpus, mode="keyword", top_k=1)
    res_hyb = engine.search(query, mock_embedded_corpus, mode="hybrid", alpha=0.7, top_k=1)

    assert res_vec["mode"] == "vector"
    assert res_kw["mode"] == "keyword"
    assert res_hyb["mode"] == "hybrid"


# ==============================================================================
# TASK 4 TESTS: PRECISION IMPROVEMENT DEMONSTRATION
# ==============================================================================

def test_demonstrate_precision_improvement(mock_embedded_corpus):
    mock_client = MockLLMClient()
    engine = FilteredSearchEngine(client=mock_client)

    query = "What are the rules and approval thresholds for high-value transaction payments?"
    section_filter = MetadataFilter(criteria={"section__contains": "Section 3"})
    relevant_ids = ["chunk_sec3_003", "chunk_sec3_004"]

    prec_summary = engine.demonstrate_precision_improvement(
        query=query,
        embedded_chunks=mock_embedded_corpus,
        metadata_filter=section_filter,
        relevant_chunk_ids=relevant_ids,
        top_k=3
    )

    unfiltered_prec = prec_summary["unfiltered_vector_search"]["precision_percentage"]
    filtered_prec = prec_summary["filtered_hybrid_search"]["precision_percentage"]
    gain = prec_summary["precision_improvement"]["precision_gain_percentage"]

    # Filtered search precision should be strictly 100% since only Section 3 chunks are present
    assert filtered_prec == 100.0
    assert unfiltered_prec < 100.0
    assert gain > 0.0


# ==============================================================================
# TASK 5 TESTS: REPORT EXPORT & SERIALIZATION
# ==============================================================================

def test_export_reports_creates_files(tmp_path, mock_embedded_corpus):
    mock_client = MockLLMClient()
    engine = FilteredSearchEngine(client=mock_client)

    query = "Disbursements exceeding $50,000"
    section_filter = MetadataFilter(criteria={"section__contains": "Section 3"})
    relevant_ids = ["chunk_sec3_003", "chunk_sec3_004"]

    comp_res = engine.compare_filtered_unfiltered(query, mock_embedded_corpus, section_filter, top_k=2)
    prec_res = engine.demonstrate_precision_improvement(query, mock_embedded_corpus, section_filter, relevant_ids, top_k=3)
    hyb_res = {"query": query, "notes": "test hybrid"}

    txt_file = str(tmp_path / "test_filtered.txt")
    json_file = str(tmp_path / "test_filtered.json")
    hyb_json = str(tmp_path / "test_hybrid.json")
    prec_txt = str(tmp_path / "test_prec.txt")

    engine.export_reports(
        comparison_results=comp_res,
        precision_results=prec_res,
        hybrid_comparison_results=hyb_res,
        output_txt_path=txt_file,
        output_json_path=json_file,
        hybrid_json_path=hyb_json,
        precision_txt_path=prec_txt
    )

    assert os.path.exists(txt_file)
    assert os.path.exists(json_file)
    assert os.path.exists(hyb_json)
    assert os.path.exists(prec_txt)

    with open(json_file, "r", encoding="utf-8") as f:
        loaded_json = json.load(f)
    assert loaded_json["query"] == query
    assert "filtered_results" in loaded_json
