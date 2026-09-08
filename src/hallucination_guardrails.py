"""
Hallucination Guardrails & Refusal Handling Engine (Tasks 1 to 5).

Implements:
- Task 1: Detect weak retrieval using signals (empty results, low similarity score, too few chunks above threshold).
- Task 2: Return a safe refusal ("I don't know" / standardized refusal) when context is weak or unsupported.
- Task 3: Multi-criteria relevance thresholds and retrieval-quality checks to decide when to refuse.
- Task 4: Preserve confident, grounded answers with full source citations when strong supporting context exists.
- Task 5: Export structured JSON and human-readable artifacts showing both refusal and confident answer cases.
"""

import os
import re
import sys
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union

try:
    from llm_client import LLMClient
    from context_injection import ContextInjector, TokenBudgetConfig, SourceMarkerStyle
    from similarity_ranker import cosine_similarity
except ImportError:
    from src.llm_client import LLMClient
    from src.context_injection import ContextInjector, TokenBudgetConfig, SourceMarkerStyle
    from src.similarity_ranker import cosine_similarity


@dataclass
class GuardrailConfig:
    """
    Configuration for retrieval quality signals and refusal decision thresholds (Task 3).
    """
    min_similarity_threshold: float = 0.35      # Minimum top similarity score required to proceed
    min_chunks_above_threshold: int = 1         # Minimum count of chunks meeting threshold
    min_keyword_overlap_ratio: float = 0.15     # Minimum lexical overlap ratio with query terms
    min_context_character_length: int = 40      # Minimum length of non-whitespace context text
    standard_refusal_message: str = (
        "I do not have sufficient information in the provided knowledge base to answer this question accurately."
    )


@dataclass
class RetrievalQualitySignals:
    """
    Calculated quality signals from retrieval candidates (Task 1).
    """
    total_chunks_retrieved: int
    top_similarity_score: float
    mean_top_k_score: float
    chunks_above_threshold: int
    keyword_overlap_ratio: float
    total_context_chars: int
    is_empty_retrieval: bool
    is_low_similarity: bool
    is_insufficient_chunks: bool
    is_weak_lexical_alignment: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GuardrailDecision:
    """
    Decision outcome from the retrieval quality evaluation (Task 1 & Task 3).
    """
    should_refuse: bool
    verdict: str                                # "SAFE_REFUSAL" or "PROCEED_CONFIDENT_ANSWER"
    refusal_reasons: List[str]                  # List of failed quality checks
    primary_reason: Optional[str]
    confidence_score: float
    quality_signals: RetrievalQualitySignals

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_refuse": self.should_refuse,
            "verdict": self.verdict,
            "refusal_reasons": self.refusal_reasons,
            "primary_reason": self.primary_reason,
            "confidence_score": round(self.confidence_score, 4),
            "quality_signals": self.quality_signals.to_dict(),
        }


@dataclass
class GuardrailResult:
    """
    End-to-end execution result for a query processed through the guardrails (Task 2 & Task 4).
    """
    query: str
    decision: GuardrailDecision
    is_refusal: bool
    final_answer: str
    cited_sources: List[Dict[str, Any]] = field(default_factory=list)
    raw_context_text: str = ""
    token_usage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "is_refusal": self.is_refusal,
            "verdict": self.decision.verdict,
            "final_answer": self.final_answer,
            "cited_sources": self.cited_sources,
            "token_usage": self.token_usage,
            "decision": self.decision.to_dict(),
        }


class HallucinationGuardrail:
    """
    Hallucination Guardrail and Retrieval-Quality Assessment Engine.
    
    Evaluates retrieval signals, triggers safe refusals for weak or irrelevant context,
    and preserves confident grounded answers when strong evidence is retrieved.
    """

    def __init__(
        self,
        config: Optional[GuardrailConfig] = None,
        llm_client: Optional[LLMClient] = None,
        context_injector: Optional[ContextInjector] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config or GuardrailConfig()
        self.llm_client = llm_client or LLMClient()
        self.injector = context_injector or ContextInjector()
        self.logger = logger or logging.getLogger("HallucinationGuardrail")

    def _extract_query_keywords(self, query: str) -> List[str]:
        """Extracts significant keywords from query ignoring common stopwords."""
        stopwords = {
            "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "the", "a", "an", "and", "or", "but", "if", "then",
            "to", "of", "for", "with", "about", "in", "on", "at", "by", "from", "up",
            "into", "over", "after", "can", "could", "should", "would", "must", "any"
        }
        raw_tokens = re.findall(r"\$?\d[\d,]*%?|\b[a-zA-Z]{3,}\b", query.lower())
        keywords = []
        for tok in raw_tokens:
            cleaned = tok.strip("$").replace(",", "")
            if cleaned not in stopwords and len(cleaned) > 1:
                keywords.append(cleaned)
        return keywords

    def _calculate_keyword_overlap(self, query: str, context_text: str) -> float:
        """Calculates ratio of query keywords present in context text."""
        keywords = self._extract_query_keywords(query)
        if not keywords:
            return 1.0
        context_clean = context_text.lower().replace(",", "")
        matched = 0
        for kw in keywords:
            stem = kw[:5] if len(kw) >= 6 else kw
            if (
                kw in context_clean
                or (kw.endswith("s") and kw[:-1] in context_clean)
                or (kw.endswith("es") and kw[:-2] in context_clean)
                or (kw + "s" in context_clean)
                or (len(kw) >= 5 and stem in context_clean)
            ):
                matched += 1
        return matched / len(keywords)

    def evaluate_retrieval_quality(
        self,
        query: str,
        retrieved_chunks: List[Any],
        similarity_scores: Optional[List[float]] = None,
    ) -> GuardrailDecision:
        """
        Tasks 1 & 3: Detects weak retrieval using multi-signal quality checks.
        
        Signals Evaluated:
        1. Empty Results: No chunks returned from retrieval.
        2. Low Similarity Score: Top candidate similarity < min_similarity_threshold.
        3. Insufficient Chunks: Number of chunks above threshold < min_chunks_above_threshold.
        4. Weak Lexical Alignment: Keyword overlap ratio < min_keyword_overlap_ratio.
        5. Insufficient Character Length: Context contains negligible text.
        """
        reasons: List[str] = []
        total_chunks = len(retrieved_chunks)

        # 1. Check for Empty Retrieval
        if total_chunks == 0:
            signals = RetrievalQualitySignals(
                total_chunks_retrieved=0,
                top_similarity_score=0.0,
                mean_top_k_score=0.0,
                chunks_above_threshold=0,
                keyword_overlap_ratio=0.0,
                total_context_chars=0,
                is_empty_retrieval=True,
                is_low_similarity=True,
                is_insufficient_chunks=True,
                is_weak_lexical_alignment=True,
            )
            return GuardrailDecision(
                should_refuse=True,
                verdict="SAFE_REFUSAL",
                refusal_reasons=["EMPTY_RETRIEVAL_RESULTS"],
                primary_reason="EMPTY_RETRIEVAL_RESULTS: Zero candidate chunks were returned from knowledge base.",
                confidence_score=0.0,
                quality_signals=signals,
            )

        # Extract raw texts and scores
        chunk_texts = []
        for c in retrieved_chunks:
            if hasattr(c, "text"):
                chunk_texts.append(c.text)
            elif hasattr(c, "source_text"):
                chunk_texts.append(c.source_text)
            elif isinstance(c, dict):
                chunk_texts.append(c.get("text", c.get("source_text", str(c))))
            else:
                chunk_texts.append(str(c))

        full_context = "\n".join(chunk_texts)
        total_chars = len(full_context.strip())

        # Process similarity scores
        if similarity_scores and len(similarity_scores) > 0:
            valid_scores = [float(s) for s in similarity_scores]
        else:
            # Fallback score extraction if embedded inside chunk objects
            valid_scores = []
            for c in retrieved_chunks:
                if hasattr(c, "score"):
                    valid_scores.append(float(c.score))
                elif hasattr(c, "similarity"):
                    valid_scores.append(float(c.similarity))
                elif isinstance(c, dict) and "score" in c:
                    valid_scores.append(float(c["score"]))
                else:
                    valid_scores.append(0.50)  # Default neutral score if unprovided

        top_score = max(valid_scores) if valid_scores else 0.0
        mean_score = (sum(valid_scores) / len(valid_scores)) if valid_scores else 0.0
        above_thresh_count = sum(1 for s in valid_scores if s >= self.config.min_similarity_threshold)
        kw_overlap = self._calculate_keyword_overlap(query, full_context)

        # Check conditions
        is_low_sim = top_score < self.config.min_similarity_threshold
        is_few_chunks = above_thresh_count < self.config.min_chunks_above_threshold
        is_weak_kw = kw_overlap < self.config.min_keyword_overlap_ratio
        is_too_short = total_chars < self.config.min_context_character_length

        if is_low_sim:
            reasons.append(
                f"LOW_SIMILARITY_SCORE: Top score ({top_score:.4f}) is below minimum threshold ({self.config.min_similarity_threshold:.2f})."
            )
        if is_few_chunks:
            reasons.append(
                f"INSUFFICIENT_CHUNKS_ABOVE_THRESHOLD: Only {above_thresh_count} chunk(s) met threshold (required: {self.config.min_chunks_above_threshold})."
            )
        if is_weak_kw:
            reasons.append(
                f"WEAK_LEXICAL_ALIGNMENT: Keyword overlap ({kw_overlap * 100:.1f}%) is below minimum required ({self.config.min_keyword_overlap_ratio * 100:.1f}%)."
            )
        if is_too_short:
            reasons.append(
                f"INSUFFICIENT_CONTEXT_LENGTH: Total context length ({total_chars} chars) is below threshold ({self.config.min_context_character_length} chars)."
            )

        should_refuse = len(reasons) > 0
        primary_reason = reasons[0] if reasons else None
        
        # Calculate composite confidence score
        confidence = (0.50 * top_score) + (0.30 * kw_overlap) + (0.20 * min(1.0, above_thresh_count / max(1, self.config.min_chunks_above_threshold)))
        if should_refuse:
            confidence = min(confidence, 0.30)

        signals = RetrievalQualitySignals(
            total_chunks_retrieved=total_chunks,
            top_similarity_score=round(top_score, 4),
            mean_top_k_score=round(mean_score, 4),
            chunks_above_threshold=above_thresh_count,
            keyword_overlap_ratio=round(kw_overlap, 4),
            total_context_chars=total_chars,
            is_empty_retrieval=False,
            is_low_similarity=is_low_sim,
            is_insufficient_chunks=is_few_chunks,
            is_weak_lexical_alignment=is_weak_kw,
        )

        return GuardrailDecision(
            should_refuse=should_refuse,
            verdict="SAFE_REFUSAL" if should_refuse else "PROCEED_CONFIDENT_ANSWER",
            refusal_reasons=reasons,
            primary_reason=primary_reason,
            confidence_score=round(confidence, 4),
            quality_signals=signals,
        )

    def generate_safe_refusal(
        self,
        query: str,
        decision: GuardrailDecision,
        custom_refusal_message: Optional[str] = None,
    ) -> GuardrailResult:
        """
        Task 2: Returns a safe refusal without calling generative LLM, preventing hallucinations.
        """
        refusal_msg = custom_refusal_message or self.config.standard_refusal_message
        
        self.logger.info(f"🛑 [Guardrail Safe Refusal Triggered]: Query='{query}'")
        self.logger.info(f"   Reason: {decision.primary_reason}")

        return GuardrailResult(
            query=query,
            decision=decision,
            is_refusal=True,
            final_answer=refusal_msg,
            cited_sources=[],
            raw_context_text="",
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    def process_query(
        self,
        query: str,
        retrieved_chunks: List[Any],
        similarity_scores: Optional[List[float]] = None,
        role: str = "Banking Regulation & Compliance Officer",
        mock_response: Optional[str] = None,
    ) -> GuardrailResult:
        """
        Tasks 1 to 4: Evaluates retrieval signals.
        - If weak: Returns safe refusal (Task 2).
        - If strong: Generates confident, grounded response with citations (Task 4).
        """
        # Step 1: Quality Check & Threshold Evaluation (Task 1 & Task 3)
        decision = self.evaluate_retrieval_quality(
            query=query,
            retrieved_chunks=retrieved_chunks,
            similarity_scores=similarity_scores,
        )

        # Step 2: Handle Weak Retrieval with Safe Refusal (Task 2)
        if decision.should_refuse:
            return self.generate_safe_refusal(query=query, decision=decision)

        # Step 3: Preserve Confident Answers on Strong Retrieval (Task 4)
        self.logger.info(f"✅ [Guardrail Passed]: Query='{query}' proceeding with confident grounded generation.")
        
        augmented_prompt = self.injector.build_augmented_prompt(
            question=query,
            retrieved_chunks=retrieved_chunks,
            role=role,
            marker_style=SourceMarkerStyle.NUMBERED,
            enforce_grounding=True,
        )

        gen_result = self.injector.generate_grounded_answer(
            augmented_prompt=augmented_prompt,
            llm_client=self.llm_client,
            mock_response=mock_response,
        )

        cited_sources = gen_result.get("injected_sources", [])

        return GuardrailResult(
            query=query,
            decision=decision,
            is_refusal=False,
            final_answer=gen_result.get("grounded_answer", ""),
            cited_sources=cited_sources,
            raw_context_text=augmented_prompt.assembled_context.formatted_context,
            token_usage=gen_result.get("token_usage", {}),
        )

    def run_demonstration_suite(
        self,
        sample_chunks: List[Any],
    ) -> Dict[str, Any]:
        """
        Task 4 & 5: Runs comprehensive demonstrations covering both Refusal Cases and Confident Answer Cases.
        """
        cases = [
            # Case 1: Strong Supporting Context (Preserve Confident Answer)
            {
                "case_id": "CASE_1_CONFIDENT_ANSWER",
                "title": "Confident Grounded Answer (Strong Context)",
                "description": "High semantic similarity score and exact entity match for customer encryption and data breach policies.",
                "query": "What are the customer encryption standards and data breach reporting timeframe?",
                "chunks": [c for c in sample_chunks if "encrypt" in (c.text.lower() if hasattr(c, "text") else str(c).lower())][:2] or sample_chunks[:1],
                "scores": [0.89, 0.76],
                "mock_response": (
                    "Customer financial data must be encrypted at rest using AES-256 and in transit using TLS 1.3 or higher [1]. "
                    "Additionally, any data breach must be reported to the regulatory oversight committee within 24 hours of initial detection [1]."
                ),
            },
            # Case 2: Out-of-Domain Query with Low Similarity (Safe Refusal)
            {
                "case_id": "CASE_2_LOW_SIMILARITY_REFUSAL",
                "title": "Safe Refusal on Low Similarity Score (Out-of-Domain Query)",
                "description": "Quantum computing satellite encryption query matched against banking docs yields low similarity below threshold.",
                "query": "What is the quantum encryption satellite key rotation protocol for deep-space missions?",
                "chunks": sample_chunks[:2],
                "scores": [0.12, 0.08],  # Below 0.35 threshold
                "mock_response": None,
            },
            # Case 3: Empty Retrieval Results (Safe Refusal)
            {
                "case_id": "CASE_3_EMPTY_RETRIEVAL_REFUSAL",
                "title": "Safe Refusal on Empty Retrieval Results",
                "description": "Knowledge search returns zero candidate chunks.",
                "query": "What are the rules regarding Mars planetary mineral mining royalties?",
                "chunks": [],
                "scores": [],
                "mock_response": None,
            },
            # Case 4: Weak Lexical Alignment (Safe Refusal)
            {
                "case_id": "CASE_4_WEAK_KEYWORD_ALIGNMENT_REFUSAL",
                "title": "Safe Refusal on Weak Lexical Keyword Overlap",
                "description": "Query with unrelated domain terminology matched loosely on general stopword density.",
                "query": "Explain quantum teleportation error correction rates and cryogenic qubit stability.",
                "chunks": sample_chunks[:1],
                "scores": [0.28],
                "mock_response": None,
            },
        ]

        evaluated_results = []
        for case in cases:
            res = self.process_query(
                query=case["query"],
                retrieved_chunks=case["chunks"],
                similarity_scores=case["scores"],
                mock_response=case.get("mock_response"),
            )
            evaluated_results.append({
                "case_id": case["case_id"],
                "title": case["title"],
                "description": case["description"],
                "input_query": case["query"],
                "provided_chunks_count": len(case["chunks"]),
                "provided_similarity_scores": case["scores"],
                "result": res.to_dict(),
            })

        return {
            "guardrail_config": asdict(self.config),
            "total_cases_evaluated": len(cases),
            "refusal_cases_count": sum(1 for c in evaluated_results if c["result"]["is_refusal"]),
            "confident_cases_count": sum(1 for c in evaluated_results if not c["result"]["is_refusal"]),
            "demonstrations": evaluated_results,
        }

    def export_sample_artifacts(
        self,
        demo_summary: Dict[str, Any],
        output_json_path: str = os.path.join("outputs", "hallucination_guardrail_results.json"),
        output_txt_path: str = os.path.join("outputs", "guardrail_refusal_sample.txt"),
        output_md_path: str = os.path.join("outputs", "guardrail_report.md"),
    ):
        """
        Task 5: Exports structured JSON results, human-readable refusal logs, and markdown report.
        """
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

        # 1. Export JSON Artifact
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(demo_summary, f, indent=2)

        # 2. Export Refusal and Confident Answer Comparison Text Log
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write("================================================================================\n")
            f.write("         HALLUCINATION GUARDRAILS & REFUSAL HANDLING VERIFICATION REPORT         \n")
            f.write("================================================================================\n\n")

            for idx, demo in enumerate(demo_summary.get("demonstrations", []), 1):
                f.write(f"################################################################################\n")
                f.write(f"CASE #{idx}: {demo['title']}\n")
                f.write(f"Description: {demo['description']}\n")
                f.write(f"################################################################################\n")
                f.write(f"Query: \"{demo['input_query']}\"\n")
                f.write(f"Candidate Chunks: {demo['provided_chunks_count']} | Scores: {demo['provided_similarity_scores']}\n\n")

                res = demo["result"]
                dec = res["decision"]
                f.write(f"--- [GUARDRAIL EVALUATION SIGNALS] ---\n")
                f.write(f"  * Verdict:         {dec['verdict']}\n")
                f.write(f"  * Should Refuse:   {dec['should_refuse']}\n")
                f.write(f"  * Confidence:      {dec['confidence_score']}\n")
                f.write(f"  * Top Score:       {dec['quality_signals']['top_similarity_score']}\n")
                f.write(f"  * Keyword Overlap: {dec['quality_signals']['keyword_overlap_ratio'] * 100:.1f}%\n")
                if dec["refusal_reasons"]:
                    f.write(f"  * Refusal Reasons: {json.dumps(dec['refusal_reasons'], indent=4)}\n")
                f.write("\n")

                f.write(f"--- [FINAL GENERATED OUTPUT] ---\n")
                f.write(f"Is Refusal: {res['is_refusal']}\n")
                f.write(f"Answer:\n\"{res['final_answer']}\"\n\n")
                if res["cited_sources"]:
                    f.write(f"Cited Sources:\n{json.dumps(res['cited_sources'], indent=2)}\n\n")
                f.write("================================================================================\n\n")

        # 3. Export Detailed Markdown Report
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write("# Hallucination Guardrails & Refusal Handling Report\n\n")
            f.write("## Overview\n\n")
            f.write("This report documents the implementation and verification of the **Hallucination Guardrails and Safe Refusal Engine**.\n\n")
            f.write("### Tasks Implemented\n\n")
            f.write("- **Task 1 — Detect Weak Retrieval**: Automatically evaluates retrieval signals (empty results, low similarity, insufficient chunks, keyword mismatch).\n")
            f.write("- **Task 2 — Return Safe Refusals**: Bypasses generative LLMs when retrieval is weak, returning standardized safe refusals without hallucinating.\n")
            f.write("- **Task 3 — Relevance Thresholds & Quality Checks**: Enforces calibrated thresholds (`min_similarity_threshold = 0.35`, `min_keyword_overlap = 0.15`).\n")
            f.write("- **Task 4 — Preserve Confident Answers**: Ensures strong supporting evidence produces full grounded answers with traceable source citations.\n")
            f.write("- **Task 5 — Output Artifacts & Reproducibility**: Generates structured JSON samples (`outputs/hallucination_guardrail_results.json`) and refusal logs (`outputs/guardrail_refusal_sample.txt`).\n\n")

            f.write("## Multi-Signal Decision Matrix (Task 1 & 3)\n\n")
            f.write("| Signal | Threshold / Condition | Action if Violated |\n")
            f.write("| :--- | :--- | :--- |\n")
            f.write(f"| **Candidate Count** | $N > 0$ | `EMPTY_RETRIEVAL_RESULTS` $\\rightarrow$ Refusal |\n")
            f.write(f"| **Top Similarity Score** | $\\text{{Score}}_{{\\text{{top}}}} \\ge {self.config.min_similarity_threshold}$ | `LOW_SIMILARITY_SCORE` $\\rightarrow$ Refusal |\n")
            f.write(f"| **Chunks Above Threshold** | $\\text{{Count}} \\ge {self.config.min_chunks_above_threshold}$ | `INSUFFICIENT_CHUNKS` $\\rightarrow$ Refusal |\n")
            f.write(f"| **Lexical Overlap Ratio** | $\\text{{Overlap}} \\ge {self.config.min_keyword_overlap_ratio * 100}\\%$ | `WEAK_LEXICAL_ALIGNMENT` $\\rightarrow$ Refusal |\n\n")

            f.write("## Case Comparison Summary\n\n")
            for idx, demo in enumerate(demo_summary.get("demonstrations", []), 1):
                res = demo["result"]
                dec = res["decision"]
                f.write(f"### Case {idx}: {demo['title']}\n\n")
                f.write(f"- **Query**: *\"{demo['input_query']}\"*\n")
                f.write(f"- **Verdict**: `{dec['verdict']}`\n")
                f.write(f"- **Refusal Triggered?**: **`{res['is_refusal']}`**\n")
                f.write(f"- **Top Similarity Score**: `{dec['quality_signals']['top_similarity_score']}`\n")
                f.write(f"- **Output Answer**:\n\n> {res['final_answer']}\n\n---\n\n")

            f.write("## Conclusion\n\n")
            f.write("The guardrail engine successfully protects the RAG pipeline from unsupported hallucinations by enforcing multi-signal quality checks and clean fallback refusals while preserving high-confidence grounded answers.\n")
