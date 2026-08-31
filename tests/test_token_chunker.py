"""
Comprehensive Unit Test Suite for TokenAwareChunker (Tasks 1 to 5 & QA Audit Checklist).

Tests:
1. Basic token chunking
2. Token count accuracy
3. Zero overlap
4. Configured overlap
5. Boundary context preservation
6. Empty text
7. Short text
8. Exact chunk-size text
9. Multi-chunk text
10. Invalid overlap
11. Invalid chunk size
12. Metadata preservation
13. Integration with existing document pipeline
"""

import unittest
import tiktoken
from src.token_chunker import TokenAwareChunker, TokenChunk
from src.chunk_metadata import trace_chunk_to_source, verify_metadata_consistency


class TestTokenAwareChunker(unittest.TestCase):

    def setUp(self):
        self.chunk_size = 50
        self.overlap = 10
        self.chunker = TokenAwareChunker(chunk_size_tokens=self.chunk_size, chunk_overlap_tokens=self.overlap)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def test_1_basic_token_chunking(self):
        """Verify basic chunking splits text into valid TokenChunk objects."""
        text = "This is a basic test sentence to verify token chunking logic works as expected."
        chunks = self.chunker.chunk_text(text, doc_id="doc_basic")
        self.assertGreater(len(chunks), 0)
        self.assertIsInstance(chunks[0], TokenChunk)

    def test_2_token_count_accuracy(self):
        """Verify token count is calculated accurately using tiktoken for every chunk."""
        long_text = "Word " * 200
        chunks = self.chunker.chunk_text(long_text, doc_id="doc_tokens")

        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, self.chunk_size)
            actual_tok_count = len(self.tokenizer.encode(chunk.text))
            self.assertEqual(actual_tok_count, chunk.token_count)

    def test_3_zero_overlap(self):
        """Verify chunking when overlap = 0."""
        text = "Sample sentence " * 30
        chunker_zero = TokenAwareChunker(chunk_size_tokens=30, chunk_overlap_tokens=0)
        chunks = chunker_zero.chunk_text(text, doc_id="doc_zero_overlap")

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertEqual(chunk.overlap_tokens, 0)

        toks_c1 = self.tokenizer.encode(chunks[0].text)
        toks_c2 = self.tokenizer.encode(chunks[1].text)
        self.assertEqual(toks_c1[-1], self.tokenizer.encode(chunks[0].text)[-1])
        # Ensure no overlap repeated
        self.assertNotEqual(toks_c1[-5:], toks_c2[:5])

    def test_4_configured_overlap(self):
        """Verify adjacent chunks repeat exactly Y trailing tokens from preceding chunk."""
        text = "Detailed paragraph for testing configured token overlap in RAG ingestion pipeline. " * 6
        chunker = TokenAwareChunker(chunk_size_tokens=30, chunk_overlap_tokens=10)
        chunks = chunker.chunk_text(text, doc_id="doc_overlap")

        self.assertGreaterEqual(len(chunks), 2)
        toks_c1 = self.tokenizer.encode(chunks[0].text)
        toks_c2 = self.tokenizer.encode(chunks[1].text)

        overlap_from_c1 = toks_c1[-10:]
        overlap_in_c2 = toks_c2[:10]

        self.assertEqual(overlap_from_c1, overlap_in_c2)
        self.assertEqual(chunks[1].overlap_tokens, 10)

    def test_5_boundary_context_preservation(self):
        """Verify demonstration shows boundary context intact with overlap vs severed without."""
        demo_results = self.chunker.demonstrate_boundary_context()
        self.assertIn("without_overlap", demo_results)
        self.assertIn("with_overlap", demo_results)
        self.assertIn("preserved_boundary_context", demo_results["with_overlap"])
        self.assertTrue(len(demo_results["with_overlap"]["overlapping_repeated_text"]) > 0)

    def test_6_empty_text(self):
        """Verify handling of empty string input."""
        self.assertEqual(self.chunker.chunk_text(""), [])
        self.assertEqual(self.chunker.chunk_text("   \n\t "), [])

    def test_7_short_text(self):
        """Verify text smaller than chunk_size produces a single chunk with zero overlap."""
        short_text = "Short sentence."
        chunks = self.chunker.chunk_text(short_text, doc_id="doc_short")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].overlap_tokens, 0)
        self.assertEqual(chunks[0].chunk_index, 0)
        self.assertEqual(chunks[0].total_chunks, 1)

    def test_8_exact_chunk_size_text(self):
        """Verify text equal to exact chunk size produces a single chunk."""
        exact_text = ("test " * (self.chunk_size - 1)) + "test"
        self.assertEqual(len(self.tokenizer.encode(exact_text)), self.chunk_size)
        chunks = self.chunker.chunk_text(exact_text, doc_id="doc_exact")

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].token_count, self.chunk_size)
        self.assertEqual(chunks[0].overlap_tokens, 0)



    def test_9_multi_chunk_text(self):
        """Verify document spanning multiple chunks generates correct chunk_index and total_chunks."""
        multi_text = "Multi chunk text paragraph testing long document splitting behavior. " * 20
        chunks = self.chunker.chunk_text(multi_text, doc_id="doc_multi")

        self.assertGreater(len(chunks), 2)
        total = len(chunks)
        for idx, chunk in enumerate(chunks):
            self.assertEqual(chunk.chunk_index, idx)
            self.assertEqual(chunk.total_chunks, total)

    def test_10_invalid_overlap(self):
        """Verify error raised when overlap >= chunk_size or negative."""
        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=50)

        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=60)

        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=50, chunk_overlap_tokens=-5)

    def test_11_invalid_chunk_size(self):
        """Verify error raised when chunk_size <= 0."""
        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=0, chunk_overlap_tokens=0)

        with self.assertRaises(ValueError):
            TokenAwareChunker(chunk_size_tokens=-10, chunk_overlap_tokens=0)

    def test_12_metadata_preservation(self):
        """Verify metadata schema is fully preserved across all generated chunks."""
        text = "Testing metadata preservation across generated chunks in RAG pipeline." * 5
        chunks = self.chunker.chunk_text(
            text=text,
            doc_id="DOC_META_001",
            filename="meta_test.txt",
            source_path="data/meta_test.txt",
            section="Executive Summary",
            page_number=2
        )

        for chunk in chunks:
            d = chunk.to_dict()
            meta = d["metadata"]
            self.assertEqual(meta["doc_id"], "DOC_META_001")
            self.assertEqual(meta["filename"], "meta_test.txt")
            self.assertEqual(meta["source_path"], "data/meta_test.txt")
            self.assertEqual(meta["section"], "Executive Summary")
            self.assertEqual(meta["page_number"], 2)
            self.assertIn("start_char", meta)
            self.assertIn("end_char", meta)

    def test_13_integration_with_existing_document_pipeline(self):
        """Verify TokenChunk converts to Chunk and verifies with trace_chunk_to_source."""
        source_text = "Standard retail banking policies mandate that routine vendor payments under $50,000 may be approved directly."
        chunks = self.chunker.chunk_text(
            text=source_text,
            doc_id="DOC_INTEG_001",
            filename="integ_test.txt",
            source_path="data/integ_test.txt"
        )
        self.assertGreater(len(chunks), 0)

        token_chunk = chunks[0]
        std_chunk = token_chunk.to_chunk()

        # Check metadata consistency report
        consistency_report = verify_metadata_consistency([std_chunk])
        self.assertTrue(consistency_report["is_fully_consistent"])

        # Trace chunk back to source document
        corpus_docs = {"DOC_INTEG_001": source_text}
        trace_res = trace_chunk_to_source(std_chunk, corpus_docs)
        self.assertTrue(trace_res["is_traced_successfully"])


if __name__ == "__main__":
    unittest.main()
