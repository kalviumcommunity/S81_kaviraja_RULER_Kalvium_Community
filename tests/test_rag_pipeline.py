import unittest

from src.rag_pipeline import RAGPipeline, RetrievedSource, assemble, embed, generate


class FakeVectorDB:
    def search(self, query_embeddings, n_results):
        return {
            "documents": [["RAG uses retrieved context."]],
            "metadatas": [[{"source_id": "doc2.txt", "chunk_index": 0}]],
            "distances": [[0.1]],
        }


class TestRAGPipeline(unittest.TestCase):
    def test_stages_are_composable_and_sources_are_returned(self):
        pipeline = RAGPipeline(
            embedding_fn=lambda query: [len(query)],
            vector_db=FakeVectorDB(),
            generator_fn=lambda query, context: f"Answer grounded in {context}",
        )
        result = pipeline.run("What is RAG?")

        self.assertEqual(result.sources[0].metadata["source_id"], "doc2.txt")
        self.assertIn("doc2.txt", result.context)
        self.assertIn("RAG uses retrieved context", result.answer)

    def test_empty_query_is_rejected(self):
        with self.assertRaises(ValueError):
            embed("  ", lambda query: [1.0])

    def test_empty_generation_is_rejected(self):
        with self.assertRaises(RuntimeError):
            generate("query", "context", lambda query, context: "")

    def test_context_contains_source_labels(self):
        context = assemble("query", [RetrievedSource("text", {"source_id": "doc.txt", "chunk_index": 2}, 0.2)])
        self.assertIn("[Source 1: doc.txt, chunk 2]", context)


if __name__ == "__main__":
    unittest.main()