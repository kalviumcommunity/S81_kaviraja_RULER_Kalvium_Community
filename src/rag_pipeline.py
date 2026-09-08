"""Stage-oriented query-to-answer RAG pipeline."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class RetrievedSource:
    text: str
    metadata: Dict[str, Any]
    distance: float


@dataclass
class RAGResponse:
    query: str
    answer: str
    sources: List[RetrievedSource]
    context: str


def embed(query: str, embedding_fn: Callable[[str], List[float]]) -> List[float]:
    """Convert the user query into one vector for semantic search."""
    if not query.strip():
        raise ValueError("query must not be empty")
    return embedding_fn(query)


def retrieve(
    query_embedding: List[float],
    vector_db: Any,
    top_k: int = 3,
) -> List[RetrievedSource]:
    """Retrieve the nearest chunks and preserve their source metadata."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    results = vector_db.search([query_embedding], n_results=top_k)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    return [
        RetrievedSource(
            text=text,
            metadata=metadata or {},
            distance=distance,
        )
        for text, metadata, distance in zip(documents, metadatas, distances)
    ]


def assemble(query: str, sources: List[RetrievedSource]) -> str:
    """Build grounded context with stable source labels for the generator."""
    if not sources:
        return f"Question: {query}\n\nContext: No relevant sources were retrieved."

    sections = [f"Question: {query}", "", "Context:"]
    for index, source in enumerate(sources, 1):
        source_id = source.metadata.get("source_id", "unknown source")
        chunk_index = source.metadata.get("chunk_index", "?")
        sections.append(f"[Source {index}: {source_id}, chunk {chunk_index}]")
        sections.append(source.text)
    return "\n".join(sections)


def generate(
    query: str,
    context: str,
    generator_fn: Callable[[str, str], str],
) -> str:
    """Generate an answer from the query and retrieved context only."""
    answer = generator_fn(query, context)
    if not answer or not answer.strip():
        raise RuntimeError("generator returned an empty answer")
    return answer.strip()


class RAGPipeline:
    """Coordinates the four independently testable RAG stages."""

    def __init__(
        self,
        embedding_fn: Callable[[str], List[float]],
        vector_db: Any,
        generator_fn: Callable[[str, str], str],
        top_k: int = 3,
    ):
        self.embedding_fn = embedding_fn
        self.vector_db = vector_db
        self.generator_fn = generator_fn
        self.top_k = top_k

    def run(self, query: str) -> RAGResponse:
        query_embedding = embed(query, self.embedding_fn)
        sources = retrieve(query_embedding, self.vector_db, self.top_k)
        context = assemble(query, sources)
        answer = generate(query, context, self.generator_fn)
        return RAGResponse(query=query, answer=answer, sources=sources, context=context)