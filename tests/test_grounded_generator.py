"""
Unit and integration tests for Context-Grounded Generation, Source Accuracy,
Missing-Context Fallback, and Retrieval Comparisons (Tasks 1 to 5).
"""

import os
import json
import pytest
from unittest.mock import MagicMock

from src.llm_client import LLMClient
from src.chunk_embedding_pipeline import EmbeddedChunk
from src.grounded_generator import (
    GroundedRAGGenerator,
    GroundedAnswer,
    AccuracyAuditReport,
    ClaimVerificationResult,
)


@pytest.fixture
def sample_chunks():
    """Returns sample embedded chunks from banking regulation corpus."""
    chunk1 = EmbeddedChunk(
        chunk_id="sample_banking_regulation_txt#chunk_003",
        source_text=(
            "30-day stress period. The Liquidity Coverage Ratio (LCR) must be calculated daily "
            "and submitted to regional financial regulatory bodies.\n\n"
            "## Section 3: High-Value Transaction Authorization Thresholds\n"
            "Standard retail banking policies mandate that routine vendor payments under $50,000 "
            "may be approved directly by designated department heads without requiring senior executive approval. "
            "However, any single capital expenditure or vendor disbursement exceeding $50,000 requires unanimous "
            "board authorization and an independent audit report prior to disbursement."
        ),
        embedding=[0.01] * 1536,
        dimension=1536,
        metadata={
            "doc_id": "sample_banking_regulation_txt",
            "filename": "sample_banking_regulation.txt",
            "section": "Section 3: High-Value Transaction Authorization Thresholds",
            "chunk_index": 2
        }
    )
    chunk2 = EmbeddedChunk(
        chunk_id="sample_banking_regulation_txt#chunk_004",
        source_text=(
            ",000 requires unanimous board authorization and an independent audit report prior to disbursement. "
            "Failure to obtain board authorization for high-value transactions results in immediate suspension "
            "of procurement privileges and mandatory compliance audit review."
        ),
        embedding=[0.02] * 1536,
        dimension=1536,
        metadata={
            "doc_id": "sample_banking_regulation_txt",
            "filename": "sample_banking_regulation.txt",
            "section": "Section 3: High-Value Transaction Authorization Thresholds",
            "chunk_index": 3
        }
    )
    return [chunk1, chunk2]



@pytest.fixture
def mock_generator(sample_chunks):
    """Initializes GroundedRAGGenerator with a mock LLMClient."""
    mock_client = LLMClient()
    mock_client.api_key = "mock"
    return GroundedRAGGenerator(client=mock_client)



# ==============================================================================
# TASK 1 TESTS: GENERATE FROM INJECTED CONTEXT
# ==============================================================================

def test_format_context_blocks(mock_generator, sample_chunks):
    """Verifies that chunks are formatted into delimited context blocks with headers."""
    context_str = mock_generator.format_context_blocks(sample_chunks)
    assert "[Chunk #1 | ID: sample_banking_regulation_txt#chunk_003]" in context_str
    assert "Section: Section 3: High-Value Transaction Authorization Thresholds" in context_str
    assert "$50,000" in context_str
    assert "[Chunk #2 | ID: sample_banking_regulation_txt#chunk_004]" in context_str


def test_format_context_blocks_empty(mock_generator):
    """Verifies format_context_blocks handles empty chunk list."""
    assert mock_generator.format_context_blocks([]) == "NO_CONTEXT_AVAILABLE"


def test_generate_grounded_answer(mock_generator, sample_chunks):
    """Task 1: Tests generating a grounded answer using injected context."""
    query = "What are the rules and approval thresholds for high-value transaction payments?"
    res = mock_generator.generate_grounded_answer(query, sample_chunks)

    assert isinstance(res, GroundedAnswer)
    assert res.is_grounded is True
    assert res.fallback_triggered is False
    assert "$50,000" in res.answer
    assert "unanimous board authorization" in res.answer
    assert len(res.cited_chunk_ids) > 0
    assert "sample_banking_regulation_txt#chunk_003" in res.cited_chunk_ids


# ==============================================================================
# TASK 2 TESTS: CHECK SOURCE ACCURACY & FAITHFULNESS
# ==============================================================================

def test_verify_source_accuracy_grounded(mock_generator, sample_chunks):
    """Task 2: Confirms 100% faithfulness for an answer accurately reflecting the context."""
    answer = (
        "Routine vendor payments under $50,000 may be approved directly by designated department heads. "
        "Any capital expenditure exceeding $50,000 requires unanimous board authorization and an independent audit report. "
        "Failure to obtain board authorization results in immediate suspension of procurement privileges."
    )
    report = mock_generator.verify_source_accuracy(answer, sample_chunks)

    assert isinstance(report, AccuracyAuditReport)
    assert report.total_claims == 3
    assert report.supported_claims == 3
    assert report.unsupported_claims == 0
    assert report.faithfulness_score == 100.0
    assert report.verdict == "100% FAITHFUL & SOURCE-ACCURATE"
    for c in report.claims:
        assert c.is_supported is True


def test_verify_source_accuracy_unsupported_claim(mock_generator, sample_chunks):
    """Task 2: Confirms detection and flagging of unsupported claims or fabricated entities."""
    hallucinated_answer = (
        "Routine vendor payments under $50,000 may be approved directly by department heads. "
        "All payments exceeding $5,000,000 require immediate notification to the Department of Treasury."
    )
    report = mock_generator.verify_source_accuracy(hallucinated_answer, sample_chunks)

    assert report.total_claims == 2
    assert report.unsupported_claims >= 1
    assert report.faithfulness_score < 100.0
    assert "CONTAINS" in report.verdict
    # Verify the second claim was flagged
    assert report.claims[1].is_supported is False
    assert "$5,000,000" in (report.claims[1].unsupported_reason or "")


# ==============================================================================
# TASK 3 TESTS: MISSING-CONTEXT FALLBACK
# ==============================================================================

def test_missing_context_fallback_empty_context(mock_generator):
    """Task 3: Verifies fallback triggered when no context chunks are supplied."""
    query = "What is the policy for vendor payments?"
    res = mock_generator.generate_with_fallback_handling(query, retrieved_chunks=[])

    assert res.fallback_triggered is True
    assert res.fallback_reason == "INSUFFICIENT_OR_IRRELEVANT_CONTEXT"
    assert "do not have enough information in the provided context" in res.answer


def test_missing_context_fallback_irrelevant_query(mock_generator, sample_chunks):
    """Task 3: Verifies fallback triggered when query is completely outside the domain of chunks."""
    out_of_domain_query = "What is the corporate policy regarding remote work reimbursement and airline baggage fees?"
    res = mock_generator.generate_with_fallback_handling(out_of_domain_query, retrieved_chunks=sample_chunks)

    assert res.fallback_triggered is True
    assert res.fallback_reason == "INSUFFICIENT_OR_IRRELEVANT_CONTEXT"
    assert "do not have enough information in the provided context" in res.answer
    assert "remote work reimbursement" in res.answer


def test_fallback_not_triggered_for_relevant_query(mock_generator, sample_chunks):
    """Task 3: Verifies fallback is NOT triggered when context contains relevant facts."""
    relevant_query = "Which disbursements exceeding $50,000 require board authorization?"
    res = mock_generator.generate_with_fallback_handling(relevant_query, retrieved_chunks=sample_chunks)

    assert res.fallback_triggered is False
    assert "$50,000" in res.answer


# ==============================================================================
# TASK 4 TESTS: COMPARE WITH AND WITHOUT RETRIEVAL
# ==============================================================================

def test_compare_with_and_without_retrieval(mock_generator, sample_chunks):
    """Task 4: Demonstrates side-by-side comparison showing how grounding changes the answer."""
    query = "What are the rules and approval thresholds for high-value transaction payments?"
    comparison = mock_generator.compare_with_and_without_retrieval(query, sample_chunks)

    assert "with_retrieval_grounded" in comparison
    assert "without_retrieval_ungrounded" in comparison
    assert "grounding_delta_analysis" in comparison

    grounded = comparison["with_retrieval_grounded"]
    ungrounded = comparison["without_retrieval_ungrounded"]

    # Grounded answer has exact institutional limits
    assert "$50,000" in grounded["answer"]
    assert "unanimous board authorization" in grounded["exact_policy_terms_found"]
    assert grounded["faithfulness_score"] == 100.0

    # Ungrounded answer does not have exact $50,000 threshold or specific sanctions
    assert "VERY LOW" in grounded["hallucination_risk"]
    assert "HIGH" in ungrounded["hallucination_risk"]
    assert comparison["grounding_delta_analysis"]["verifiable_citations"] is True


# ==============================================================================
# TASK 5 TESTS: EXPORT REPORTS & PERSISTENCE
# ==============================================================================

def test_export_grounded_reports(mock_generator, sample_chunks, tmp_path):
    """Task 5: Confirms export of structured JSON, comparison report, and text logs."""
    query = "What are the rules and approval thresholds for high-value transaction payments?"
    grounded_ans = mock_generator.generate_grounded_answer(query, sample_chunks)
    accuracy_rep = mock_generator.verify_source_accuracy(grounded_ans.answer, sample_chunks)
    fallback_ans = mock_generator.generate_with_fallback_handling("Irrelevant query", [])
    comparison = mock_generator.compare_with_and_without_retrieval(query, sample_chunks)

    json_path = str(tmp_path / "test_results.json")
    txt_path = str(tmp_path / "test_output.txt")
    comp_path = str(tmp_path / "test_comp.json")
    acc_path = str(tmp_path / "test_acc.txt")
    fb_path = str(tmp_path / "test_fb.txt")

    payload = mock_generator.export_grounded_reports(
        grounded_answer=grounded_ans,
        accuracy_report=accuracy_rep,
        fallback_demo=fallback_ans,
        comparison_demo=comparison,
        output_json_path=json_path,
        output_txt_path=txt_path,
        comparison_json_path=comp_path,
        accuracy_txt_path=acc_path,
        fallback_txt_path=fb_path,
    )

    assert os.path.exists(json_path)
    assert os.path.exists(txt_path)
    assert os.path.exists(comp_path)
    assert os.path.exists(acc_path)
    assert os.path.exists(fb_path)

    with open(json_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert "task_1_grounded_answer" in loaded
    assert "task_2_source_accuracy_audit" in loaded
    assert "task_3_missing_context_fallback" in loaded
    assert "task_4_with_vs_without_comparison" in loaded
