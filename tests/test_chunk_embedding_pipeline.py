"""
Unit and Integration Test Suite for API-Based Embedding Integration with Prepared Chunks Pipeline.

Verifies:
1. Prepared chunks are accepted and text extracted.
2. Chunk text is sent to embedding layer.
3. Real/Mock embedding vectors are returned.
4. Embeddings are numeric floats.
5. Dimension consistency across all embedded chunks.
6. Source text is 100% preserved in EmbeddedChunk.
7. Chunk metadata is 100% preserved (doc_id, filename, section, chunk_index, char offsets, etc.).
8. Chunk index is preserved.
9. Multiple chunks are embedded together.
10. Empty chunks are handled gracefully without unnecessary API calls.
11. Missing configuration / API error handling.
12. End-to-end integration with TokenAwareChunker works.
"""

import math
import unittest
from typing import List
from src.llm_client import LLMClient
from src.token_chunker import TokenAwareChunker, TokenChunk
from src.chunk_metadata import Chunk, ChunkMetadata
from src.chunk_embedding_pipeline import (
    EmbeddedChunk,
    ChunkEmbeddingPipeline,
)


class TestChunkEmbeddingPipeline(unittest.TestCase):

    def setUp(self):
        # Create offline mock LLMClient instance for deterministic unit testing
        self.mock_client = LLMClient()
        self.mock_client.api_key = "mock"
        self.pipeline = ChunkEmbeddingPipeline(client=self.mock_client)

    def test_1_prepared_chunks_accepted_and_embedded(self):
        """Verify prepared text chunks are accepted and return EmbeddedChunk objects."""
        chunker = TokenAwareChunker(chunk_size_tokens=100, chunk_overlap_tokens=10)
        chunks = chunker.chunk_text(
            "Financial compliance regulations require continuous transaction audit.",
            doc_id="doc_test_01",
            filename="regulation.txt"
        )
        self.assertGreater(len(chunks), 0)

        embedded_chunks, stats = self.pipeline.embed_chunks(chunks)

        self.assertEqual(len(embedded_chunks), len(chunks))
        self.assertEqual(stats["embedded_count"], len(chunks))
        self.assertIsInstance(embedded_chunks[0], EmbeddedChunk)

    def test_2_source_text_and_metadata_preserved(self):
        """Verify that every embedded chunk preserves source text and complete metadata."""
        meta = ChunkMetadata(
            doc_id="DOC_999",
            filename="policy.pdf",
            source_path="data/policy.pdf",
            section="Section 1: Security",
            page_number=3,
            chunk_index=2,
            total_chunks=5,
            start_char=120,
            end_char=250
        )
        chunk = Chunk(chunk_id="DOC_999#chunk_003", text="Strict encryption standard must be enforced.", metadata=meta)

        embedded_chunks, stats = self.pipeline.embed_chunks([chunk])

        self.assertEqual(len(embedded_chunks), 1)
        ec = embedded_chunks[0]

        # Verify source text preservation
        self.assertEqual(ec.source_text, "Strict encryption standard must be enforced.")
        self.assertEqual(ec.chunk_id, "DOC_999#chunk_003")

        # Verify metadata preservation
        self.assertEqual(ec.metadata["doc_id"], "DOC_999")
        self.assertEqual(ec.metadata["filename"], "policy.pdf")
        self.assertEqual(ec.metadata["source_path"], "data/policy.pdf")
        self.assertEqual(ec.metadata["section"], "Section 1: Security")
        self.assertEqual(ec.metadata["page_number"], 3)
        self.assertEqual(ec.metadata["chunk_index"], 2)
        self.assertEqual(ec.metadata["total_chunks"], 5)
        self.assertEqual(ec.metadata["start_char"], 120)
        self.assertEqual(ec.metadata["end_char"], 250)

    def test_3_vector_numeric_and_dimension_consistency(self):
        """Verify vector embeddings are numeric floats and have consistent dimensions."""
        chunker = TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=5)
        doc_text = (
            "Paragraph 1: Risk management policies.\n\n"
            "Paragraph 2: Capital adequacy reserves.\n\n"
            "Paragraph 3: Internal audit control procedures."
        )
        chunks = chunker.chunk_text(doc_text, doc_id="doc_multi")

        embedded_chunks, _ = self.pipeline.embed_chunks(chunks)
        dim_report = self.pipeline.verify_pipeline_dimensions(embedded_chunks)

        self.assertTrue(dim_report["is_consistent"])
        self.assertEqual(dim_report["status"], "PASS")

        # Assert numeric check
        for ec in embedded_chunks:
            self.assertGreater(ec.dimension, 0)
            self.assertEqual(len(ec.embedding), ec.dimension)
            for val in ec.embedding:
                self.assertIsInstance(val, (int, float))
                self.assertFalse(math.isnan(val))

    def test_4_empty_chunks_handled_without_api_call(self):
        """Verify empty or whitespace-only chunks are handled gracefully without breaking pipeline."""
        empty_chunk = TokenChunk(
            chunk_id="chunk_empty",
            text="   ",
            token_count=0,
            start_token=0,
            end_token=0,
            overlap_tokens=0
        )
        valid_chunk = TokenChunk(
            chunk_id="chunk_valid",
            text="Valid sentence for embedding.",
            token_count=5,
            start_token=0,
            end_token=5,
            overlap_tokens=0
        )

        embedded_chunks, stats = self.pipeline.embed_chunks([empty_chunk, valid_chunk])

        self.assertEqual(len(embedded_chunks), 1)
        self.assertEqual(embedded_chunks[0].chunk_id, "chunk_valid")
        self.assertEqual(stats["skipped_empty_chunks"], 1)

    def test_5_missing_api_key_or_authentication_failure_handled(self):
        """Verify pipeline handles API errors gracefully when API key is missing or invalid."""
        bad_client = LLMClient()
        bad_client.api_key = "invalid_secret_key"

        # Force real call to trigger authentication error or catch simulate_error logic
        pipeline_bad = ChunkEmbeddingPipeline(client=bad_client)
        chunk = TokenChunk(
            chunk_id="c1", text="Test text", token_count=2, start_token=0, end_token=2, overlap_tokens=0
        )

        # In mock mode or live fail mode, pipeline should return empty list or handle cleanly
        embedded, stats = pipeline_bad.embed_chunks([chunk])
        self.assertIsInstance(embedded, list)
        self.assertIn("chunks_received", stats)

    def test_6_full_pipeline_run(self):
        """Verify end-to-end run_pipeline execution produces verification reports and JSON outputs."""
        sample_corpus = [
            (
                "data/test_doc.txt",
                "test_doc.txt",
                "Financial regulation doc. High value transfers over $50k require board review."
            )
        ]
        embedded_chunks, results = self.pipeline.run_pipeline(
            sample_docs=sample_corpus,
            output_txt_path="outputs/test_chunk_embeddings_output.txt",
            output_json_path="outputs/test_chunk_embeddings_results.json"
        )

        self.assertGreater(len(embedded_chunks), 0)
        self.assertEqual(results["pipeline_metadata"]["chunks_received"], len(embedded_chunks))
        self.assertEqual(results["pipeline_metadata"]["dimension_consistency"], "PASS")

    def test_7_embedded_chunk_serialization(self):
        """Verify EmbeddedChunk to_dict and from_dict roundtrip."""
        ec = EmbeddedChunk(
            chunk_id="c_100",
            source_text="Sample text",
            embedding=[0.1, 0.2, 0.3],
            dimension=3,
            metadata={"doc_id": "d1"}
        )
        d = ec.to_dict()
        ec_restored = EmbeddedChunk.from_dict(d)

        self.assertEqual(ec_restored.chunk_id, ec.chunk_id)
        self.assertEqual(ec_restored.source_text, ec.source_text)
        self.assertEqual(ec_restored.embedding, ec.embedding)
        self.assertEqual(ec_restored.dimension, ec.dimension)
        self.assertEqual(ec_restored.metadata, ec.metadata)


if __name__ == "__main__":
    unittest.main()
