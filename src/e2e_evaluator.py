"""
End-to-End RAG Evaluation Suite.

Implements Tasks 1 to 5 for evaluating the full RAG system:
- Task 1: Prepare a test set (loaded from data/e2e_test_set.json)
- Task 2: Score correctness and grounding
- Task 3: Check citation accuracy
- Task 4: Summarize quality and failures
- Task 5: Export evaluation results (for commit)
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

try:
    from llm_client import LLMClient
    from similarity_ranker import SimilarityRanker
    from chunk_embedding_pipeline import ChunkEmbeddingPipeline, EmbeddedChunk
    from filtered_search import FilteredSearchEngine, MetadataFilter
    from grounded_generator import GroundedRAGGenerator, GroundedAnswer, AccuracyAuditReport
except ImportError:
    from src.llm_client import LLMClient
    from src.similarity_ranker import SimilarityRanker
    from src.chunk_embedding_pipeline import ChunkEmbeddingPipeline, EmbeddedChunk
    from src.filtered_search import FilteredSearchEngine, MetadataFilter
    from src.grounded_generator import GroundedRAGGenerator, GroundedAnswer, AccuracyAuditReport

# ==============================================================================
# TASK 1: LABELLED E2E QUERY BENCHMARK
# ==============================================================================

@dataclass
class E2ELabelledQuery:
    query_id: str
    query: str
    category: str
    expected_chunk_ids: List[str]
    expected_answer_snippets: List[str]
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "E2ELabelledQuery":
        return cls(
            query_id=data.get("query_id", ""),
            query=data.get("query", ""),
            category=data.get("category", "Standard"),
            expected_chunk_ids=data.get("expected_chunk_ids", []),
            expected_answer_snippets=data.get("expected_answer_snippets", []),
            description=data.get("description", "")
        )

def load_e2e_queries(filepath: str = os.path.join("data", "e2e_test_set.json")) -> List[E2ELabelledQuery]:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                queries_list = data.get("queries", [])
                if queries_list:
                    return [E2ELabelledQuery.from_dict(q) for q in queries_list]
        except Exception as e:
            print(f"Error loading e2e test set: {e}")
    return []

# ==============================================================================
# CORE ENGINE: E2E EVALUATOR
# ==============================================================================

class E2EEvaluator:
    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or LLMClient()
        self.ranker = SimilarityRanker(client=self.client, metric="cosine")
        self.retriever = FilteredSearchEngine(client=self.client, ranker=self.ranker)
        self.generator = GroundedRAGGenerator(client=self.client, retriever=self.retriever)

    def score_correctness(self, answer: str, expected_snippets: List[str]) -> Dict[str, Any]:
        """
        Task 2: Scores correctness based on whether the expected key snippets are present in the answer.
        """
        answer_lower = answer.lower()
        matched = []
        missed = []
        for snippet in expected_snippets:
            if snippet.lower() in answer_lower:
                matched.append(snippet)
            else:
                missed.append(snippet)
        
        score = len(matched) / len(expected_snippets) if expected_snippets else 1.0
        return {
            "correctness_score": score,
            "matched_snippets": matched,
            "missed_snippets": missed,
            "is_fully_correct": score == 1.0
        }

    def check_citation_accuracy(self, cited_chunk_ids: List[str], expected_chunk_ids: List[str]) -> Dict[str, Any]:
        """
        Task 3: Checks whether citations point to the sources that actually support the claims.
        """
        if not expected_chunk_ids:
            # For fallback queries, we expect no citations.
            is_accurate = len(cited_chunk_ids) == 0
            return {
                "citation_score": 1.0 if is_accurate else 0.0,
                "is_accurate": is_accurate,
                "missing_expected_citations": [],
                "hallucinated_citations": cited_chunk_ids
            }
            
        cited_set = set(cited_chunk_ids)
        expected_set = set(expected_chunk_ids)
        
        missing = list(expected_set - cited_set)
        hallucinated = list(cited_set - expected_set)
        
        hits = len(expected_set.intersection(cited_set))
        score = hits / len(expected_set) if expected_set else 0.0
        
        return {
            "citation_score": score,
            "is_accurate": score == 1.0 and len(hallucinated) == 0,
            "missing_expected_citations": missing,
            "hallucinated_citations": hallucinated
        }

    def evaluate_query(
        self,
        labelled_query: E2ELabelledQuery,
        embedded_chunks: List[EmbeddedChunk]
    ) -> Dict[str, Any]:
        """
        Task 2 & 3: Run pipeline and score single query.
        """
        # 1. Retrieve
        search_res = self.retriever.search(
            query=labelled_query.query,
            embedded_chunks=embedded_chunks,
            mode="hybrid",
            top_k=3
        )
        retrieved_chunks = search_res.get("ranked_chunks", [])
        
        # 2. Generate
        if len(labelled_query.expected_chunk_ids) == 0:
            # Fallback handling expected
            grounded_ans = self.generator.generate_with_fallback_handling(
                query=labelled_query.query,
                retrieved_chunks=retrieved_chunks
            )
        else:
            grounded_ans = self.generator.generate_grounded_answer(
                query=labelled_query.query,
                retrieved_chunks=retrieved_chunks
            )

        # 3. Score Grounding (Faithfulness)
        accuracy_audit = self.generator.verify_source_accuracy(
            answer=grounded_ans.answer,
            context_chunks=retrieved_chunks
        )
        
        # 4. Score Correctness
        correctness_eval = self.score_correctness(
            answer=grounded_ans.answer,
            expected_snippets=labelled_query.expected_answer_snippets
        )
        
        # 5. Check Citation Accuracy
        citation_eval = self.check_citation_accuracy(
            cited_chunk_ids=grounded_ans.cited_chunk_ids,
            expected_chunk_ids=labelled_query.expected_chunk_ids
        )

        # 6. Diagnose Failure
        is_failure = not (correctness_eval["is_fully_correct"] and citation_eval["is_accurate"])
        failure_type = "NONE"
        if is_failure:
            if not citation_eval["is_accurate"] and len(citation_eval["missing_expected_citations"]) > 0:
                failure_type = "RETRIEVAL_OR_CITATION_FAILURE"
            elif not correctness_eval["is_fully_correct"]:
                failure_type = "GENERATION_INCOMPLETENESS"
            if len(citation_eval["hallucinated_citations"]) > 0:
                failure_type = "HALLUCINATED_CITATION"

        return {
            "query_id": labelled_query.query_id,
            "query": labelled_query.query,
            "category": labelled_query.category,
            "retrieved_chunk_ids": [c.get("chunk_id") if isinstance(c, dict) else c.chunk_id for c in retrieved_chunks],
            "generated_answer": grounded_ans.answer,
            "correctness": correctness_eval,
            "citation_accuracy": citation_eval,
            "grounding_faithfulness": {
                "score": accuracy_audit.faithfulness_score,
                "verdict": accuracy_audit.verdict
            },
            "is_failure": is_failure,
            "failure_type": failure_type
        }

    def run_evaluation_suite(
        self,
        embedded_chunks: List[EmbeddedChunk],
        queries: Optional[List[E2ELabelledQuery]] = None
    ) -> Dict[str, Any]:
        """
        Task 4: Runs comprehensive E2E evaluation and summarizes quality and failures.
        """
        test_queries = queries or load_e2e_queries()
        if not test_queries:
            return {"error": "No E2E test queries found."}

        results = []
        total_queries = len(test_queries)
        failures_count = 0
        failure_cases = []
        
        agg_correctness = 0.0
        agg_citation = 0.0
        agg_faithfulness = 0.0

        for q in test_queries:
            eval_res = self.evaluate_query(q, embedded_chunks)
            results.append(eval_res)
            
            agg_correctness += eval_res["correctness"]["correctness_score"]
            agg_citation += eval_res["citation_accuracy"]["citation_score"]
            agg_faithfulness += eval_res["grounding_faithfulness"]["score"]
            
            if eval_res["is_failure"]:
                failures_count += 1
                failure_cases.append({
                    "query_id": eval_res["query_id"],
                    "query": eval_res["query"],
                    "failure_type": eval_res["failure_type"],
                    "correctness": eval_res["correctness"],
                    "citation_accuracy": eval_res["citation_accuracy"]
                })

        mean_correctness = (agg_correctness / total_queries) * 100.0
        mean_citation = (agg_citation / total_queries) * 100.0
        mean_faithfulness = agg_faithfulness / total_queries

        summary = {
            "evaluation_metadata": {
                "total_queries_evaluated": total_queries,
                "overall_pass_rate_percentage": round(((total_queries - failures_count) / total_queries) * 100.0, 2),
                "failures_detected": failures_count
            },
            "aggregate_metrics": {
                "mean_correctness_score_percentage": round(mean_correctness, 2),
                "mean_citation_accuracy_percentage": round(mean_citation, 2),
                "mean_grounding_faithfulness_percentage": round(mean_faithfulness, 2)
            },
            "failure_inspection_summary": {
                "total_failures": failures_count,
                "failure_cases": failure_cases
            },
            "query_level_evaluations": results
        }
        return summary

    def export_evaluation_reports(
        self,
        eval_summary: Dict[str, Any],
        output_txt_path: str = os.path.join("outputs", "e2e_evaluation_summary.txt"),
        output_json_path: str = os.path.join("outputs", "e2e_evaluation_results.json")
    ) -> None:
        """
        Task 5: Produce summary reporting overall quality scores and notable failures.
        """
        os.makedirs("outputs", exist_ok=True)

        meta = eval_summary.get("evaluation_metadata", {})
        agg = eval_summary.get("aggregate_metrics", {})
        failures = eval_summary.get("failure_inspection_summary", {})

        lines = [
            "================================================================================",
            "                 E2E RAG EVALUATION SUMMARY REPORT                              ",
            "================================================================================",
            f"Total Queries Evaluated: {meta.get('total_queries_evaluated', 0)}",
            f"Overall Pass Rate:       {meta.get('overall_pass_rate_percentage', 0.0)}%",
            f"Mean Correctness Score:  {agg.get('mean_correctness_score_percentage', 0.0):.2f}%",
            f"Mean Citation Accuracy:  {agg.get('mean_citation_accuracy_percentage', 0.0):.2f}%",
            f"Mean Grounding Faith:    {agg.get('mean_grounding_faithfulness_percentage', 0.0):.2f}%",
            "",
            "--------------------------------------------------------------------------------",
            "NOTABLE FAILURES",
            "--------------------------------------------------------------------------------"
        ]

        if failures.get("total_failures", 0) == 0:
            lines.append("🎉 No failures identified! All queries passed correctness and citation checks.")
        else:
            for f in failures.get("failure_cases", []):
                lines.extend([
                    f"\nQuery ID: {f['query_id']} [{f['failure_type']}]",
                    f"Query: \"{f['query']}\"",
                    f"Correctness Missed: {f['correctness'].get('missed_snippets', [])}",
                    f"Citation Missing: {f['citation_accuracy'].get('missing_expected_citations', [])}",
                    f"Citation Hallucinated: {f['citation_accuracy'].get('hallucinated_citations', [])}",
                    "-" * 60
                ])

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(eval_summary, f, indent=2)

        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def run_e2e_evaluation_demonstration(pipeline: Optional[ChunkEmbeddingPipeline] = None) -> Dict[str, Any]:
    pipe = pipeline or ChunkEmbeddingPipeline()
    embedded_chunks, _ = pipe.run_pipeline(output_txt_path=None, output_json_path=None)
    evaluator = E2EEvaluator(client=pipe.client)
    queries = load_e2e_queries()
    
    summary = evaluator.run_evaluation_suite(embedded_chunks=embedded_chunks, queries=queries)
    evaluator.export_evaluation_reports(summary)
    return summary

if __name__ == "__main__":
    print("Executing E2E Evaluation Suite...")
    summary = run_e2e_evaluation_demonstration()
    print("Done. Check outputs/e2e_evaluation_summary.txt for details.")
