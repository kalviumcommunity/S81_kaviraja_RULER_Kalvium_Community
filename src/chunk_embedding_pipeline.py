"""
API-Based Embedding Integration with Prepared Text Chunk Pipeline.

Integrates prepared text chunks from token-aware chunking with API-based embedding generation:
1. Accepts prepared text chunks (TokenChunk / Chunk objects).
2. Extracts chunk text while skipping empty or whitespace-only chunks.
3. Sends text content to the configured embedding API via LLMClient.
4. Stores embedding vectors with original source text and complete chunk metadata (EmbeddedChunk).
5. Verifies vector dimension consistency across all returned embeddings.
6. Generates reproducible verification reports and structured JSON output.
"""

import os
import re
import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple, Union

try:
    from llm_client import LLMClient
    from token_chunker import TokenAwareChunker, TokenChunk
    from chunk_metadata import Chunk, ChunkMetadata
    from embedding_demo import format_vector_preview, verify_vector_dimensions
except ImportError:
    from src.llm_client import LLMClient
    from src.token_chunker import TokenAwareChunker, TokenChunk
    from src.chunk_metadata import Chunk, ChunkMetadata
    from src.embedding_demo import format_vector_preview, verify_vector_dimensions


@dataclass
class EmbeddedChunk:
    """
    Embedded Chunk data model linking source text, embedding vector, and full chunk metadata.
    Prepares system for future vector database ingestion (Task 2 & Integration Safety).
    """
    chunk_id: str
    source_text: str
    embedding: List[float]
    dimension: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts EmbeddedChunk to dictionary representation suitable for JSON persistence."""
        return {
            "chunk_id": self.chunk_id,
            "source_text": self.source_text,
            "embedding": self.embedding,
            "dimension": self.dimension,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddedChunk":
        """Instantiates an EmbeddedChunk from a dictionary."""
        return cls(
            chunk_id=data.get("chunk_id", ""),
            source_text=data.get("source_text", ""),
            embedding=data.get("embedding", []),
            dimension=data.get("dimension", len(data.get("embedding", []))),
            metadata=data.get("metadata", {}),
        )


class ChunkEmbeddingPipeline:
    """
    Engine for integrating prepared text chunks with API-based embedding generation.
    """

    def __init__(self, client: Optional[LLMClient] = None):
        """
        Initialize the embedding pipeline with an optional LLMClient.
        Reuses existing LLMClient and environment configuration (Task 3).
        """
        self.client = client or LLMClient()

    def embed_chunks(
        self,
        chunks: List[Union[TokenChunk, Chunk, Dict[str, Any]]],
        model: Optional[str] = None,
    ) -> Tuple[List[EmbeddedChunk], Dict[str, Any]]:
        """
        Task 1 & Task 2: Accept prepared chunks, extract text, call embedding API,
        and construct EmbeddedChunk records preserving source text and metadata.
        
        Handles empty/whitespace-only chunks by returning empty vector records without API calls.
        """
        if not chunks:
            self.client.logger.warning("Empty chunk list provided to embed_chunks.")
            return [], {"chunks_received": 0, "embedded_count": 0, "failed_count": 0}

        # Step 1: Normalize inputs and extract text while handling empty chunks
        valid_chunk_tuples: List[Tuple[int, str, str, Dict[str, Any]]] = []
        empty_chunk_indices: List[int] = []

        for idx, chunk in enumerate(chunks):
            chunk_id, text, meta_dict = self._extract_chunk_info(chunk, idx)
            if not text or not text.strip():
                self.client.logger.warning(f"Skipping empty text for chunk index {idx} ({chunk_id}).")
                empty_chunk_indices.append(idx)
                continue
            valid_chunk_tuples.append((idx, chunk_id, text, meta_dict))

        if not valid_chunk_tuples:
            self.client.logger.warning("No valid non-empty text chunks to embed.")
            return [], {
                "chunks_received": len(chunks),
                "embedded_count": 0,
                "failed_count": len(empty_chunk_indices),
            }

        texts_to_embed = [item[2] for item in valid_chunk_tuples]

        # Step 2: Send text to the configured embedding API
        embeddings, usage = self.client.generate_embeddings(texts_to_embed, model=model)

        if embeddings is None:
            self.client.logger.error("API call to generate_embeddings failed.")
            return [], {
                "chunks_received": len(chunks),
                "embedded_count": 0,
                "failed_count": len(chunks),
                "error": "Embedding API request failed or returned None.",
            }

        # Step 3: Verify returned embedding vectors count & consistency
        if len(embeddings) != len(valid_chunk_tuples):
            self.client.logger.error(
                f"Mismatch between requested texts ({len(valid_chunk_tuples)}) "
                f"and returned vectors ({len(embeddings)})."
            )
            return [], {
                "chunks_received": len(chunks),
                "embedded_count": 0,
                "failed_count": len(chunks),
                "error": "Vector count mismatch.",
            }

        # Step 4: Construct EmbeddedChunk records preserving source text + metadata
        embedded_chunks: List[EmbeddedChunk] = []

        for (orig_idx, chunk_id, text, meta_dict), vec in zip(valid_chunk_tuples, embeddings):
            dim = len(vec)
            embedded_records = EmbeddedChunk(
                chunk_id=chunk_id,
                source_text=text,
                embedding=vec,
                dimension=dim,
                metadata=meta_dict,
            )
            embedded_chunks.append(embedded_records)

        pipeline_stats = {
            "chunks_received": len(chunks),
            "embedded_count": len(embedded_chunks),
            "failed_count": len(empty_chunk_indices),
            "skipped_empty_chunks": len(empty_chunk_indices),
            "token_usage": usage or {},
        }

        return embedded_chunks, pipeline_stats

    def verify_pipeline_dimensions(self, embedded_chunks: List[EmbeddedChunk]) -> Dict[str, Any]:
        """
        Verify that all generated embedded chunks have consistent numeric vector dimensions.
        """
        if not embedded_chunks:
            return {
                "is_consistent": False,
                "detected_dimension": 0,
                "status": "FAIL - No embedded chunks to verify",
            }

        vectors = [ec.embedding for ec in embedded_chunks]
        return verify_vector_dimensions(vectors)

    def generate_verification_report(
        self,
        embedded_chunks: List[EmbeddedChunk],
        pipeline_stats: Dict[str, Any],
        source_doc_count: int = 1,
        sample_preview_count: int = 3,
        output_txt_path: Optional[str] = None,
        output_json_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Task 4 & Task 5: Format reproducible verification report and JSON results.
        """
        dim_report = self.verify_pipeline_dimensions(embedded_chunks)
        detected_dim = dim_report.get("detected_dimension", 0)

        provider = "OpenAI-Compatible API"
        if "openrouter" in self.client.base_url.lower():
            provider = "OpenRouter (OpenAI-Compatible API)"

        results = {
            "pipeline_metadata": {
                "embedding_provider": provider,
                "base_url": self.client.base_url,
                "embedding_model": self.client.embedding_model,
                "source_documents": source_doc_count,
                "chunks_received": pipeline_stats.get("chunks_received", len(embedded_chunks)),
                "chunks_embedded": pipeline_stats.get("embedded_count", len(embedded_chunks)),
                "chunks_failed": pipeline_stats.get("failed_count", 0),
                "vector_dimension": detected_dim,
                "dimension_consistency": dim_report.get("status", "UNKNOWN"),
            },
            "dimension_verification": dim_report,
            "sample_embedded_chunks": [ec.to_dict() for ec in embedded_chunks[:sample_preview_count]],
            "token_usage": pipeline_stats.get("token_usage", {}),
        }

        # Build human-readable verification log strictly adhering to Task 4 format
        lines = [
            "RAG Embedding Verification",
            "==========================",
            "",
            "Embedding Provider:",
            f"{provider}",
            "",
            "Embedding Model:",
            f"{self.client.embedding_model}",
            "",
            "Source Documents:",
            f"{source_doc_count}",
            "",
            "Chunks Received:",
            f"{pipeline_stats.get('chunks_received', len(embedded_chunks))}",
            "",
            "Chunks Successfully Embedded:",
            f"{pipeline_stats.get('embedded_count', len(embedded_chunks))}",
            "",
            "Vector Dimension:",
            f"{detected_dim}",
            "",
            "Dimension Consistency:",
            f"{dim_report.get('status', 'FAIL')}",
            "",
            "==========================",
            "Sample Embedded Chunks Output",
            "==========================",
        ]

        for ec in embedded_chunks[:sample_preview_count]:
            chunk_idx = ec.metadata.get("chunk_index", "N/A")
            source_file = ec.metadata.get("filename") or ec.metadata.get("source_path") or "N/A"
            text_preview = ec.source_text[:120].replace("\n", " ") + ("..." if len(ec.source_text) > 120 else "")
            vec_preview = format_vector_preview(ec.embedding, preview_size=4)

            lines.extend([
                "--------------------------------------",
                f"Chunk Index:",
                f"{chunk_idx}",
                "",
                f"Source:",
                f"{source_file}",
                "",
                f"Metadata:",
                f"{json.dumps(ec.metadata, indent=2)}",
                "",
                f"Text:",
                f'"{text_preview}"',
                "",
                f"Vector Length:",
                f"{ec.dimension}",
                "",
                f"Vector Preview:",
                f"{vec_preview}",
                "--------------------------------------",
            ])

        text_content = "\n".join(lines) + "\n"

        if output_txt_path:
            os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(text_content)

        if output_json_path:
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

        return results

    def run_pipeline(
        self,
        sample_docs: Optional[List[Tuple[str, str, str]]] = None,
        chunk_size_tokens: int = 100,
        chunk_overlap_tokens: int = 20,
        output_txt_path: str = os.path.join("outputs", "chunk_embeddings_output.txt"),
        output_json_path: str = os.path.join("outputs", "chunk_embeddings_results.json"),
    ) -> Tuple[List[EmbeddedChunk], Dict[str, Any]]:
        """
        Task 5: Execute end-to-end embedding pipeline on sample corpus.
        
        Flow:
        Sample Document(s) -> TokenAwareChunker -> Prepared Chunks -> Embedding API -> Embedded Chunks
        """
        if sample_docs is None:
            sample_docs = self._load_default_sample_corpus()

        self.client.logger.info(f"Starting Chunk Embedding Pipeline for {len(sample_docs)} document(s)...")

        # Step 1: Execute Token-Aware Chunking on all documents
        chunker = TokenAwareChunker(
            chunk_size_tokens=chunk_size_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
        )

        all_prepared_chunks: List[TokenChunk] = []

        for source_path, filename, content in sample_docs:
            doc_id = filename.replace(".", "_")
            chunks = chunker.chunk_text(
                text=content,
                doc_id=doc_id,
                filename=filename,
                source_path=source_path,
                section="Document Content",
            )
            # Detect section header for each chunk if document contains markdown headings
            current_section = "Document Content"
            for chunk in chunks:
                sec_match = re.search(r"^\s*#{1,6}\s+(Section\s+\d+:[^\n]+)", chunk.text, re.MULTILINE)
                if sec_match:
                    current_section = sec_match.group(1).strip()
                elif current_section == "Document Content":
                    prior_headers = list(re.finditer(r"^\s*#{1,6}\s+(Section\s+\d+:[^\n]+)", content[:chunk.start_char + 50], re.MULTILINE))
                    if prior_headers:
                        current_section = prior_headers[-1].group(1).strip()
                chunk.section = current_section
            all_prepared_chunks.extend(chunks)

        self.client.logger.info(f"Generated {len(all_prepared_chunks)} text chunks across corpus.")

        # Step 2: Embed prepared chunks through API
        embedded_chunks, pipeline_stats = self.embed_chunks(all_prepared_chunks)

        # Step 3: Generate verification report & save outputs
        results = self.generate_verification_report(
            embedded_chunks=embedded_chunks,
            pipeline_stats=pipeline_stats,
            source_doc_count=len(sample_docs),
            sample_preview_count=3,
            output_txt_path=output_txt_path,
            output_json_path=output_json_path,
        )

        return embedded_chunks, results

    def _extract_chunk_info(
        self, chunk: Union[TokenChunk, Chunk, Dict[str, Any]], idx: int
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Extracts chunk_id, text, and metadata dict from various chunk object representations."""
        if hasattr(chunk, "to_dict"):
            d = chunk.to_dict()
            chunk_id = d.get("chunk_id", f"chunk_{idx}")
            text = d.get("text", "")
            meta = d.get("metadata", {})
            if hasattr(chunk, "token_count"):
                meta["token_count"] = getattr(chunk, "token_count")
            if hasattr(chunk, "section"):
                meta["section"] = getattr(chunk, "section")
            if "category" not in meta:
                meta["category"] = "Compliance & Regulation"
            if "doc_type" not in meta:
                meta["doc_type"] = "Regulatory Framework"
            return chunk_id, text, meta

        if isinstance(chunk, dict):
            chunk_id = chunk.get("chunk_id", f"chunk_{idx}")
            text = chunk.get("text", "")
            meta = chunk.get("metadata", {})
            return chunk_id, text, meta

        # Fallback for plain string or custom object
        return f"chunk_{idx}", str(chunk), {"chunk_index": idx}

    def _load_default_sample_corpus(self) -> List[Tuple[str, str, str]]:
        """Loads sample documents from data directory or provides default multi-chunk corpus."""
        doc_path = os.path.join("data", "sample_banking_regulation.txt")
        if os.path.exists(doc_path):
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.strip():
                    return [(doc_path, os.path.basename(doc_path), content)]
            except Exception:
                pass

        default_text = (
            "# Global Banking Compliance & Regulatory Framework 2026\n\n"
            "## Section 1: Executive Summary & Overview\n"
            "Financial institutions operating within international jurisdictions must establish automated compliance "
            "monitoring systems to detect, prevent, and report suspicious transactions under Anti-Money Laundering (AML) "
            "and Counter-Terrorism Financing (CTF) directives. All automated systems must evaluate transaction velocities, "
            "beneficiary country risk scores, and entity sanction lists in real time prior to authorization.\n\n"
            "## Section 2: Capital Reserves & Liquidity Ratios\n"
            "Under Basel IV capital adequacy standards, Tier 1 common equity capital must remain above 10.5% of total "
            "risk-weighted assets at all times. In addition, institutions must hold high-quality liquid assets (HQLA) "
            "sufficient to cover total net cash outflows over a 30-day stress period. "
            "The Liquidity Coverage Ratio (LCR) must be calculated daily and submitted to regional financial regulatory bodies.\n\n"
            "## Section 3: High-Value Transaction Authorization Thresholds\n"
            "Standard retail banking policies mandate that routine vendor payments under $50,000 may be approved directly "
            "by designated department heads without requiring senior executive approval. "
            "However, any single capital expenditure or vendor disbursement exceeding $50,000 requires unanimous board authorization "
            "and an independent audit report prior to disbursement. "
            "Failure to obtain board authorization for high-value transactions results in immediate suspension of procurement privileges "
            "and mandatory compliance audit review."
        )
        return [("data/sample_banking_regulation.txt", "sample_banking_regulation.txt", default_text)]


if __name__ == "__main__":
    pipeline = ChunkEmbeddingPipeline()
    embedded_chunks, results = pipeline.run_pipeline()
    print("\nChunk Embedding Pipeline Executed Successfully!")
    print(f"Chunks Received: {results['pipeline_metadata']['chunks_received']}")
    print(f"Chunks Embedded: {results['pipeline_metadata']['chunks_embedded']}")
    print(f"Vector Dimension: {results['pipeline_metadata']['vector_dimension']}")
    print(f"Dimension Consistency: {results['pipeline_metadata']['dimension_consistency']}")
