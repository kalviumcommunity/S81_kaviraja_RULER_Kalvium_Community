"""
Unit and Integration Tests for Similarity Metric Computation and Query-Chunk Ranking.

Validates:
1. Cosine similarity, dot product, and Euclidean distance computation on known vectors.
2. Error handling for vector dimension mismatch, zero vectors, and empty inputs.
3. Ranking accuracy for query vs. chunk embeddings (most similar vs. least similar).
4. Technical metric justification output.
5. File reporting (TXT and JSON) for similarity ranking outputs.
"""

import os
import json
import pytest
from typing import List

from src.similarity_ranker import (
    SimilarityRanker,
    RankedChunk,
    dot_product,
    euclidean_distance,
)
from src.embedding_demo import cosine_similarity
from src.chunk_embedding_pipeline import EmbeddedChunk


class MockLLMClient:
    """Mock LLMClient for testing SimilarityRanker without network API calls."""

    class Logger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    def __init__(self):
        self.logger = self.Logger()
        self.base_url = "https://mock.api/v1"
        self.embedding_model = "mock-embedding-model"

    def generate_embeddings(self, texts: List[str], model=None):
        # Deterministic mock vectors based on text content
        embeddings = []
        for t in texts:
            if "vendor" in t.lower() or "payment" in t.lower() or "high-value" in t.lower():
                # Query/chunk about payment thresholds
                embeddings.append([0.8, 0.6, 0.0, 0.0])
            elif "liquidity" in t.lower() or "basel" in t.lower():
                # Finance ratios
                embeddings.append([0.0, 0.0, 0.9, 0.4])
            else:
                # General compliance
                embeddings.append([0.1, 0.2, 0.3, 0.4])
        usage = {"prompt_tokens": 10, "total_tokens": 10}
        return embeddings, usage


def test_cosine_similarity_identical_vectors():
    vec_a = [1.0, 2.0, 3.0]
    score = cosine_similarity(vec_a, vec_a)
    assert pytest.approx(score, 0.0001) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [0.0, 1.0, 0.0]
    score = cosine_similarity(vec_a, vec_b)
    assert pytest.approx(score, 0.0001) == 0.0


def test_cosine_similarity_opposite_vectors():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [-1.0, 0.0, 0.0]
    score = cosine_similarity(vec_a, vec_b)
    assert pytest.approx(score, 0.0001) == -1.0


def test_dot_product_and_euclidean():
    vec_a = [3.0, 4.0]
    vec_b = [1.0, 2.0]

    dot_val = dot_product(vec_a, vec_b)
    assert dot_val == (3.0 * 1.0 + 4.0 * 2.0)  # 11.0

    euc_val = euclidean_distance(vec_a, vec_b)
    # sqrt((3-1)^2 + (4-2)^2) = sqrt(4 + 4) = sqrt(8) ~ 2.8284
    assert pytest.approx(euc_val, 0.0001) == 2.828427


def test_input_validation_errors():
    with pytest.raises(ValueError, match="cannot be empty"):
        cosine_similarity([], [1.0, 2.0])

    with pytest.raises(ValueError, match="do not match"):
        cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="Unsupported similarity metric"):
        ranker = SimilarityRanker(client=MockLLMClient())
        ranker.compute_similarity([1.0], [1.0], metric="invalid_metric")


def test_rank_chunks_ordering():
    client = MockLLMClient()
    ranker = SimilarityRanker(client=client, metric="cosine")

    # High similarity chunk
    chunk_high = EmbeddedChunk(
        chunk_id="c_high",
        source_text="Vendor payment approvals under $50,000.",
        embedding=[0.8, 0.6, 0.0, 0.0],
        dimension=4,
        metadata={"filename": "test.txt", "section": "Payments"}
    )
    # Medium similarity chunk
    chunk_med = EmbeddedChunk(
        chunk_id="c_med",
        source_text="General compliance monitoring policies.",
        embedding=[0.1, 0.2, 0.3, 0.4],
        dimension=4,
        metadata={"filename": "test.txt", "section": "Compliance"}
    )
    # Low similarity chunk
    chunk_low = EmbeddedChunk(
        chunk_id="c_low",
        source_text="Basel IV capital reserves and liquidity coverage.",
        embedding=[0.0, 0.0, 0.9, 0.4],
        dimension=4,
        metadata={"filename": "test.txt", "section": "Liquidity"}
    )

    query = "What are the vendor payment approval rules?"
    res = ranker.rank_chunks(
        query=query,
        embedded_chunks=[chunk_low, chunk_high, chunk_med],
        top_k=1
    )

    assert res["total_chunks_compared"] == 3
    ranked_chunks = res["ranked_chunks"]

    # Verify descending score order
    assert ranked_chunks[0]["chunk_id"] == "c_high"
    assert ranked_chunks[1]["chunk_id"] == "c_med"
    assert ranked_chunks[2]["chunk_id"] == "c_low"

    # Verify top and bottom selection
    assert res["most_similar"][0]["chunk_id"] == "c_high"
    assert res["least_similar"][0]["chunk_id"] == "c_low"


def test_justify_metric():
    ranker = SimilarityRanker(client=MockLLMClient(), metric="cosine")
    justification = ranker.justify_metric("cosine")

    assert justification["metric_name"] == "Cosine Similarity"
    assert "Directional Semantic Alignment" in justification["key_reasons"][0]
    assert "Length Invariance" in justification["key_reasons"][1]
    assert "verdict" in justification


def test_generate_ranking_reports(tmp_path):
    client = MockLLMClient()
    ranker = SimilarityRanker(client=client, metric="cosine")

    chunk = EmbeddedChunk(
        chunk_id="c_1",
        source_text="Vendor payment rules.",
        embedding=[1.0, 0.0, 0.0, 0.0],
        dimension=4,
        metadata={"filename": "test.txt"}
    )

    ranking_results = ranker.rank_chunks("vendor payments", [chunk])

    txt_file = os.path.join(tmp_path, "ranking.txt")
    json_file = os.path.join(tmp_path, "ranking.json")

    ranker.generate_ranking_reports(ranking_results, output_txt_path=txt_file, output_json_path=json_file)

    assert os.path.exists(txt_file)
    assert os.path.exists(json_file)

    with open(txt_file, "r", encoding="utf-8") as f:
        txt_content = f.read()
    assert "Vector Similarity Ranking Report" in txt_content
    assert "Most Similar Chunks" in txt_content

    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    assert json_data["query"] == "vendor payments"
    assert len(json_data["ranked_chunks"]) == 1


def test_empty_chunks_list():
    ranker = SimilarityRanker(client=MockLLMClient())
    res = ranker.rank_chunks("test query", [])
    assert res["total_chunks_compared"] == 0
    assert res["ranked_chunks"] == []
    assert res["most_similar"] == []
    assert res["least_similar"] == []
