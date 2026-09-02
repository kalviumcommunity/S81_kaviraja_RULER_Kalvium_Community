"""
Similarity Metric Computation and Semantic Ranking Module.

Provides functionality for:
1. Task 1 - Compute Similarity Metric: Cosine similarity and alternative distance metrics between vector embeddings.
2. Task 2 - Compare Query Against Chunks: Embed a user query and evaluate vector similarity against corpus chunk embeddings.
3. Task 3 - Rank and Show Results: Sort chunks by similarity score, highlighting most similar and least similar results.
4. Task 4 - Justify Metric: Technical rationale explaining why cosine similarity is optimal for directional embedding vectors.
5. Task 5 - Output Generation & Reproducibility: Save formatted text and structured JSON reports containing rankings, scores, source text, and metadata.
"""

import math
import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union

try:
    from llm_client import LLMClient
    from token_chunker import TokenAwareChunker, TokenChunk
    from chunk_embedding_pipeline import ChunkEmbeddingPipeline, EmbeddedChunk
    from embedding_demo import format_vector_preview, verify_vector_dimensions, cosine_similarity
except ImportError:
    from src.llm_client import LLMClient
    from src.token_chunker import TokenAwareChunker, TokenChunk
    from src.chunk_embedding_pipeline import ChunkEmbeddingPipeline, EmbeddedChunk
    from src.embedding_demo import format_vector_preview, verify_vector_dimensions, cosine_similarity


def dot_product(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate dot product between two numeric vectors of identical length.
    """
    if not vec_a or not vec_b:
        raise ValueError("Vector inputs cannot be empty.")
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vector dimensions do not match: {len(vec_a)} vs {len(vec_b)}")
    return sum(a * b for a, b in zip(vec_a, vec_b))


def euclidean_distance(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate Euclidean distance between two numeric vectors of identical length.
    Lower score indicates higher similarity (0.0 means identical).
    """
    if not vec_a or not vec_b:
        raise ValueError("Vector inputs cannot be empty.")
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vector dimensions do not match: {len(vec_a)} vs {len(vec_b)}")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec_a, vec_b)))


@dataclass
class RankedChunk:
    """
    Data model representing a chunk scored and ranked against a query vector.
    """
    rank: int
    score: float
    chunk_id: str
    source_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    vector_preview: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert RankedChunk to dictionary representation suitable for JSON serialization."""
        return {
            "rank": self.rank,
            "score": round(self.score, 6),
            "chunk_id": self.chunk_id,
            "source_text": self.source_text,
            "metadata": self.metadata,
            "vector_preview": self.vector_preview,
        }


class SimilarityRanker:
    """
    Engine for computing vector similarity metrics, comparing query embeddings against
    corpus chunks, ranking results, and documenting metric justifications.
    """

    def __init__(self, client: Optional[LLMClient] = None, metric: str = "cosine"):
        """
        Initialize SimilarityRanker with an optional LLMClient and default metric.
        """
        self.client = client or LLMClient()
        self.metric = metric.lower().strip()

    def compute_similarity(self, vec_a: List[float], vec_b: List[float], metric: Optional[str] = None) -> float:
        """
        Task 1: Compute similarity metric between two embedding vectors.
        Supports 'cosine', 'dot_product', and 'euclidean'.
        """
        selected_metric = (metric or self.metric).lower().strip()

        if selected_metric == "cosine":
            return cosine_similarity(vec_a, vec_b)
        elif selected_metric in ("dot", "dot_product"):
            return dot_product(vec_a, vec_b)
        elif selected_metric in ("euclidean", "l2"):
            return euclidean_distance(vec_a, vec_b)
        else:
            raise ValueError(f"Unsupported similarity metric '{selected_metric}'. Choose from 'cosine', 'dot_product', 'euclidean'.")

    def justify_metric(self, metric: Optional[str] = None) -> Dict[str, Any]:
        """
        Task 4: Technical justification for chosen similarity/distance metric.
        """
        selected_metric = (metric or self.metric).lower().strip()

        justifications = {
            "cosine": {
                "metric_name": "Cosine Similarity",
                "mathematical_formula": "cos(θ) = (A · B) / (||A|| * ||B||)",
                "range": "[-1.0, 1.0] (0.0 to 1.0 for non-negative normalized embeddings)",
                "key_reasons": [
                    "Directional Semantic Alignment: Modern high-dimensional text embeddings (e.g. OpenAI text-embedding-3-small) encode semantic meaning primarily in the direction/angle of vectors rather than their magnitude.",
                    "Length Invariance: Text chunks of varying token counts produce embedding vectors with different norms. Cosine similarity normalizes vector lengths, preventing longer chunks from artificially dominating similarity scores.",
                    "Bounded & Interpretable Range: Produces a predictable score between 0.0 (orthogonal/unrelated) and 1.0 (identical direction/meaning), ideal for confidence thresholds in RAG retrieval."
                ],
                "verdict": "Cosine similarity is the industry standard metric for comparing text embeddings in vector search and RAG applications."
            },
            "dot_product": {
                "metric_name": "Dot Product",
                "mathematical_formula": "A · B = Σ (a_i * b_i)",
                "range": "[-∞, +∞]",
                "key_reasons": [
                    "Computationally Efficient: Requires fewer floating point operations than cosine similarity as magnitude square roots are omitted.",
                    "Magnitude-Sensitive: Equivalent to cosine similarity ONLY when embedding vectors are pre-normalized to unit norm (||v|| = 1)."
                ],
                "verdict": "Suitable for normalized unit vectors where speed is paramount."
            },
            "euclidean": {
                "metric_name": "Euclidean Distance (L2)",
                "mathematical_formula": "d(A, B) = sqrt(Σ (a_i - b_i)^2)",
                "range": "[0, +∞]",
                "key_reasons": [
                    "Spatial Distance: Measures absolute geometric distance between vector endpoints.",
                    "Inverse Score Scale: Lower scores indicate higher similarity, requiring custom sorting inverted relative to dot product or cosine."
                ],
                "verdict": "Useful for spatial clustering, but sensitive to vector magnitude variations across chunk sizes."
            }
        }

        return justifications.get(selected_metric, {
            "metric_name": selected_metric,
            "verdict": "Custom or unrecognized metric."
        })

    def rank_chunks(
        self,
        query: str,
        embedded_chunks: List[EmbeddedChunk],
        metric: Optional[str] = None,
        top_k: int = 3,
        query_embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Task 2 & Task 3: Compare query against chunk embeddings, calculate scores,
        and rank chunks from most similar to least similar.
        """
        selected_metric = (metric or self.metric).lower().strip()
        if not embedded_chunks:
            self.client.logger.warning("Empty embedded_chunks list passed to rank_chunks.")
            return {
                "query": query,
                "metric": selected_metric,
                "total_chunks_compared": 0,
                "ranked_chunks": [],
                "most_similar": [],
                "least_similar": [],
                "metric_justification": self.justify_metric(selected_metric)
            }

        # Task 2: Create or reuse query embedding
        usage_info = {}
        if query_embedding is None:
            self.client.logger.info(f"Generating query embedding for query: '{query}'")
            embeddings, usage = self.client.generate_embeddings([query])
            if not embeddings or len(embeddings) == 0:
                raise RuntimeError("Failed to generate embedding for query.")
            query_vec = embeddings[0]
            usage_info = usage or {}
        else:
            query_vec = query_embedding

        # Task 1 & 2: Score each chunk against the query embedding
        scored_chunks: List[Tuple[float, EmbeddedChunk]] = []
        for chunk in embedded_chunks:
            score = self.compute_similarity(query_vec, chunk.embedding, metric=selected_metric)
            scored_chunks.append((score, chunk))

        # Task 3: Rank chunks by score
        # For cosine and dot_product: higher score = more similar (descending)
        # For euclidean: lower distance = more similar (ascending)
        is_reverse = selected_metric not in ("euclidean", "l2")
        scored_chunks.sort(key=lambda item: item[0], reverse=is_reverse)

        ranked_list: List[RankedChunk] = []
        for idx, (score, chunk) in enumerate(scored_chunks, 1):
            vec_prev = format_vector_preview(chunk.embedding, preview_size=4)
            rc = RankedChunk(
                rank=idx,
                score=score,
                chunk_id=chunk.chunk_id,
                source_text=chunk.source_text,
                metadata=chunk.metadata,
                vector_preview=vec_prev
            )
            ranked_list.append(rc)

        # Identify most similar and least similar chunks
        num_k = min(top_k, len(ranked_list))
        most_similar = [rc.to_dict() for rc in ranked_list[:num_k]]
        least_similar = [rc.to_dict() for rc in reversed(ranked_list[-num_k:])]

        return {
            "query": query,
            "query_vector_dimension": len(query_vec),
            "query_vector_preview": format_vector_preview(query_vec, preview_size=4),
            "metric": selected_metric,
            "total_chunks_compared": len(ranked_list),
            "ranked_chunks": [rc.to_dict() for rc in ranked_list],
            "most_similar": most_similar,
            "least_similar": least_similar,
            "metric_justification": self.justify_metric(selected_metric),
            "token_usage": usage_info
        }

    def generate_ranking_reports(
        self,
        ranking_results: Dict[str, Any],
        output_txt_path: Optional[str] = None,
        output_json_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Task 5: Format human-readable text report and structured JSON output.
        """
        query = ranking_results.get("query", "")
        metric = ranking_results.get("metric", "cosine")
        total_chunks = ranking_results.get("total_chunks_compared", 0)
        ranked_chunks = ranking_results.get("ranked_chunks", [])
        most_sim = ranking_results.get("most_similar", [])
        least_sim = ranking_results.get("least_similar", [])
        justification = ranking_results.get("metric_justification", {})

        # Build clean text report
        lines = [
            "Vector Similarity Ranking Report",
            "================================",
            "",
            f"Query: \"{query}\"",
            f"Metric Used: {justification.get('metric_name', metric.upper())}",
            f"Total Chunks Scored: {total_chunks}",
            f"Query Dimension: {ranking_results.get('query_vector_dimension', 'N/A')}",
            f"Query Vector Preview: {ranking_results.get('query_vector_preview', 'N/A')}",
            "",
            "================================",
            "Metric Justification (Task 4)",
            "================================",
            f"Formula: {justification.get('mathematical_formula', 'N/A')}",
            f"Score Range: {justification.get('range', 'N/A')}",
            "Key Reasons:",
        ]

        for reason in justification.get("key_reasons", []):
            lines.append(f" - {reason}")
        lines.append(f"Verdict: {justification.get('verdict', '')}")

        lines.extend([
            "",
            "================================",
            "Most Similar Chunks (Top Ranked)",
            "================================"
        ])

        for chunk in most_sim:
            lines.extend([
                f"Rank #{chunk['rank']} | Score: {chunk['score']:.6f} | Chunk ID: {chunk['chunk_id']}",
                f"Source Path: {chunk['metadata'].get('source_path', 'N/A')}",
                f"Filename: {chunk['metadata'].get('filename', 'N/A')}",
                f"Section: {chunk['metadata'].get('section', 'N/A')}",
                f"Text: \"{chunk['source_text']}\"",
                f"Vector Preview: {chunk['vector_preview']}",
                "--------------------------------------------------"
            ])

        lines.extend([
            "",
            "================================",
            "Least Similar Chunks (Bottom Ranked)",
            "================================"
        ])

        for chunk in least_sim:
            lines.extend([
                f"Rank #{chunk['rank']} | Score: {chunk['score']:.6f} | Chunk ID: {chunk['chunk_id']}",
                f"Source Path: {chunk['metadata'].get('source_path', 'N/A')}",
                f"Filename: {chunk['metadata'].get('filename', 'N/A')}",
                f"Section: {chunk['metadata'].get('section', 'N/A')}",
                f"Text: \"{chunk['source_text']}\"",
                f"Vector Preview: {chunk['vector_preview']}",
                "--------------------------------------------------"
            ])

        text_content = "\n".join(lines) + "\n"

        if output_txt_path:
            os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(text_content)

        if output_json_path:
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(ranking_results, f, indent=2)

        return ranking_results

    def export_vector_matrix(
        self,
        embedded_chunks: List[EmbeddedChunk],
        query_vec: Optional[List[float]] = None,
        output_json_path: str = os.path.join("outputs", "vector_matrix_output.json"),
        output_txt_path: str = os.path.join("outputs", "vector_matrix_output.txt")
    ) -> Dict[str, Any]:
        """
        Exports explicit 2D Vector Matrix (N x D) and Chunk-by-Chunk Pairwise Similarity Matrix.
        """
        if not embedded_chunks:
            return {}

        num_chunks = len(embedded_chunks)
        dim = embedded_chunks[0].dimension
        matrix_data = [chunk.embedding for chunk in embedded_chunks]
        chunk_ids = [chunk.chunk_id for chunk in embedded_chunks]

        # Calculate N x N pairwise similarity matrix between chunks
        pairwise_sim_matrix = []
        for i in range(num_chunks):
            row = []
            for j in range(num_chunks):
                sim = self.compute_similarity(embedded_chunks[i].embedding, embedded_chunks[j].embedding, metric="cosine")
                row.append(round(sim, 6))
            pairwise_sim_matrix.append(row)

        matrix_export = {
            "matrix_metadata": {
                "rows_chunk_count": num_chunks,
                "columns_dimension": dim,
                "matrix_shape": [num_chunks, dim],
                "chunk_ids": chunk_ids,
                "has_query_vector": query_vec is not None,
                "query_vector_dimension": len(query_vec) if query_vec else 0
            },
            "query_vector": query_vec or [],
            "vector_matrix": matrix_data,
            "pairwise_similarity_matrix": pairwise_sim_matrix,
            "chunk_catalog": [
                {
                    "row_index": idx,
                    "chunk_id": chunk.chunk_id,
                    "source_text_snippet": chunk.source_text[:100],
                    "vector_dimension": chunk.dimension,
                    "first_4_dimensions": chunk.embedding[:4]
                }
                for idx, chunk in enumerate(embedded_chunks)
            ]
        }

        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(matrix_export, f, indent=2)

        # Build readable text report showing full matrix layout & pairwise table
        txt_lines = [
            "Vector Matrix & Pairwise Similarity Export",
            "==========================================",
            "",
            f"Matrix Dimensions: {num_chunks} Chunks x {dim} Embedding Dimensions",
            f"Total Floating-Point Matrix Values: {num_chunks * dim}",
            "",
            "==========================================",
            "Pairwise Chunk Similarity Matrix (Cosine)",
            "==========================================",
            "Row Chunk ID \\ Column Chunk ID | " + " | ".join([f"C{i}" for i in range(num_chunks)]),
            "-" * 80
        ]

        for i, row in enumerate(pairwise_sim_matrix):
            sim_str = " | ".join([f"{val:.4f}" for val in row])
            txt_lines.append(f"C{i} ({chunk_ids[i][:25]}...) | {sim_str}")

        txt_lines.extend([
            "",
            "==========================================",
            "Vector Matrix Row Details",
            "==========================================",
        ])

        for idx, chunk in enumerate(embedded_chunks):
            txt_lines.extend([
                f"Row Matrix Index [{idx}]: Chunk ID '{chunk.chunk_id}'",
                f"Text Snippet: \"{chunk.source_text[:90]}...\"",
                f"Vector Dimension: {chunk.dimension}",
                f"Vector Head [0:8]: {[round(x, 5) for x in chunk.embedding[:8]]}",
                f"Vector Tail [-8:]: {[round(x, 5) for x in chunk.embedding[-8:]]}",
                "------------------------------------------"
            ])

        os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(txt_lines) + "\n")

        return matrix_export

    def run_demonstration(
        self,
        query: str = "What are the rules and approval thresholds for high-value transaction payments?",
        output_txt_path: str = os.path.join("outputs", "similarity_ranking_output.txt"),
        output_json_path: str = os.path.join("outputs", "similarity_ranking_results.json")
    ) -> Dict[str, Any]:
        """
        Execute end-to-end similarity ranking demonstration:
        1. Ingest small corpus & generate prepared chunks via TokenAwareChunker
        2. Embed prepared chunks via ChunkEmbeddingPipeline
        3. Embed sample query and compute cosine similarity against all chunks
        4. Rank chunks and generate output reports (Tasks 1 to 5)
        """
        self.client.logger.info("Executing Similarity Ranking Demonstration...")

        # Step 1 & 2: Pipeline execution to get EmbeddedChunk list
        emb_pipeline = ChunkEmbeddingPipeline(client=self.client)
        embedded_chunks, pipeline_stats = emb_pipeline.run_pipeline(
            output_txt_path=None,  # skip overwriting pipeline standalone outputs
            output_json_path=None
        )

        if not embedded_chunks:
            raise RuntimeError("Failed to generate embedded chunks for similarity ranking demonstration.")

        # Step 3 & 4: Rank chunks against query
        ranking_results = self.rank_chunks(
            query=query,
            embedded_chunks=embedded_chunks,
            metric=self.metric,
            top_k=2
        )

        # Step 5: Save formatted text and JSON reports
        self.generate_ranking_reports(
            ranking_results=ranking_results,
            output_txt_path=output_txt_path,
            output_json_path=output_json_path
        )

        # Step 6: Export explicit Vector Matrix (N x D) output files
        self.export_vector_matrix(
            embedded_chunks=embedded_chunks,
            output_json_path=os.path.join("outputs", "vector_matrix_output.json"),
            output_txt_path=os.path.join("outputs", "vector_matrix_output.txt")
        )

        return ranking_results



if __name__ == "__main__":
    ranker = SimilarityRanker()
    results = ranker.run_demonstration()
    print("\nSimilarity Ranking Demonstration Completed Successfully!")
    print(f"Query: \"{results['query']}\"")
    print(f"Metric: {results['metric']}")
    print(f"Total Chunks Scored: {results['total_chunks_compared']}")
    print("\n--- Top Most Similar Result ---")
    top_res = results['most_similar'][0]
    print(f"Rank #{top_res['rank']} | Score: {top_res['score']:.6f} | Chunk ID: {top_res['chunk_id']}")
    print(f"Text Preview: \"{top_res['source_text'][:100]}...\"")
    print("\n--- Top Least Similar Result ---")
    bottom_res = results['least_similar'][0]
    print(f"Rank #{bottom_res['rank']} | Score: {bottom_res['score']:.6f} | Chunk ID: {bottom_res['chunk_id']}")
    print(f"Text Preview: \"{bottom_res['source_text'][:100]}...\"")
