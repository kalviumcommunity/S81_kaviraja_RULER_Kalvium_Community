"""
Retrieval Evaluation Suite for RAG Application.

Implements Tasks 1 to 5:
- Task 1: Prepare Labelled Queries: Load and manage ground-truth labelled query benchmark.
- Task 2: Measure Recall@K: Evaluate exact set Recall@K and Hit Rate at multiple depths.
- Task 3: Report Precision & Quality Signals: Measure Precision@K, MRR, F1@K, and graded relevance scores.
- Task 4: Inspect Failures: Categorize failure root causes (negation blindspots, cross-section distraction, boundary issues).
- Task 5: Export & Commit Results: Generate reproducible evaluation metrics and failure inspection reports.
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Set

try:
    from llm_client import LLMClient
    from similarity_ranker import SimilarityRanker
    from chunk_embedding_pipeline import ChunkEmbeddingPipeline, EmbeddedChunk
    from filtered_search import FilteredSearchEngine, MetadataFilter
except ImportError:
    from src.llm_client import LLMClient
    from src.similarity_ranker import SimilarityRanker
    from src.chunk_embedding_pipeline import ChunkEmbeddingPipeline, EmbeddedChunk
    from src.filtered_search import FilteredSearchEngine, MetadataFilter


# ==============================================================================
# TASK 1: LABELLED QUERY BENCHMARK
# ==============================================================================

@dataclass
class LabelledQuery:
    """
    Data model representing a gold-standard ground-truth labelled evaluation query.
    """
    query_id: str
    query: str
    category: str
    target_section: str
    expected_chunk_ids: List[str]
    min_acceptable_rank: int = 1
    difficulty: str = "Standard"
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LabelledQuery":
        return cls(
            query_id=data.get("query_id", ""),
            query=data.get("query", ""),
            category=data.get("category", "Standard Relevance"),
            target_section=data.get("target_section", ""),
            expected_chunk_ids=data.get("expected_chunk_ids", []),
            min_acceptable_rank=data.get("min_acceptable_rank", 1),
            difficulty=data.get("difficulty", "Standard"),
            description=data.get("description", "")
        )


def load_labelled_queries(
    filepath: Optional[str] = os.path.join("data", "labelled_queries.json")
) -> List[LabelledQuery]:
    """
    Task 1: Loads ground-truth labelled queries from JSON dataset or returns default benchmark.
    """
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                queries_list = data.get("queries", [])
                if queries_list:
                    return [LabelledQuery.from_dict(q) for q in queries_list]
        except Exception:
            pass

    # Built-in fallback benchmark dataset
    return [
        LabelledQuery(
            query_id="Q-001",
            query="How are suspicious transactions and beneficiary country risk scores monitored under AML directives?",
            category="Standard Relevance",
            target_section="Section 1: Executive Summary & Overview",
            expected_chunk_ids=["sample_banking_regulation_txt#chunk_001"],
            min_acceptable_rank=1,
            description="AML risk monitoring query targeting Section 1 chunk."
        ),
        LabelledQuery(
            query_id="Q-002",
            query="What minimum Tier 1 capital adequacy ratio is required under Basel IV?",
            category="Standard Relevance",
            target_section="Section 2: Capital Reserves & Liquidity Ratios",
            expected_chunk_ids=["sample_banking_regulation_txt#chunk_002"],
            min_acceptable_rank=1,
            description="Basel IV Tier 1 capital query targeting Section 2 chunk."
        ),
        LabelledQuery(
            query_id="Q-003",
            query="What are the rules and approval thresholds for high-value transaction payments?",
            category="Standard Relevance",
            target_section="Section 3: High-Value Transaction Authorization Thresholds",
            expected_chunk_ids=[
                "sample_banking_regulation_txt#chunk_003",
                "sample_banking_regulation_txt#chunk_004"
            ],
            min_acceptable_rank=2,
            description="Payment threshold query targeting Section 3 authorization chunks."
        ),
        LabelledQuery(
            query_id="Q-004",
            query="Which vendor disbursements do NOT require unanimous board approval?",
            category="Negation Blindspot (Known Failure)",
            target_section="Section 3: High-Value Transaction Authorization Thresholds",
            expected_chunk_ids=["sample_banking_regulation_txt#chunk_003"],
            min_acceptable_rank=1,
            description="Tests negation blindspot ('NOT'). Expected chunk specifies under $50k payments."
        ),
        LabelledQuery(
            query_id="Q-005",
            query="What audit procedures and compliance checks are required for transaction authorization?",
            category="Cross-Section Lexical Distractor",
            target_section="Section 3: High-Value Transaction Authorization Thresholds",
            expected_chunk_ids=[
                "sample_banking_regulation_txt#chunk_003",
                "sample_banking_regulation_txt#chunk_004"
            ],
            min_acceptable_rank=2,
            description="Cross-section keyword distraction across AML and payments."
        ),
        LabelledQuery(
            query_id="Q-006",
            query="How often must institutions calculate and submit the Liquidity Coverage Ratio (LCR)?",
            category="Specific Entity / Threshold",
            target_section="Section 2: Capital Reserves & Liquidity Ratios",
            expected_chunk_ids=["sample_banking_regulation_txt#chunk_002"],
            min_acceptable_rank=1,
            description="LCR calculation schedule query targeting Section 2."
        ),
        LabelledQuery(
            query_id="Q-007",
            query="What consequences follow a failure to obtain board authorization for high-value expenditures?",
            category="Boundary Consequence Clause",
            target_section="Section 3: High-Value Transaction Authorization Thresholds",
            expected_chunk_ids=["sample_banking_regulation_txt#chunk_004"],
            min_acceptable_rank=1,
            description="Tests penalty clause in trailing chunk #4."
        ),
        LabelledQuery(
            query_id="Q-008",
            query="What automated screening protocols verify transaction velocity and entity sanction status?",
            category="Semantic Paraphrase",
            target_section="Section 1: Executive Summary & Overview",
            expected_chunk_ids=["sample_banking_regulation_txt#chunk_001"],
            min_acceptable_rank=1,
            description="Paraphrased query targeting Section 1 AML systems."
        ),
    ]


# ==============================================================================
# TASKS 2 & 3: RECALL, PRECISION, AND QUALITY METRICS
# ==============================================================================

def calculate_recall_at_k(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str],
    k: int
) -> float:
    """
    Task 2: Computes Recall@K:
      Recall@K = |Retrieved_K ∩ Expected| / |Expected|
    """
    if not expected_chunk_ids:
        return 0.0
    top_k_retrieved = set(retrieved_chunk_ids[:k])
    expected_set = set(expected_chunk_ids)
    hits = len(top_k_retrieved.intersection(expected_set))
    return round(hits / len(expected_set), 4)


def calculate_hit_at_k(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str],
    k: int
) -> int:
    """
    Task 2: Computes Hit@K (Binary hit: 1 if at least one relevant chunk in top K, else 0).
    """
    top_k_retrieved = set(retrieved_chunk_ids[:k])
    expected_set = set(expected_chunk_ids)
    return 1 if len(top_k_retrieved.intersection(expected_set)) > 0 else 0


def calculate_precision_at_k(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str],
    k: int
) -> float:
    """
    Task 3: Computes Precision@K:
      Precision@K = |Retrieved_K ∩ Expected| / K
    """
    if k <= 0:
        return 0.0
    top_k_retrieved = retrieved_chunk_ids[:k]
    expected_set = set(expected_chunk_ids)
    hits = sum(1 for cid in top_k_retrieved if cid in expected_set)
    return round(hits / k, 4)


def calculate_reciprocal_rank(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str]
) -> float:
    """
    Task 3: Computes Reciprocal Rank (1 / rank of first relevant chunk, or 0.0 if not found).
    """
    expected_set = set(expected_chunk_ids)
    for idx, cid in enumerate(retrieved_chunk_ids, 1):
        if cid in expected_set:
            return round(1.0 / idx, 4)
    return 0.0


def calculate_f1_score(precision: float, recall: float) -> float:
    """Computes harmonic mean F1 score from precision and recall."""
    if (precision + recall) == 0.0:
        return 0.0
    return round(2.0 * (precision * recall) / (precision + recall), 4)


def assign_graded_relevance(
    chunk_id: str,
    expected_chunk_ids: List[str],
    target_section: str,
    chunk_metadata: Dict[str, Any]
) -> int:
    """
    Task 3 Quality Signal: Graded relevance scoring:
    2 = Highly Relevant (exact expected chunk)
    1 = Partially Relevant (same target section, but secondary chunk)
    0 = Irrelevant (different section or unrelated content)
    """
    if chunk_id in expected_chunk_ids:
        return 2
    section = chunk_metadata.get("section", "")
    if target_section and (target_section.lower() in section.lower() or section.lower() in target_section.lower()):
        return 1
    return 0


# ==============================================================================
# TASK 4: FAILURE INSPECTION & ROOT CAUSE DIAGNOSIS
# ==============================================================================

@dataclass
class FailureInspectionReport:
    """
    Data model capturing root cause diagnosis for failed or low-scoring query retrievals.
    """
    query_id: str
    query: str
    category: str
    is_failure: bool
    top_rank_achieved: int
    min_acceptable_rank: int
    actual_top_chunk_id: str
    actual_top_section: str
    expected_chunk_ids: List[str]
    expected_section: str
    failure_type: str
    root_cause: str
    pipeline_remediation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FailureInspector:
    """
    Task 4: Automated diagnostic inspector analyzing failed and borderline retrieval cases.
    Identifies root causes across embedding negation blindspots, cross-section lexical distraction,
    chunk boundary cutoffs, missing metadata filters, and vocabulary mismatches.
    """

    @staticmethod
    def inspect_query_result(
        labelled_query: LabelledQuery,
        ranked_chunks: List[Dict[str, Any]],
        retrieved_ids: List[str]
    ) -> FailureInspectionReport:
        """
        Diagnoses whether a query retrieval failed to satisfy the acceptable rank threshold
        and determines the underlying failure mechanism.
        """
        expected_set = set(labelled_query.expected_chunk_ids)
        top_rank_achieved = 999
        for idx, cid in enumerate(retrieved_ids, 1):
            if cid in expected_set:
                top_rank_achieved = idx
                break

        is_failure = top_rank_achieved > labelled_query.min_acceptable_rank

        actual_top = ranked_chunks[0] if ranked_chunks else {}
        actual_top_id = actual_top.get("chunk_id", "NONE")
        actual_top_sec = actual_top.get("metadata", {}).get("section", "Unknown")

        if not is_failure:
            return FailureInspectionReport(
                query_id=labelled_query.query_id,
                query=labelled_query.query,
                category=labelled_query.category,
                is_failure=False,
                top_rank_achieved=top_rank_achieved,
                min_acceptable_rank=labelled_query.min_acceptable_rank,
                actual_top_chunk_id=actual_top_id,
                actual_top_section=actual_top_sec,
                expected_chunk_ids=labelled_query.expected_chunk_ids,
                expected_section=labelled_query.target_section,
                failure_type="NONE_PASS",
                root_cause="Relevant chunk retrieved within acceptable rank threshold.",
                pipeline_remediation="No remediation required."
            )

        # Diagnose root cause of failure
        q_lower = labelled_query.query.lower()

        # 1. Negation Blindspot Diagnosis
        if "not" in q_lower or "without" in q_lower or "never" in q_lower or "except" in q_lower:
            failure_type = "EMBEDDING_NEGATION_BLINDSPOT"
            root_cause = (
                "Dense embedding models map queries by topic keywords and fail to invert vector direction "
                "for logical negation. The model matched positive topic tokens ('disbursements', 'board approval') "
                f"and mistakenly ranked '{actual_top_id}' at rank #1."
            )
            remediation = (
                "Implement query transformation/rewriting to rephrase negative constraints, "
                "or apply structured metadata filtering on authorization tiers prior to vector search."
            )

        # 2. Cross-Section Lexical Distractor Diagnosis
        elif actual_top_sec != labelled_query.target_section and any(
            w in q_lower for w in ["audit", "compliance", "report", "authoriz"]
        ):
            failure_type = "CROSS_SECTION_LEXICAL_DISTRACTION"
            root_cause = (
                f"Shared vocabulary ('compliance', 'audit') between Section 1 and Section 3 caused out-of-scope "
                f"chunk '{actual_top_id}' from '{actual_top_sec}' to outrank target chunk '{labelled_query.expected_chunk_ids[0]}' "
                f"from '{labelled_query.target_section}'."
            )
            remediation = (
                "Apply pre-retrieval metadata filtering scoped to target document section, or utilize hybrid search "
                "with exact phrase matching to penalize cross-section false positives."
            )

        # 3. Chunk Boundary Fragmentation Diagnosis
        elif labelled_query.category == "Boundary Consequence Clause" or (
            actual_top_id in ["sample_banking_regulation_txt#chunk_003", "sample_banking_regulation_txt#chunk_004"]
            and len(labelled_query.expected_chunk_ids) > 1
        ):
            failure_type = "CHUNK_BOUNDARY_FRAGMENTATION"
            root_cause = (
                "Relevant context was split across adjacent chunk boundaries during token-aware chunking. "
                "The isolated chunk lacked the complete subject clause, reducing its semantic similarity score."
            )
            remediation = (
                "Increase token overlap between adjacent chunks (e.g. from 64 to 128 tokens) "
                "or implement parent-document / hierarchical chunk retrieval."
            )

        # 4. General Semantic Distance / Vocabulary Mismatch
        else:
            failure_type = "VOCABULARY_OR_EMBEDDING_MISMATCH"
            root_cause = (
                "Query phrasing had a wide semantic distance from the exact terminology used in the regulatory corpus, "
                "causing the embedding model to assign suboptimal similarity."
            )
            remediation = (
                "Expand queries using LLM query expansion (HyDE) or inject domain-specific synonyms into hybrid search."
            )

        return FailureInspectionReport(
            query_id=labelled_query.query_id,
            query=labelled_query.query,
            category=labelled_query.category,
            is_failure=True,
            top_rank_achieved=top_rank_achieved,
            min_acceptable_rank=labelled_query.min_acceptable_rank,
            actual_top_chunk_id=actual_top_id,
            actual_top_section=actual_top_sec,
            expected_chunk_ids=labelled_query.expected_chunk_ids,
            expected_section=labelled_query.target_section,
            failure_type=failure_type,
            root_cause=root_cause,
            pipeline_remediation=remediation
        )


# ==============================================================================
# MAIN ENGINE: RETRIEVAL EVALUATOR
# ==============================================================================

class RetrievalEvaluator:
    """
    Evaluation Engine for measuring Recall@K, Precision@K, MRR, Hit Rate,
    and conducting systematic failure analysis across retrieval pipelines.
    """

    def __init__(
        self,
        ranker: Optional[SimilarityRanker] = None,
        filtered_engine: Optional[FilteredSearchEngine] = None,
        client: Optional[LLMClient] = None
    ):
        self.ranker = ranker or SimilarityRanker(client=client, metric="cosine")
        self.client = self.ranker.client
        self.filtered_engine = filtered_engine or FilteredSearchEngine(ranker=self.ranker, client=self.client)
        self.logger = self.client.logger

    def evaluate_query(
        self,
        labelled_query: LabelledQuery,
        embedded_chunks: List[EmbeddedChunk],
        mode: str = "vector",
        metadata_filter: Optional[MetadataFilter] = None,
        k_values: List[int] = [1, 2, 3, 5]
    ) -> Dict[str, Any]:
        """
        Tasks 2, 3 & 4: Evaluates a single labelled query against corpus chunks,
        measuring Recall@K, Precision@K, Hit@K, MRR, and diagnosing failure modes.
        """
        # Execute retrieval
        max_k = max(k_values)
        if metadata_filter is not None or mode != "vector":
            search_out = self.filtered_engine.search(
                query=labelled_query.query,
                embedded_chunks=embedded_chunks,
                metadata_filter=metadata_filter,
                mode=mode,
                alpha=0.6,
                top_k=max_k
            )
            ranked_chunks = search_out.get("ranked_chunks", [])
        else:
            search_out = self.ranker.rank_chunks(
                query=labelled_query.query,
                embedded_chunks=embedded_chunks,
                metric="cosine",
                top_k=max_k
            )
            ranked_chunks = search_out.get("ranked_chunks", [])

        retrieved_ids = [c["chunk_id"] for c in ranked_chunks]

        # Calculate metrics across K
        metrics_by_k: Dict[str, Dict[str, float]] = {}
        for k in k_values:
            rec = calculate_recall_at_k(retrieved_ids, labelled_query.expected_chunk_ids, k)
            prec = calculate_precision_at_k(retrieved_ids, labelled_query.expected_chunk_ids, k)
            hit = calculate_hit_at_k(retrieved_ids, labelled_query.expected_chunk_ids, k)
            f1 = calculate_f1_score(prec, rec)
            metrics_by_k[f"k_{k}"] = {
                "recall": rec,
                "precision": prec,
                "hit_rate": hit,
                "f1_score": f1
            }

        reciprocal_rank = calculate_reciprocal_rank(retrieved_ids, labelled_query.expected_chunk_ids)

        # Graded relevance scores
        graded_scores = [
            assign_graded_relevance(c["chunk_id"], labelled_query.expected_chunk_ids, labelled_query.target_section, c.get("metadata", {}))
            for c in ranked_chunks
        ]
        avg_quality_signal = (sum(graded_scores) / len(graded_scores)) if graded_scores else 0.0

        # Task 4: Failure inspection
        failure_report = FailureInspector.inspect_query_result(labelled_query, ranked_chunks, retrieved_ids)

        return {
            "query_id": labelled_query.query_id,
            "query": labelled_query.query,
            "category": labelled_query.category,
            "difficulty": labelled_query.difficulty,
            "expected_chunk_ids": labelled_query.expected_chunk_ids,
            "target_section": labelled_query.target_section,
            "retrieved_chunk_ids": retrieved_ids,
            "reciprocal_rank": reciprocal_rank,
            "metrics_by_k": metrics_by_k,
            "quality_signals": {
                "graded_relevance_scores": graded_scores,
                "average_graded_relevance": round(avg_quality_signal, 4)
            },
            "failure_analysis": failure_report.to_dict()
        }

    def run_evaluation_suite(
        self,
        embedded_chunks: List[EmbeddedChunk],
        queries: Optional[List[LabelledQuery]] = None,
        mode: str = "vector",
        metadata_filter: Optional[MetadataFilter] = None,
        k_values: List[int] = [1, 2, 3, 5]
    ) -> Dict[str, Any]:
        """
        Tasks 2, 3 & 4: Runs comprehensive evaluation across all labelled benchmark queries
        and computes corpus-wide aggregate metrics.
        """
        test_queries = queries or load_labelled_queries()
        query_results = []

        total_queries = len(test_queries)
        if total_queries == 0:
            return {"error": "No queries provided for evaluation."}

        # Accumulators for aggregate metrics
        agg_recall = {f"k_{k}": 0.0 for k in k_values}
        agg_precision = {f"k_{k}": 0.0 for k in k_values}
        agg_hit = {f"k_{k}": 0 for k in k_values}
        agg_f1 = {f"k_{k}": 0.0 for k in k_values}
        agg_mrr = 0.0
        agg_quality = 0.0

        failures_count = 0
        failure_cases: List[Dict[str, Any]] = []

        for q in test_queries:
            q_eval = self.evaluate_query(
                labelled_query=q,
                embedded_chunks=embedded_chunks,
                mode=mode,
                metadata_filter=metadata_filter,
                k_values=k_values
            )
            query_results.append(q_eval)

            for k in k_values:
                k_key = f"k_{k}"
                agg_recall[k_key] += q_eval["metrics_by_k"][k_key]["recall"]
                agg_precision[k_key] += q_eval["metrics_by_k"][k_key]["precision"]
                agg_hit[k_key] += q_eval["metrics_by_k"][k_key]["hit_rate"]
                agg_f1[k_key] += q_eval["metrics_by_k"][k_key]["f1_score"]

            agg_mrr += q_eval["reciprocal_rank"]
            agg_quality += q_eval["quality_signals"]["average_graded_relevance"]

            fail_rep = q_eval["failure_analysis"]
            if fail_rep["is_failure"]:
                failures_count += 1
                failure_cases.append(fail_rep)

        # Average aggregate metrics
        mean_metrics = {
            f"k_{k}": {
                "mean_recall": round(agg_recall[f"k_{k}"] / total_queries, 4),
                "mean_precision": round(agg_precision[f"k_{k}"] / total_queries, 4),
                "hit_rate_percentage": round((agg_hit[f"k_{k}"] / total_queries) * 100.0, 2),
                "mean_f1_score": round(agg_f1[f"k_{k}"] / total_queries, 4)
            }
            for k in k_values
        }

        mrr_score = round(agg_mrr / total_queries, 4)
        mean_quality = round(agg_quality / total_queries, 4)
        pass_rate_pct = round(((total_queries - failures_count) / total_queries) * 100.0, 2)

        summary = {
            "evaluation_metadata": {
                "total_queries_evaluated": total_queries,
                "retrieval_mode": mode,
                "filter_applied": metadata_filter.to_dict() if metadata_filter else None,
                "k_depths_evaluated": k_values,
                "overall_pass_rate_percentage": pass_rate_pct,
                "failures_detected": failures_count
            },
            "aggregate_metrics": {
                "mean_reciprocal_rank_mrr": mrr_score,
                "mean_graded_quality_signal": mean_quality,
                "metrics_by_depth": mean_metrics
            },
            "query_level_evaluations": query_results,
            "failure_inspection_summary": {
                "total_failures": failures_count,
                "failure_cases": failure_cases
            }
        }

        return summary

    # ==============================================================================
    # TASK 5: EXPORT EVALUATION ARTIFACTS
    # ==============================================================================

    def export_evaluation_reports(
        self,
        eval_summary: Dict[str, Any],
        output_txt_path: str = os.path.join("outputs", "retrieval_evaluation_report.txt"),
        output_json_path: str = os.path.join("outputs", "retrieval_evaluation_results.json"),
        failure_txt_path: str = os.path.join("outputs", "retrieval_failure_analysis.txt"),
        failure_json_path: str = os.path.join("outputs", "retrieval_failure_analysis.json")
    ) -> Dict[str, Any]:
        """
        Task 5: Produce and commit structured JSON metrics, human-readable evaluation summary,
        and failure diagnosis reports.
        """
        meta = eval_summary.get("evaluation_metadata", {})
        agg = eval_summary.get("aggregate_metrics", {})
        depth_metrics = agg.get("metrics_by_depth", {})
        fail_summary = eval_summary.get("failure_inspection_summary", {})

        # 1. Main Evaluation Report Text
        lines = [
            "================================================================================",
            "                 RAG RETRIEVAL EVALUATION BENCHMARK REPORT                      ",
            "================================================================================",
            f"Retrieval Mode: {meta.get('retrieval_mode', 'vector').upper()}",
            f"Total Queries Evaluated: {meta.get('total_queries_evaluated', 0)}",
            f"Mean Reciprocal Rank (MRR): {agg.get('mean_reciprocal_rank_mrr', 0.0):.4f}",
            f"Benchmark Pass Rate: {meta.get('overall_pass_rate_percentage', 0.0)}%",
            f"Average Graded Quality Signal: {agg.get('mean_graded_quality_signal', 0.0):.4f} / 2.00",
            "",
            "--------------------------------------------------------------------------------",
            "AGGREGATE METRICS ACROSS RETRIEVAL DEPTH (K)",
            "--------------------------------------------------------------------------------",
            f"{'Depth (K)':<12} | {'Recall@K':<12} | {'Precision@K':<14} | {'Hit Rate %':<12} | {'F1@K':<10}",
            "-" * 70,
        ]

        for k_key, vals in depth_metrics.items():
            depth = k_key.replace("k_", "K=")
            lines.append(
                f"{depth:<12} | {vals['mean_recall']:<12.4f} | {vals['mean_precision']:<14.4f} | {vals['hit_rate_percentage']:<11.1f}% | {vals['mean_f1_score']:<10.4f}"
            )

        lines.extend([
            "",
            "--------------------------------------------------------------------------------",
            "QUERY-BY-QUERY RETRIEVAL EVALUATION",
            "--------------------------------------------------------------------------------"
        ])

        for q in eval_summary.get("query_level_evaluations", []):
            fail = q["failure_analysis"]
            status_tag = "[PASS]" if not fail["is_failure"] else f"[FAIL - {fail['failure_type']}]"
            k1_m = q["metrics_by_k"].get("k_1", {})
            k3_m = q["metrics_by_k"].get("k_3", {})
            lines.extend([
                f"\n{q['query_id']}: \"{q['query']}\" {status_tag}",
                f"  Category: {q['category']} | Target Section: {q['target_section']}",
                f"  Expected Chunks: {q['expected_chunk_ids']}",
                f"  Retrieved Chunks: {q['retrieved_chunk_ids'][:3]}",
                f"  MRR: {q['reciprocal_rank']:.4f} | Recall@1: {k1_m.get('recall', 0.0):.2f} | Precision@1: {k1_m.get('precision', 0.0):.2f} | Recall@3: {k3_m.get('recall', 0.0):.2f} | Precision@3: {k3_m.get('precision', 0.0):.2f}",
                f"  Graded Relevance Scores: {q['quality_signals']['graded_relevance_scores'][:3]}",
                "-" * 40
            ])

        report_txt_content = "\n".join(lines) + "\n"

        # 2. Failure Analysis Text Report
        fail_lines = [
            "================================================================================",
            "                 RETRIEVAL FAILURE & DIAGNOSTIC INSPECTION REPORT               ",
            "================================================================================",
            f"Total Queries Evaluated: {meta.get('total_queries_evaluated', 0)}",
            f"Failed / Low-Scoring Queries: {fail_summary.get('total_failures', 0)}",
            f"Benchmark Pass Rate: {meta.get('overall_pass_rate_percentage', 0.0)}%",
            "",
            "--------------------------------------------------------------------------------",
            "IDENTIFIED FAILURE CASES & ROOT CAUSE INSPECTION",
            "--------------------------------------------------------------------------------",
        ]

        if not fail_summary.get("failure_cases"):
            fail_lines.append("\n🎉 No failures identified! All queries satisfied acceptable rank thresholds.")
        else:
            for f_case in fail_summary.get("failure_cases", []):
                fail_lines.extend([
                    f"\nQuery ID: {f_case['query_id']} [{f_case['failure_type']}]",
                    f"Query: \"{f_case['query']}\"",
                    f"Category: {f_case['category']}",
                    f"Expected Section: {f_case['expected_section']} (Expected Chunks: {f_case['expected_chunk_ids']})",
                    f"Actual Top Rank #1: {f_case['actual_top_chunk_id']} (Section: {f_case['actual_top_section']})",
                    f"Rank Achieved for Target Chunk: #{f_case['top_rank_achieved']} (Acceptable: #{f_case['min_acceptable_rank']})",
                    "",
                    "Root Cause Diagnosis:",
                    f"  {f_case['root_cause']}",
                    "",
                    "Pipeline Remediation Recommendation:",
                    f"  {f_case['pipeline_remediation']}",
                    "-" * 60
                ])

        fail_lines.append("================================================================================\n")
        fail_txt_content = "\n".join(fail_lines)

        # Write files
        if output_txt_path:
            os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(report_txt_content)

        if output_json_path:
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(eval_summary, f, indent=2)

        if failure_txt_path:
            os.makedirs(os.path.dirname(failure_txt_path), exist_ok=True)
            with open(failure_txt_path, "w", encoding="utf-8") as f:
                f.write(fail_txt_content)

        if failure_json_path:
            os.makedirs(os.path.dirname(failure_json_path), exist_ok=True)
            with open(failure_json_path, "w", encoding="utf-8") as f:
                json.dump(fail_summary, f, indent=2)

        return {
            "eval_summary": eval_summary,
            "output_txt": output_txt_path,
            "output_json": output_json_path,
            "failure_txt": failure_txt_path,
            "failure_json": failure_json_path
        }


# ==============================================================================
# SAMPLE EXECUTION RUNNER
# ==============================================================================

def run_retrieval_evaluation_demonstration(
    pipeline: Optional[ChunkEmbeddingPipeline] = None
) -> Dict[str, Any]:
    """
    Executes an end-to-end evaluation suite on the banking regulation corpus.
    Compares Pure Vector Search against Filtered/Hybrid Search.
    """
    pipe = pipeline or ChunkEmbeddingPipeline()
    embedded_chunks, _ = pipe.run_pipeline(output_txt_path=None, output_json_path=None)

    evaluator = RetrievalEvaluator(client=pipe.client)
    queries = load_labelled_queries()

    # 1. Evaluate Pure Vector Search
    vector_eval = evaluator.run_evaluation_suite(
        embedded_chunks=embedded_chunks,
        queries=queries,
        mode="vector",
        k_values=[1, 2, 3, 5]
    )

    # 2. Evaluate Hybrid Search
    hybrid_eval = evaluator.run_evaluation_suite(
        embedded_chunks=embedded_chunks,
        queries=queries,
        mode="hybrid",
        k_values=[1, 2, 3, 5]
    )

    combined_summary = {
        "vector_search_evaluation": vector_eval,
        "hybrid_search_evaluation": hybrid_eval,
        "benchmark_comparison": {
            "mrr_comparison": {
                "vector_search": vector_eval["aggregate_metrics"]["mean_reciprocal_rank_mrr"],
                "hybrid_search": hybrid_eval["aggregate_metrics"]["mean_reciprocal_rank_mrr"],
            },
            "recall_at_1_comparison": {
                "vector_search": vector_eval["aggregate_metrics"]["metrics_by_depth"]["k_1"]["mean_recall"],
                "hybrid_search": hybrid_eval["aggregate_metrics"]["metrics_by_depth"]["k_1"]["mean_recall"],
            },
            "precision_at_1_comparison": {
                "vector_search": vector_eval["aggregate_metrics"]["metrics_by_depth"]["k_1"]["mean_precision"],
                "hybrid_search": hybrid_eval["aggregate_metrics"]["metrics_by_depth"]["k_1"]["mean_precision"],
            },
            "pass_rate_comparison": {
                "vector_search": vector_eval["evaluation_metadata"]["overall_pass_rate_percentage"],
                "hybrid_search": hybrid_eval["evaluation_metadata"]["overall_pass_rate_percentage"],
            },
            "failures_count": {
                "vector_search": vector_eval["failure_inspection_summary"]["total_failures"],
                "hybrid_search": hybrid_eval["failure_inspection_summary"]["total_failures"],
            }
        }
    }

    # 3. Export reports
    evaluator.export_evaluation_reports(
        eval_summary=vector_eval,
        output_txt_path=os.path.join("outputs", "retrieval_evaluation_report.txt"),
        output_json_path=os.path.join("outputs", "retrieval_evaluation_results.json"),
        failure_txt_path=os.path.join("outputs", "retrieval_failure_analysis.txt"),
        failure_json_path=os.path.join("outputs", "retrieval_failure_analysis.json")
    )

    return combined_summary


if __name__ == "__main__":
    combined = run_retrieval_evaluation_demonstration()
    vec_summary = combined["vector_search_evaluation"]
    hyb_summary = combined["hybrid_search_evaluation"]
    comp = combined["benchmark_comparison"]

    print("\n==================================================")
    print("      RETRIEVAL EVALUATION SUITE EXECUTED         ")
    print("==================================================")
    print(f"Total Queries Evaluated: {vec_summary['evaluation_metadata']['total_queries_evaluated']}")
    print("\n--- PURE VECTOR SEARCH ---")
    print(f"Pass Rate: {vec_summary['evaluation_metadata']['overall_pass_rate_percentage']}%")
    print(f"MRR:       {vec_summary['aggregate_metrics']['mean_reciprocal_rank_mrr']:.4f}")
    d_v = vec_summary["aggregate_metrics"]["metrics_by_depth"]
    print(f"Recall@1:  {d_v['k_1']['mean_recall']:.4f} | Precision@1: {d_v['k_1']['mean_precision']:.4f}")
    print(f"Recall@3:  {d_v['k_3']['mean_recall']:.4f} | Precision@3: {d_v['k_3']['mean_precision']:.4f}")
    print(f"Failures:  {vec_summary['failure_inspection_summary']['total_failures']}")

    print("\n--- HYBRID SEARCH ---")
    print(f"Pass Rate: {hyb_summary['evaluation_metadata']['overall_pass_rate_percentage']}%")
    print(f"MRR:       {hyb_summary['aggregate_metrics']['mean_reciprocal_rank_mrr']:.4f}")
    d_h = hyb_summary["aggregate_metrics"]["metrics_by_depth"]
    print(f"Recall@1:  {d_h['k_1']['mean_recall']:.4f} | Precision@1: {d_h['k_1']['mean_precision']:.4f}")
    print(f"Recall@3:  {d_h['k_3']['mean_recall']:.4f} | Precision@3: {d_h['k_3']['mean_precision']:.4f}")
    print(f"Failures:  {hyb_summary['failure_inspection_summary']['total_failures']}")
    print("==================================================")
