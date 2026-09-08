"""Run the complete query-to-answer RAG flow on the sample documents."""

import hashlib
import json
import os
import sys
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from llm_client import LLMClient
from vector_db import VectorDBClient
from rag_pipeline import RAGPipeline


EMBEDDING_DIMENSIONS = 256


def offline_embedding(text: str) -> List[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for word in text.lower().split():
        index = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16) % EMBEDDING_DIMENSIONS
        vector[index] += 1.0
    magnitude = sum(value * value for value in vector) ** 0.5 or 1.0
    return [value / magnitude for value in vector]


def load_sample_documents() -> List[dict]:
    chunks = []
    for filename in ("doc1.txt", "doc2.txt"):
        path = os.path.join("data", filename)
        with open(path, "r", encoding="utf-8") as document_file:
            chunks.append({
                "id": filename,
                "text": document_file.read().strip(),
                "metadata": {"source_id": filename, "chunk_index": 0},
            })
    return chunks


def build_demo_store(vector_db: VectorDBClient, documents: List[dict], embedding_fn) -> None:
    if vector_db.get_collection_count() > 0:
        return
    vector_db.add_records(
        ids=[document["id"] for document in documents],
        embeddings=[embedding_fn(document["text"]) for document in documents],
        documents=[document["text"] for document in documents],
        metadatas=[document["metadata"] for document in documents],
    )


def offline_generator(query: str, context: str) -> str:
    return (
        "RAG retrieves relevant facts from an external knowledge base and supplies them "
        "to a language model as context. It converts documents into embeddings, stores "
        "them in a vector database, and retrieves the most relevant documents for a "
        "user query."
    )


def live_generator(llm_client: LLMClient, query: str, context: str) -> str:
    system_message = (
        "Answer the question using only the supplied context. Be concise and cite "
        "the source labels included in the context. If the context does not answer "
        "the question, say so."
    )
    answer, _ = llm_client.create_chat_completion(
        system_message=system_message,
        user_message=context,
        temperature=0.2,
    )
    if not answer:
        raise RuntimeError("the LLM did not return an answer")
    return answer


def main() -> None:
    use_live_api = bool(os.getenv("OPENAI_API_KEY"))
    documents = load_sample_documents()
    llm_client = LLMClient(log_file=os.path.join("outputs", "rag_pipeline_log.txt")) if use_live_api else None
    embedding_fn = offline_embedding if not use_live_api else lambda text: llm_client.create_embeddings([text])[0][0]
    collection_name = "rag_pipeline_demo_live" if use_live_api else "rag_pipeline_demo"
    vector_db = VectorDBClient(collection_name=collection_name)
    build_demo_store(vector_db, documents, embedding_fn)

    pipeline = RAGPipeline(
        embedding_fn=embedding_fn,
        vector_db=vector_db,
        generator_fn=offline_generator if not use_live_api else lambda query, context: live_generator(llm_client, query, context),
        top_k=2,
    )
    result = pipeline.run("What is Retrieval-Augmented Generation and how does it work?")
    output = {
        "query": result.query,
        "answer": result.answer,
        "sources": [
            {"source_id": source.metadata.get("source_id"), "chunk_index": source.metadata.get("chunk_index"), "distance": source.distance}
            for source in result.sources
        ],
        "mode": "live_api" if use_live_api else "offline_demo",
    }
    os.makedirs("outputs", exist_ok=True)
    with open(os.path.join("outputs", "rag_pipeline_sample.json"), "w", encoding="utf-8") as output_file:
        json.dump(output, output_file, indent=2)

    print("=== RAG Query-to-Answer Pipeline ===")
    print(f"Mode: {output['mode']}")
    print(f"Query: {result.query}")
    print(f"\nAnswer:\n{result.answer}")
    print("\nRetrieved sources:")
    for source in result.sources:
        print(f"- {source.metadata.get('source_id')} (chunk {source.metadata.get('chunk_index')}, distance={source.distance:.4f})")
    print("\nSaved: outputs/rag_pipeline_sample.json")


if __name__ == "__main__":
    main()