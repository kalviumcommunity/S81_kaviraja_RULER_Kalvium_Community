"""
Chunk Re-Ranking for Precision Module (Tasks 1 to 4).

Implements:
- Task 1: Retrieve a larger candidate set (e.g., initial_k = 10 chunks).
- Task 2: Re-rank candidates by query relevance using LLM scoring, cross-encoder heuristics, or hybrid scoring.
- Task 3: Demonstrate improved top results (top-3 after re-ranking more relevant than initial vector order).
- Task 4: Compare before-and-after ordering with original vector scores, re-rank scores, source text, and metadata.
"""

import os
import re
import json
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple


def setup_logger(log_file_path: Optional[str] = None) -> logging.Logger:
    """Configures structured logging for the Re-ranker module."""
    logger = logging.getLogger("Reranker")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if log_file_path:
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            fh = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger


@dataclass
class CandidateChunk:
    """
    Data structure representing a retrieved candidate chunk across the two-stage retrieval lifecycle.
    """
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    initial_rank: int
    vector_distance: float
    vector_similarity: float
    rerank_score: float = 0.0
    final_rank: int = 0
    rank_change: int = 0  # initial_rank - final_rank (positive = promoted, negative = demoted)
    relevance_reasoning: str = ""
    is_selected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Converts candidate chunk representation to a serializable dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata,
            "initial_rank": self.initial_rank,
            "vector_distance": round(self.vector_distance, 4),
            "vector_similarity": round(self.vector_similarity, 4),
            "rerank_score": round(self.rerank_score, 4),
            "final_rank": self.final_rank,
            "rank_change": self.rank_change,
            "rank_shift_label": (
                f"+{self.rank_change} (Promoted)" if self.rank_change > 0
                else (f"{self.rank_change} (Demoted)" if self.rank_change < 0 else "0 (Unchanged)")
            ),
            "relevance_reasoning": self.relevance_reasoning,
            "is_selected": self.is_selected
        }


class ChunkReranker:
    """
    Two-Stage Retrieval & Re-Ranking Engine.
    
    1. First Stage: High-recall vector search retrieves a large candidate pool (e.g. k=10).
    2. Second Stage: High-precision scoring (Cross-Encoder / LLM / Lexical-Semantic Hybrid)
       evaluates fine-grained query-document alignment and selects top-k (e.g. k=3).
    """

    def __init__(self, llm_client: Optional[Any] = None, log_file: Optional[str] = None):
        self.llm_client = llm_client
        self.logger = setup_logger(log_file)

    def calculate_custom_relevance_score(self, query: str, text: str, vector_sim: float = 0.5) -> Tuple[float, str]:
        """
        Custom Cross-Encoder & Lexical-Semantic Relevance Scorer.
        
        Evaluates:
        1. Exact keyword & multi-word phrase matching.
        2. Query term coverage ratio (how many distinct query concepts appear).
        3. Term frequency saturation and density in chunk text.
        4. Information density (penalizes generic boilerplate, rewards specific entities & figures).
        5. Vector similarity baseline weighting.
        """
        if not text or not query:
            return 0.0, "Empty query or text."

        query_lower = query.lower()
        text_lower = text.lower()

        # Tokenize query into meaningful search keywords (removing stop words)
        stopwords = {
            "a", "an", "the", "in", "on", "of", "at", "by", "for", "with", "about",
            "against", "between", "into", "through", "during", "before", "after",
            "above", "below", "to", "from", "up", "down", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did", "and",
            "but", "if", "or", "because", "as", "until", "while", "what", "which",
            "who", "whom", "this", "that", "these", "those", "am", "how", "why"
        }
        raw_terms = re.findall(r"\b[a-zA-Z0-9_\-\.\%]+\b", query_lower)
        keywords = [t for t in raw_terms if t not in stopwords and len(t) > 1]
        
        if not keywords:
            keywords = raw_terms if raw_terms else [query_lower]

        # 1. Term Coverage Score (ratio of query keywords present in chunk)
        matched_keywords = [kw for kw in keywords if kw in text_lower]
        term_coverage = len(matched_keywords) / len(keywords) if keywords else 0.0

        # 2. Exact Multi-Word Phrase Matching Bonus
        phrase_bonus = 0.0
        # Check for 2-word, 3-word n-grams from query
        words = query_lower.split()
        for n in [4, 3, 2]:
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                if len(phrase) > 5 and phrase in text_lower:
                    phrase_bonus += 0.15 * n
                    break

        # 3. Specific Entity & Numeric Precision Bonus (e.g. percentages, ratios, hours, standards)
        numeric_terms = re.findall(r"\b(?:\d+(?:\.\d+)?%?|\b(?:aes-\d+|tls|poip|mfa|lcr|hcla|tier\s*\d+))\b", query_lower)
        numeric_bonus = 0.0
        for num in numeric_terms:
            if num in text_lower:
                numeric_bonus += 0.20

        # 4. Keyword Density / Saturation Score
        match_count = sum(text_lower.count(kw) for kw in matched_keywords)
        density_score = min(0.3, (match_count / max(1, len(text.split()))) * 2.5)

        # 5. Combine into calibrated Re-Rank Score (0.0 to 1.0 scale)
        # Weights: 40% Term Coverage + 25% Vector Similarity + 15% Phrase Bonus + 10% Numeric Bonus + 10% Density
        raw_score = (
            (term_coverage * 0.40) +
            (max(0.0, min(1.0, vector_sim)) * 0.25) +
            (min(0.20, phrase_bonus) * 1.0) +
            (min(0.20, numeric_bonus) * 1.0) +
            (density_score * 0.5)
        )
        final_score = min(1.0, max(0.05, round(raw_score, 4)))

        reasoning = (
            f"Coverage: {len(matched_keywords)}/{len(keywords)} terms ({term_coverage*100:.0f}%), "
            f"Vector Sim: {vector_sim:.3f}, Phrase/Entity match: +{phrase_bonus + numeric_bonus:.2f}"
        )
        return final_score, reasoning

    def score_with_llm(self, query: str, text: str, vector_sim: float = 0.5) -> Tuple[float, str]:
        """
        LLM-based Cross-Encoder Scoring Step (Task 2).
        Prompts LLM to evaluate direct factual relevance on a 0.0 - 1.0 scale.
        """
        if not self.llm_client:
            return self.calculate_custom_relevance_score(query, text, vector_sim)

        system_prompt = (
            "You are an expert RAG relevance re-ranker. Given a user query and a candidate document chunk, "
            "evaluate how directly, accurately, and completely the chunk answers the query. "
            "Assign a relevance_score between 0.0 (completely irrelevant) and 1.0 (perfectly answers the query). "
            "Return structured JSON with keys: 'relevance_score' (float) and 'reasoning' (short 1-sentence string)."
        )
        user_prompt = f"Query: \"{query}\"\n\nCandidate Chunk Text:\n\"\"\"{text}\"\"\""

        try:
            res, _ = self.llm_client.create_structured_completion(
                system_message=system_prompt,
                user_message=user_prompt,
                required_fields=["relevance_score", "reasoning"],
                default_values={"relevance_score": 0.5, "reasoning": "Evaluated relevance"},
                temperature=0.0
            )
            if res and "relevance_score" in res:
                score = float(res["relevance_score"])
                reasoning = res.get("reasoning", "LLM relevance score")
                # Blend with vector similarity for stability
                blended_score = round(0.80 * score + 0.20 * vector_sim, 4)
                return min(1.0, max(0.0, blended_score)), f"LLM: {reasoning}"
        except Exception as e:
            self.logger.warning(f"LLM scoring fallback triggered: {e}")

        return self.calculate_custom_relevance_score(query, text, vector_sim)

    def retrieve_candidate_set(
        self,
        vector_db: Any,
        query: str,
        initial_k: int = 10,
        query_embedding: Optional[List[float]] = None
    ) -> List[CandidateChunk]:
        """
        Task 1: Retrieve a larger candidate set (e.g. initial_k = 10) from the vector database.
        """
        self.logger.info(f"[Task 1] Retrieving initial candidate set of {initial_k} chunks for query: '{query}'")

        if query_embedding is None and self.llm_client:
            embs, _ = self.llm_client.create_embeddings([query])
            query_embedding = embs[0] if embs else None

        if query_embedding is None:
            raise ValueError("Query embedding or LLM client is required to perform vector retrieval.")

        search_results = vector_db.search([query_embedding], n_results=initial_k)
        candidates: List[CandidateChunk] = []

        if not search_results or not search_results.get("documents") or not search_results["documents"][0]:
            self.logger.warning("No candidates found in vector search.")
            return []

        docs = search_results["documents"][0]
        metas = search_results.get("metadatas", [[]])[0]
        distances = search_results.get("distances", [[]])[0]
        ids = search_results.get("ids", [[]])[0] if search_results.get("ids") else [f"chunk_{i+1}" for i in range(len(docs))]

        for idx, (doc_text, meta, dist, cid) in enumerate(zip(docs, metas, distances, ids), start=1):
            # Chroma cosine distance = 1 - cosine_similarity. Similarity = 1 - distance
            similarity = max(0.0, 1.0 - dist)
            candidate = CandidateChunk(
                chunk_id=cid,
                text=doc_text,
                metadata=meta or {},
                initial_rank=idx,
                vector_distance=float(dist),
                vector_similarity=float(similarity)
            )
            candidates.append(candidate)

        self.logger.info(f"[Task 1] Successfully retrieved {len(candidates)} initial candidates.")
        return candidates

    def rerank(
        self,
        query: str,
        candidates: List[CandidateChunk],
        top_k: int = 3,
        method: str = "hybrid"
    ) -> Tuple[List[CandidateChunk], List[CandidateChunk]]:
        """
        Task 2: Re-rank candidates by relevance to the query using scoring.
        
        :param query: User query string
        :param candidates: List of CandidateChunk from initial retrieval (Task 1)
        :param top_k: Number of final chunks to keep (default 3)
        :param method: 'llm', 'custom', or 'hybrid'
        :return: (all_reranked_candidates, top_k_selected_chunks)
        """
        self.logger.info(f"[Task 2] Re-ranking {len(candidates)} candidate chunks using method: '{method}' (final k={top_k})")

        reranked_pool: List[CandidateChunk] = []

        for candidate in candidates:
            if method == "llm":
                score, reasoning = self.score_with_llm(query, candidate.text, candidate.vector_similarity)
            elif method == "custom":
                score, reasoning = self.calculate_custom_relevance_score(query, candidate.text, candidate.vector_similarity)
            else:  # hybrid
                # Compute custom lexical score + vector sim blend
                custom_score, c_reason = self.calculate_custom_relevance_score(query, candidate.text, candidate.vector_similarity)
                score = custom_score
                reasoning = c_reason

            candidate.rerank_score = score
            candidate.relevance_reasoning = reasoning
            reranked_pool.append(candidate)

        # Sort descending by re-rank score; secondary sort by vector similarity
        reranked_pool.sort(key=lambda c: (c.rerank_score, c.vector_similarity), reverse=True)

        # Assign final ranks and compute rank changes
        for final_idx, cand in enumerate(reranked_pool, start=1):
            cand.final_rank = final_idx
            cand.rank_change = cand.initial_rank - cand.final_rank
            cand.is_selected = (final_idx <= top_k)

        top_k_chunks = reranked_pool[:top_k]
        self.logger.info(f"[Task 2] Re-ranking complete. Selected top {len(top_k_chunks)} chunks.")
        return reranked_pool, top_k_chunks

    def compare_rankings(
        self,
        query: str,
        initial_candidates: List[CandidateChunk],
        reranked_candidates: List[CandidateChunk],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Tasks 3 & 4: Compare before and after ordering for a sample query.
        Shows improved top results and outputs detailed metrics and comparison tables.
        """
        promoted_chunks = [c for c in reranked_candidates if c.rank_change > 0]
        demoted_chunks = [c for c in reranked_candidates if c.rank_change < 0]
        retained_top_k = [c for c in reranked_candidates if c.is_selected]

        # Top 1 comparison
        initial_top1 = initial_candidates[0] if initial_candidates else None
        reranked_top1 = reranked_candidates[0] if reranked_candidates else None

        top1_improved = (
            reranked_top1 is not None and initial_top1 is not None and
            (reranked_top1.chunk_id != initial_top1.chunk_id or reranked_top1.rerank_score > initial_top1.rerank_score)
        )

        comparison_data = {
            "query": query,
            "initial_candidate_count": len(initial_candidates),
            "final_top_k_count": top_k,
            "metrics": {
                "top_1_changed": initial_top1.chunk_id != reranked_top1.chunk_id if (initial_top1 and reranked_top1) else False,
                "initial_top_1_chunk": initial_top1.chunk_id if initial_top1 else None,
                "reranked_top_1_chunk": reranked_top1.chunk_id if reranked_top1 else None,
                "total_promotions": len(promoted_chunks),
                "total_demotions": len(demoted_chunks),
                "max_rank_promotion": max([c.rank_change for c in reranked_candidates], default=0),
                "max_rank_demotion": min([c.rank_change for c in reranked_candidates], default=0),
            },
            "top_k_selected_chunks": [c.to_dict() for c in retained_top_k],
            "all_candidates_comparison": [c.to_dict() for c in reranked_candidates]
        }

        return comparison_data

    def format_comparison_table_markdown(self, comparison_data: Dict[str, Any]) -> str:
        """
        Formats before-and-after ranking results as a clean Markdown table.
        """
        lines = []
        lines.append(f"### Query: \"{comparison_data['query']}\"\n")
        lines.append(f"- **Initial Candidate Set Size**: {comparison_data['initial_candidate_count']}")
        lines.append(f"- **Final Top-K Kept**: {comparison_data['final_top_k_count']}")
        lines.append(f"- **Top-1 Shift**: `{comparison_data['metrics']['initial_top_1_chunk']}` -> `{comparison_data['metrics']['reranked_top_1_chunk']}`\n")
        
        lines.append("| Final Rank | Initial Rank | Rank Shift | Chunk ID | Section / Doc | Vector Sim | Re-Rank Score | Status | Text Preview |")
        lines.append("|:---:|:---:|:---:|:---|:---|:---:|:---:|:---:|:---|")

        for c in comparison_data["all_candidates_comparison"]:
            shift_badge = (
                f"+{c['rank_change']}" if c['rank_change'] > 0
                else (f"{c['rank_change']}" if c['rank_change'] < 0 else "0")
            )
            status_badge = "**SELECTED (Top 3)**" if c["is_selected"] else "Filtered"
            doc_section = f"{c['metadata'].get('filename', 'doc')} ({c['metadata'].get('section', 'General')})"
            text_snippet = c["text"][:75].replace("\n", " ") + "..."
            lines.append(
                f"| **#{c['final_rank']}** | #{c['initial_rank']} | {shift_badge} | `{c['chunk_id']}` | "
                f"{doc_section} | {c['vector_similarity']:.3f} | **{c['rerank_score']:.3f}** | {status_badge} | {text_snippet} |"
            )

        return "\n".join(lines)
