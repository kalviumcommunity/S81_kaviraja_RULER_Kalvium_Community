"""
Comprehensive Unit Test Suite for Embedding Fundamentals (Tasks 1 to 5).

Tests:
1. Embeddings are successfully generated
2. Multiple sample texts can be embedded
3. Every returned embedding is numeric
4. Every embedding has the same dimension
5. Vector dimension is greater than zero
6. Cosine similarity calculation accuracy & bounds
7. Similar texts score higher than unrelated texts
8. Empty or invalid input handled appropriately
"""

import math
import unittest
from typing import List
from src.llm_client import LLMClient
from src.embedding_demo import (
    cosine_similarity,
    verify_vector_dimensions,
    format_vector_preview,
    EmbeddingDemonstration,
)


class TestEmbeddingFundamentals(unittest.TestCase):

    def setUp(self):
        # Create a mock LLMClient instance for offline unit testing
        self.mock_client = LLMClient()
        self.mock_client.api_key = "mock"

    def test_1_embeddings_successfully_generated(self):
        """Verify embeddings are generated for a valid text input."""
        texts = ["The customer wants to check their bank account balance."]
        embeddings, usage = self.mock_client.generate_embeddings(texts)

        self.assertIsNotNone(embeddings)
        self.assertEqual(len(embeddings), 1)
        self.assertIsInstance(embeddings[0], list)

    def test_2_multiple_sample_texts_embedded(self):
        """Verify multiple sample texts return the corresponding number of embedding vectors."""
        texts = [
            "The customer wants to check their bank account balance.",
            "The user would like to know how much money is available in their account.",
            "A football match was played during heavy rain."
        ]
        embeddings, usage = self.mock_client.generate_embeddings(texts)

        self.assertIsNotNone(embeddings)
        self.assertEqual(len(embeddings), 3)

    def test_3_every_returned_embedding_is_numeric(self):
        """Verify that every single float inside the embedding vector is a valid number."""
        texts = ["Sample financial regulation text."]
        embeddings, _ = self.mock_client.generate_embeddings(texts)

        for vec in embeddings:
            for val in vec:
                self.assertIsInstance(val, (int, float))
                self.assertFalse(math.isnan(val))
                self.assertFalse(math.isinf(val))

    def test_4_every_embedding_has_same_dimension(self):
        """Verify programmatically that every returned embedding vector has identical length."""
        texts = [
            "Banking balance check request.",
            "Account balance query.",
            "Heavy rain in stadium."
        ]
        embeddings, _ = self.mock_client.generate_embeddings(texts)
        dim_report = verify_vector_dimensions(embeddings)

        self.assertTrue(dim_report["is_consistent"])
        self.assertEqual(dim_report["status"], "PASS")
        self.assertEqual(len(set(dim_report["lengths"])), 1)

    def test_5_vector_dimension_greater_than_zero(self):
        """Verify vector dimension is strictly greater than 0."""
        texts = ["Vector dimension assertion test."]
        embeddings, _ = self.mock_client.generate_embeddings(texts)
        dim_report = verify_vector_dimensions(embeddings)

        self.assertGreater(dim_report["detected_dimension"], 0)

    def test_6_cosine_similarity_calculation(self):
        """Verify cosine similarity function produces expected values (identity, orthogonal, opposite)."""
        vec_1 = [1.0, 0.0, 0.0]
        vec_2 = [1.0, 0.0, 0.0]
        vec_3 = [0.0, 1.0, 0.0]
        vec_4 = [-1.0, 0.0, 0.0]

        # Identical vectors -> Cosine similarity 1.0
        self.assertAlmostEqual(cosine_similarity(vec_1, vec_2), 1.0, places=5)
        # Orthogonal vectors -> Cosine similarity 0.0
        self.assertAlmostEqual(cosine_similarity(vec_1, vec_3), 0.0, places=5)
        # Opposite vectors -> Cosine similarity -1.0
        self.assertAlmostEqual(cosine_similarity(vec_1, vec_4), -1.0, places=5)

    def test_7_similar_texts_score_higher_than_unrelated(self):
        """Verify similar texts yield higher cosine similarity than unrelated texts."""
        # Custom mock vectors to test semantic similarity logic deterministically
        vec_a = [0.8, 0.6, 0.0, 0.0]  # Bank balance
        vec_b = [0.75, 0.65, 0.05, 0.0] # Account funds (high overlap with vec_a)
        vec_c = [0.0, 0.0, 0.9, 0.4]  # Football in rain (orthogonal)

        sim_ab = cosine_similarity(vec_a, vec_b)
        sim_ac = cosine_similarity(vec_a, vec_c)

        self.assertGreater(sim_ab, sim_ac)

    def test_8_empty_or_invalid_input_handled(self):
        """Verify empty or invalid inputs are handled gracefully without raising unhandled exceptions."""
        # Empty input list
        embeddings, usage = self.mock_client.generate_embeddings([])
        self.assertEqual(embeddings, [])
        self.assertEqual(usage["prompt_tokens"], 0)

        # Dimension check on empty list
        empty_dim = verify_vector_dimensions([])
        self.assertFalse(empty_dim["is_consistent"])

        # Cosine similarity on empty or mismatched vectors
        with self.assertRaises(ValueError):
            cosine_similarity([], [1.0, 2.0])

        with self.assertRaises(ValueError):
            cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])

    def test_9_embedding_demonstration_full_run(self):
        """Verify full EmbeddingDemonstration engine runs and returns expected PASS results."""
        demo = EmbeddingDemonstration(client=self.mock_client)
        # Provide explicit mock vectors so similar pair scores higher
        mock_vecs = [
            [0.8, 0.6, 0.1, 0.0] * 384,  # Text A
            [0.78, 0.62, 0.09, 0.01] * 384, # Text B (similar)
            [0.01, -0.02, 0.9, 0.4] * 384   # Text C (unrelated)
        ]
        
        # Override generate_embeddings return for mock demonstration test
        self.mock_client.generate_embeddings = lambda texts: (mock_vecs, {"prompt_tokens": 30, "total_tokens": 30})

        results = demo.run_demonstration()

        self.assertTrue(results["dimension_verification"]["all_dimensions_consistent"])
        self.assertEqual(results["dimension_verification"]["verification_status"], "PASS")
        self.assertTrue(results["similarity_comparison"]["comparison_check"]["is_passed"])
        self.assertIn("PASS", results["similarity_comparison"]["comparison_check"]["result_status"])


if __name__ == "__main__":
    unittest.main()
