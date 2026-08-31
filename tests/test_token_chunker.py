"""
Unit tests for TokenAwareChunker (Tasks 1 to 4).
"""

import unittest
import tiktoken
from src.token_chunker import TokenAwareChunker, TokenChunk


class TestTokenAwareChunker(unittest.TestCase):

    def setUp(self):
        self.chunker = TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=10)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def test_task_1_token_sizing(self):
        """Task 1: Verify chunk size is measured strictly in tokens, not characters."""
        long_text = "Word " * 200  # 200 words
        chunks = self.chunker.chunk_text(long_text, doc_id="test_doc")

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 50)
            # Verify actual tiktoken token count matches metadata token_count
            actual_tokens = len(self.tokenizer.encode(chunk.text))
            self.assertEqual(actual_tokens, chunk.token_count)

    def test_task_2_controlled_overlap(self):
        """Task 2: Verify controlled overlap between adjacent chunks."""
        text = "This is a detailed paragraph meant to test controlled token overlap between adjacent chunks in a RAG pipeline. " * 5
        chunker = TokenAwareChunker(chunk_size_tokens=30, chunk_overlap_tokens=10)
        chunks = chunker.chunk_text(text, doc_id="overlap_doc")

        self.assertGreaterEqual(len(chunks), 2)

        # Verify Chunk 2 repeats the last 10 tokens of Chunk 1
        toks_c1 = self.tokenizer.encode(chunks[0].text)
        toks_c2 = self.tokenizer.encode(chunks[1].text)

        overlap_from_c1 = toks_c1[-10:]
        overlap_in_c2 = toks_c2[:10]

        self.assertEqual(overlap_from_c1, overlap_in_c2)
        self.assertEqual(chunks[1].overlap_tokens, 10)

    def test_task_3_boundary_context_demonstration(self):
        """Task 3: Demonstrate boundary context preservation with vs without overlap."""
        demo_results = self.chunker.demonstrate_boundary_context()

        self.assertIn("without_overlap", demo_results)
        self.assertIn("with_overlap", demo_results)
        self.assertIn("preserved_boundary_context", demo_results["with_overlap"])
        self.assertIn("boundary_issue", demo_results["without_overlap"])
        self.assertTrue(len(demo_results["with_overlap"]["overlapping_repeated_text"]) > 0)

    def test_task_4_settings_justification(self):
        """Task 4: Verify technical settings justification report structure."""
        justification = self.chunker.justify_settings()

        self.assertEqual(justification["chosen_chunk_size_tokens"], 50)
        self.assertEqual(justification["chosen_overlap_tokens"], 10)
        self.assertIn("task_1_token_sizing", justification["justifications"])
        self.assertIn("task_2_controlled_overlap_rationale", justification["justifications"])
        self.assertIn("cost_vs_context_tradeoff", justification["justifications"])

    def test_empty_and_short_text(self):
        """Verify behavior on empty text and text smaller than chunk_size."""
        # Empty text
        self.assertEqual(self.chunker.chunk_text(""), [])

        # Short text
        short_text = "Short text under chunk size limit."
        chunks = self.chunker.chunk_text(short_text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].overlap_tokens, 0)
        self.assertEqual(chunks[0].chunk_index, 0)
        self.assertEqual(chunks[0].total_chunks, 1)

    def test_invalid_parameters(self):
        """Verify validation errors for invalid token size or overlap settings."""
        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=0, chunk_overlap_tokens=0)

        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=-5)

        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=50)

        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=60)


if __name__ == "__main__":
    unittest.main()
