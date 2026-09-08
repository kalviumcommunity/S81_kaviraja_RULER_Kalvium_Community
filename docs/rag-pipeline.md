# Query-to-Answer RAG Flow

The end-to-end pipeline is implemented in `src/rag_pipeline.py` and exercised by `scripts/run_rag_pipeline.py`.

```text
User query
   |
   v
embed(query) -> query embedding vector
   |
   v
retrieve(vector) -> top-k document chunks from ChromaDB
   |
   v
assemble(query, chunks) -> labelled grounded context
   |
   v
generate(query, context) -> answer from the LLM
   |
   v
RAG response -> answer + retrieved source IDs, chunk indexes, and distances
```

Each stage is a separate function and receives its external dependency through a callable or client. That makes the embedding, retrieval, context assembly, and generation behavior independently testable. The runner uses deterministic local embeddings and generation when `OPENAI_API_KEY` is absent, so the complete flow can be verified offline. When the key is configured, query embedding and answer generation use the existing OpenAI-compatible `LLMClient`.

## Sample output

The sample query is `What is Retrieval-Augmented Generation and how does it work?`.

```text
Answer:
RAG retrieves relevant facts from an external knowledge base and supplies them to a language model as context. It converts documents into embeddings, stores them in a vector database, and retrieves the most relevant documents for a user query.

Retrieved sources:
- doc2.txt (chunk 0)
- doc1.txt (chunk 0)
```

The full machine-readable result, including similarity distances, is written to `outputs/rag_pipeline_sample.json`.