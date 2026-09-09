"""
Unit and Integration Tests for Conversational RAG & Query Rewriting Engine (Tasks 1 to 5).
"""

import os
import json
import pytest
from unittest.mock import MagicMock

from src.llm_client import LLMClient
from src.chunk_embedding_pipeline import EmbeddedChunk
from src.conversational_rag import (
    ConversationTurn,
    ConversationHistoryTracker,
    ConversationalQueryRewriter,
    ConversationalRetriever,
    ConversationalRAGEngine,
    RetrievalComparisonResult,
    _extract_chunk_score,
)


@pytest.fixture
def mock_client():
    """Mock LLMClient for deterministic offline test runs."""
    client = MagicMock(spec=LLMClient)
    client.api_key = "mock"
    client.model_name = "gpt-4o-mini"
    client.logger = MagicMock()
    return client


@pytest.fixture
def sample_embedded_chunks():
    """Returns sample banking regulation embedded chunks."""
    c1 = EmbeddedChunk(
        chunk_id="sample_banking_regulation_txt#chunk_001",
        source_text=(
            "# Global Banking Compliance & Regulatory Framework 2026\n"
            "Financial institutions operating within international jurisdictions must establish "
            "automated compliance monitoring systems to detect, prevent, and report suspicious transactions "
            "under Anti-Money Laundering (AML) and Counter-Terrorism Financing (CTF) directives."
        ),
        embedding=[0.05] * 1536,
        dimension=1536,
        metadata={
            "filename": "sample_banking_regulation.txt",
            "section": "Section 1: Executive Summary & Overview",
            "category": "Compliance & Regulation"
        }
    )
    c2 = EmbeddedChunk(
        chunk_id="sample_banking_regulation_txt#chunk_002",
        source_text=(
            "## Section 2: Capital Reserves & Liquidity Ratios\n"
            "Under Basel IV capital adequacy standards, Tier 1 common equity capital must remain above 10.5% "
            "of total risk-weighted assets at all times. In addition, institutions must hold high-quality liquid "
            "assets (HQLA) sufficient to cover total net cash outflows over a 30-day stress period. "
            "The Liquidity Coverage Ratio (LCR) must be calculated daily and submitted to regional financial regulatory bodies."
        ),
        embedding=[0.10] * 1536,
        dimension=1536,
        metadata={
            "filename": "sample_banking_regulation.txt",
            "section": "Section 2: Capital Reserves & Liquidity Ratios",
            "category": "Compliance & Regulation"
        }
    )
    c3 = EmbeddedChunk(
        chunk_id="sample_banking_regulation_txt#chunk_003",
        source_text=(
            "## Section 3: High-Value Transaction Authorization Thresholds\n"
            "Standard retail banking policies mandate that routine vendor payments under $50,000 "
            "may be approved directly by designated department heads without requiring senior executive approval. "
            "However, any single capital expenditure or vendor disbursement exceeding $50,000 requires unanimous "
            "board authorization and an independent audit report prior to disbursement."
        ),
        embedding=[0.15] * 1536,
        dimension=1536,
        metadata={
            "filename": "sample_banking_regulation.txt",
            "section": "Section 3: High-Value Transaction Authorization Thresholds",
            "category": "Compliance & Regulation"
        }
    )
    c4 = EmbeddedChunk(
        chunk_id="sample_banking_regulation_txt#chunk_004",
        source_text=(
            ",000 requires unanimous board authorization and an independent audit report prior to disbursement. "
            "Failure to obtain board authorization for high-value transactions results in immediate suspension "
            "of procurement privileges and mandatory compliance audit review."
        ),
        embedding=[0.20] * 1536,
        dimension=1536,
        metadata={
            "filename": "sample_banking_regulation.txt",
            "section": "Section 3: High-Value Transaction Authorization Thresholds",
            "category": "Compliance & Regulation"
        }
    )
    return [c1, c2, c3, c4]


# ==============================================================================
# TASK 1 TESTS: CONVERSATION HISTORY TRACKING
# ==============================================================================

def test_task_1_conversation_turn_creation():
    """Verify ConversationTurn fields and dictionary conversion."""
    turn = ConversationTurn(
        turn_id=1,
        user_query="What is the capital reserve ratio?",
        assistant_response="Tier 1 capital must remain above 10.5% [1].",
        rewritten_query="What is the capital reserve ratio under Basel IV?",
        is_rewritten=True,
        retrieved_chunk_ids=["chunk_002"],
        citations=["chunk_002"],
        similarity_scores=[0.892],
    )
    d = turn.to_dict()
    assert d["turn_id"] == 1
    assert d["user_query"] == "What is the capital reserve ratio?"
    assert d["is_rewritten"] is True
    assert "chunk_002" in d["retrieved_chunk_ids"]
    assert d["similarity_scores"] == [0.892]


def test_task_1_history_tracker_window_and_formatting():
    """Verify FIFO windowing, turn tracking, and prompt formatting."""
    tracker = ConversationHistoryTracker(max_turns=2)
    assert len(tracker) == 0

    t1 = tracker.add_turn(
        user_query="What is Basel IV?",
        assistant_response="A global regulatory standard on bank capital adequacy.",
    )
    assert len(tracker) == 1
    assert t1.turn_id == 1

    t2 = tracker.add_turn(
        user_query="What is the minimum Tier 1 ratio?",
        assistant_response="Tier 1 ratio must be above 10.5%.",
    )
    assert len(tracker) == 2
    assert t2.turn_id == 2

    # Third turn should trigger FIFO capacity eviction
    t3 = tracker.add_turn(
        user_query="What happens if a bank fails to comply?",
        assistant_response="It faces audit review and penalties.",
    )
    assert len(tracker) == 2
    turns = tracker.get_turns()
    assert turns[0].user_query == "What is the minimum Tier 1 ratio?"
    assert turns[1].user_query == "What happens if a bank fails to comply?"

    # Prompt formatting test
    prompt_str = tracker.format_history_for_prompt()
    assert "User: What is the minimum Tier 1 ratio?" in prompt_str
    assert "Assistant: Tier 1 ratio must be above 10.5%." in prompt_str


# ==============================================================================
# TASK 2 TESTS: FOLLOW-UP QUERY REWRITING
# ==============================================================================

def test_task_2_standalone_query_preservation(mock_client):
    """Verify that an already standalone query is not rewritten."""
    tracker = ConversationHistoryTracker()
    rewriter = ConversationalQueryRewriter(client=mock_client)

    query = "What are the rules and approval thresholds for high-value transaction payments?"
    rewritten, was_rw, meta = rewriter.rewrite_query(query, tracker)

    assert was_rw is False
    assert rewritten == query
    assert meta["was_rewritten"] is False


def test_task_2_pronoun_followup_rewriting(mock_client):
    """Verify that a pronoun follow-up ('them') is rewritten into a standalone query."""
    tracker = ConversationHistoryTracker()
    tracker.add_turn(
        user_query="What are the rules and approval thresholds for high-value transaction payments?",
        assistant_response="Payments over $50,000 require unanimous board authorization and an audit.",
    )
    rewriter = ConversationalQueryRewriter(client=mock_client)

    followup = "What happens if a bank fails to comply with them?"
    rewritten, was_rw, meta = rewriter.rewrite_query(followup, tracker)

    assert was_rw is True
    assert "high-value" in rewritten.lower() or "transaction" in rewritten.lower() or "payment" in rewritten.lower()
    assert "penalt" in rewritten.lower() or "fail" in rewritten.lower() or "consequence" in rewritten.lower()


def test_task_2_elliptical_followup_rewriting(mock_client):
    """Verify that elliptical follow-up queries ('What about routine vendor payments under that threshold?') are expanded."""
    tracker = ConversationHistoryTracker()
    tracker.add_turn(
        user_query="What are the rules for payments exceeding $50,000?",
        assistant_response="Disbursements exceeding $50,000 require unanimous board authorization.",
    )
    rewriter = ConversationalQueryRewriter(client=mock_client)

    followup = "What about routine vendor payments under that threshold?"
    rewritten, was_rw, meta = rewriter.rewrite_query(followup, tracker)

    assert was_rw is True
    assert "$50,000" in rewritten or "50,000" in rewritten or "threshold" in rewritten


# ==============================================================================
# TASK 3 TESTS: RETRIEVE USING REWRITTEN QUERY & COMPARATIVE EVALUATION
# ==============================================================================

def test_task_3_retrieval_comparison(sample_embedded_chunks):
    """Verify that retrieval with rewritten query shows score improvement over ambiguous query."""
    client = LLMClient()
    retriever = ConversationalRetriever(client=client)

    raw_query = "What happens if a bank fails to comply with them?"
    rewritten_query = "What are the regulatory penalties and consequences if a financial institution fails to comply with high-value transaction payment authorization thresholds?"

    comparison = retriever.compare_retrieval(
        raw_query=raw_query,
        rewritten_query=rewritten_query,
        embedded_chunks=sample_embedded_chunks,
        expected_section_keyword="Section",
    )

    assert isinstance(comparison, RetrievalComparisonResult)
    assert comparison.raw_query == raw_query
    assert comparison.rewritten_query == rewritten_query
    assert comparison.rewritten_top_chunk_id is not None
    assert comparison.rewritten_top_similarity_score > 0.0
    assert comparison.similarity_score_gain >= 0.0
    assert "PASSED" in comparison.relevance_verdict


# ==============================================================================
# TASK 4 TESTS: END-TO-END MULTI-TURN DIALOGUE
# ==============================================================================

def test_task_4_multi_turn_dialogue(sample_embedded_chunks):
    """Verify sequential execution of multi-turn dialogue with history retention."""
    client = LLMClient()
    engine = ConversationalRAGEngine(client=client)

    custom_queries = [
        "What are the rules and approval thresholds for high-value transaction payments?",
        "What happens if a bank fails to comply with them?",
        "What about routine vendor payments under that threshold?",
    ]

    summary = engine.run_multi_turn_demonstration(
        embedded_chunks=sample_embedded_chunks,
        custom_dialogue_queries=custom_queries,
    )

    assert summary["total_turns"] == 3
    assert summary["standalone_initial_turns_count"] == 1
    assert summary["rewritten_turns_count"] == 2
    assert len(summary["dialogue_turns"]) == 3

    # Turn 1 should be standalone
    assert summary["dialogue_turns"][0]["was_rewritten"] is False
    assert len(summary["dialogue_turns"][0]["retrieved_chunk_ids"]) > 0

    # Turn 2 should be rewritten
    assert summary["dialogue_turns"][1]["was_rewritten"] is True
    assert summary["dialogue_turns"][1]["rewritten_query"] is not None

    # Turn 3 should be rewritten
    assert summary["dialogue_turns"][2]["was_rewritten"] is True


# ==============================================================================
# TASK 5 TESTS: EXPORT SAMPLE DIALOGUE ARTIFACTS
# ==============================================================================

def test_task_5_export_artifacts(tmp_path, sample_embedded_chunks):
    """Verify generation of sample dialogue JSON, text transcript, and reports."""
    client = LLMClient()
    engine = ConversationalRAGEngine(client=client)

    summary = engine.run_multi_turn_demonstration(
        embedded_chunks=sample_embedded_chunks,
        custom_dialogue_queries=[
            "What are the rules and approval thresholds for high-value transaction payments?",
            "What happens if a bank fails to comply with them?",
        ]
    )

    json_path = str(tmp_path / "sample_dialogue.json")
    txt_path = str(tmp_path / "sample_dialogue.txt")
    res_path = str(tmp_path / "conversational_rag_results.json")
    md_path = str(tmp_path / "conversational_rag_report.md")

    engine.export_sample_artifacts(
        demo_summary=summary,
        output_json_path=json_path,
        output_txt_path=txt_path,
        output_results_path=res_path,
        output_report_path=md_path,
    )

    assert os.path.exists(json_path)
    assert os.path.exists(txt_path)
    assert os.path.exists(res_path)
    assert os.path.exists(md_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "dialogue" in data
        assert len(data["dialogue"]) == 2
        assert "turn_id" in data["dialogue"][0]
        assert "rewritten_standalone_query" in data["dialogue"][1]

    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()
        assert "CONVERSATIONAL RAG & QUERY REWRITING SAMPLE DIALOGUE TRANSCRIPT" in text
        assert "TURN #1" in text
        assert "TURN #2" in text

    with open(md_path, "r", encoding="utf-8") as f:
        report = f.read()
        assert "# Conversational RAG & Multi-Turn Query Rewriting Report" in report
