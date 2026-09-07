"""
Unit Tests for Chunk Re-Ranking for Precision (Tasks 1 to 4).
"""

import unittest
from types import SimpleNamespace
from src.reranker import ChunkReranker, CandidateChunk


class TestChunkReranker(unittest.TestCase):

    def setUp(self):
        self.reranker = ChunkReranker(llm_client=None)

    def test_task_1_candidate_pool_structure(self):
        """Task 1: Verify CandidateChunk dataclass and representation structure."""
        candidate = CandidateChunk(
            chunk_id="doc_1#chunk_001",
            text="Financial institutions must maintain a Tier 1 Capital Ratio of at least 10.5%.",
            metadata={"doc_id": "doc_1", "section": "Capital Requirements"},
            initial_rank=1,
            vector_distance=0.15,
            vector_similarity=0.85
        )
        c_dict = candidate.to_dict()
        self.assertEqual(c_dict["chunk_id"], "doc_1#chunk_001")
        self.assertEqual(c_dict["initial_rank"], 1)
        self.assertEqual(c_dict["vector_similarity"], 0.85)
        self.assertIn("rank_shift_label", c_dict)

    def test_task_2_reranking_scoring_and_ordering(self):
        """Task 2: Verify candidates are re-ordered by relevance score in descending order."""
        query = "What is the minimum Tier 1 Capital Ratio for banks?"
        
        candidates = [
            CandidateChunk(
                chunk_id="chunk_broad_ai",
                text="Artificial intelligence models must be trained on high quality clean datasets.",
                metadata={"section": "AI Models"},
                initial_rank=1,
                vector_distance=0.20,
                vector_similarity=0.80
            ),
            CandidateChunk(
                chunk_id="chunk_exact_tier1",
                text="Financial institutions must maintain a Tier 1 Capital Ratio of at least 10.5% at all times.",
                metadata={"section": "Capital Requirements"},
                initial_rank=2,
                vector_distance=0.25,
                vector_similarity=0.75
            ),
            CandidateChunk(
                chunk_id="chunk_general_banking",
                text="All licensed entities must implement strict risk controls and audit logs.",
                metadata={"section": "Overview"},
                initial_rank=3,
                vector_distance=0.30,
                vector_similarity=0.70
            ),
        ]

        reranked_all, top_k = self.reranker.rerank(query, candidates, top_k=2, method="custom")

        # The exact tier1 chunk must be promoted to rank 1
        self.assertEqual(reranked_all[0].chunk_id, "chunk_exact_tier1")
        self.assertEqual(reranked_all[0].final_rank, 1)
        self.assertEqual(reranked_all[0].rank_change, 1)  # was rank 2, now rank 1 (+1)
        self.assertTrue(reranked_all[0].is_selected)

        # The broad AI chunk should be demoted
        self.assertEqual(reranked_all[1].final_rank, 2)
        self.assertTrue(reranked_all[0].rerank_score >= reranked_all[1].rerank_score)
        self.assertEqual(len(top_k), 2)

    def test_task_3_demonstrate_improved_top_results(self):
        """Task 3: Verify that re-ranking promotes high-precision ground truth chunk to top."""
        query = "How quickly must a data breach be reported?"

        candidates = [
            CandidateChunk(
                chunk_id="chunk_broad_sec",
                text="Customer financial data must be encrypted at rest using AES-256 and in transit using TLS 1.3.",
                metadata={"section": "Security"},
                initial_rank=1,
                vector_distance=0.18,
                vector_similarity=0.82
            ),
            CandidateChunk(
                chunk_id="chunk_exact_breach",
                text="Any data breach must be reported to the regulatory oversight committee within 24 hours of initial detection.",
                metadata={"section": "Breach Reporting"},
                initial_rank=2,
                vector_distance=0.22,
                vector_similarity=0.78
            ),
        ]

        reranked, top_selected = self.reranker.rerank(query, candidates, top_k=1, method="custom")

        self.assertEqual(top_selected[0].chunk_id, "chunk_exact_breach")
        self.assertGreater(top_selected[0].rerank_score, reranked[1].rerank_score)
        self.assertEqual(top_selected[0].final_rank, 1)

    def test_task_4_compare_before_and_after_reporting(self):
        """Task 4: Verify before-and-after comparison metrics and table generation."""
        query = "Explain machine learning adaptability"
        candidates = [
            CandidateChunk(
                chunk_id="c1",
                text="Machine learning enables systems to automatically learn from and adapt to new input data.",
                metadata={"filename": "doc1.txt"},
                initial_rank=1,
                vector_distance=0.1,
                vector_similarity=0.9
            ),
            CandidateChunk(
                chunk_id="c2",
                text="Database tables should be normalized.",
                metadata={"filename": "doc2.txt"},
                initial_rank=2,
                vector_distance=0.4,
                vector_similarity=0.6
            ),
        ]

        reranked, _ = self.reranker.rerank(query, candidates, top_k=1, method="custom")
        comparison = self.reranker.compare_rankings(query, candidates, reranked, top_k=1)

        self.assertEqual(comparison["query"], query)
        self.assertEqual(comparison["initial_candidate_count"], 2)
        self.assertEqual(comparison["final_top_k_count"], 1)
        self.assertIn("metrics", comparison)
        self.assertIn("top_k_selected_chunks", comparison)
        self.assertIn("all_candidates_comparison", comparison)

        # Verify markdown table formatting works without error
        md_table = self.reranker.format_comparison_table_markdown(comparison)
        self.assertIn("Final Rank", md_table)
        self.assertIn("Initial Rank", md_table)
        self.assertIn("Vector Sim", md_table)
        self.assertIn("Re-Rank Score", md_table)

    def test_edge_cases(self):
        """Verify edge cases like empty candidates and top_k larger than candidate pool."""
        # Empty candidate list
        reranked, top_k = self.reranker.rerank("test query", [], top_k=3)
        self.assertEqual(reranked, [])
        self.assertEqual(top_k, [])

        # top_k larger than available candidates
        single_cand = [
            CandidateChunk(
                chunk_id="c1",
                text="Some text",
                metadata={},
                initial_rank=1,
                vector_distance=0.1,
                vector_similarity=0.9
            )
        ]
        reranked_single, top_single = self.reranker.rerank("query", single_cand, top_k=5)
        self.assertEqual(len(top_single), 1)
        self.assertTrue(top_single[0].is_selected)


if __name__ == "__main__":
    unittest.main()
