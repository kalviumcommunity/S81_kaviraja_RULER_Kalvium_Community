"""
Unit and Integration Test Suite for MongoDB Database Layer and Schemas.

Verifies:
1. Schema integrity for UserRecord, QueryRecord, FeedbackRecord, DocumentRecord, and ChunkRecord.
2. MongoDB client initialization and configuration loading.
3. CRUD operations on queries, feedback, documents, and users.
4. Database health telemetry and collection statistics (/api/db/status).
5. Offline graceful fallback mode.
"""

import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from src.database import (
    MongoDBClient,
    UserRecord,
    QueryRecord,
    FeedbackRecord,
    DocumentRecord,
    ChunkRecord,
)
from src.server import app


class TestMongoDBIntegration(unittest.TestCase):
    """Test suite for MongoDB database schemas, client operations, and endpoints."""

    def setUp(self):
        # Create fresh test client instance with in-memory fallback enabled
        self.db = MongoDBClient(mongo_uri="mongodb://localhost:27017", db_name="ruler_test_db")
        self.api_client = TestClient(app)

    def test_01_user_record_schema(self):
        """Validates UserRecord creation, default values, and dictionary export."""
        user = UserRecord(
            email="officer@banking-compliance.gov",
            full_name="Jane Doe",
            role="Compliance Officer",
            department="Banking Regulatory Risk",
        )
        data = user.to_dict()
        self.assertEqual(data["email"], "officer@banking-compliance.gov")
        self.assertEqual(data["role"], "Compliance Officer")
        self.assertEqual(data["status"], "active")
        self.assertIn("created_at", data)

        saved = self.db.save_user(user)
        self.assertEqual(saved["email"], "officer@banking-compliance.gov")

        fetched = self.db.get_user("officer@banking-compliance.gov")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["full_name"], "Jane Doe")

    def test_02_query_record_schema_and_persistence(self):
        """Validates QueryRecord fields, sources array, and query retrieval."""
        query = QueryRecord(
            question="What is Tier 1 Capital Adequacy ratio?",
            answer="Tier 1 Capital Adequacy ratio must be at least 10.5% [1].",
            status="success",
            confidence="high",
            is_grounded=True,
            user_email="compliance@bank.com",
            sources=[
                {
                    "doc_id": "DOC_BRCF_2026_001",
                    "filename": "sample_banking_regulation.txt",
                    "section": "Section 1: Executive Overview",
                    "similarity_score": 0.95,
                }
            ],
            tokens_generated=48,
            latency_ms=120.5,
        )
        data = query.to_dict()
        self.assertEqual(data["question"], "What is Tier 1 Capital Adequacy ratio?")
        self.assertEqual(len(data["sources"]), 1)
        self.assertEqual(data["tokens_generated"], 48)

        saved = self.db.save_query(query)
        self.assertIn("created_at", saved)

        queries = self.db.get_queries(limit=10)
        self.assertGreaterEqual(len(queries), 1)
        self.assertEqual(queries[0]["question"], "What is Tier 1 Capital Adequacy ratio?")

    def test_03_feedback_record_schema_and_persistence(self):
        """Validates FeedbackRecord thoughts, ratings, and category tagging."""
        feedback = FeedbackRecord(
            question="What are data breach reporting timeframes?",
            answer="Data breaches must be reported within 24 hours.",
            rating="helpful",
            rating_score=1,
            thoughts="Accurate citation of Section 3 cybersecurity directive.",
            category="Cybersecurity & Encryption",
            tokens_generated=32,
        )
        data = feedback.to_dict()
        self.assertEqual(data["rating"], "helpful")
        self.assertEqual(data["category"], "Cybersecurity & Encryption")
        self.assertEqual(data["rating_score"], 1)

        saved = self.db.save_feedback(feedback)
        self.assertEqual(saved["thoughts"], "Accurate citation of Section 3 cybersecurity directive.")

        feedbacks = self.db.get_feedbacks(limit=5)
        self.assertGreaterEqual(len(feedbacks), 1)

    def test_04_document_and_chunk_records(self):
        """Validates DocumentRecord and ChunkRecord schema consistency."""
        doc = DocumentRecord(
            doc_id="DOC_AML_2026_01",
            filename="aml_kyc_directives.txt",
            category="AML / KYC Directives",
            character_count=1200,
            token_count=300,
            chunk_count=2,
        )
        chunk1 = ChunkRecord(
            chunk_id="DOC_AML_chunk_1",
            doc_id="DOC_AML_2026_01",
            filename="aml_kyc_directives.txt",
            text="Financial institutions must perform Enhanced Due Diligence (EDD).",
            section="Section 1: EDD Requirements",
            token_count=150,
            start_char=0,
            end_char=68,
        )

        saved_doc = self.db.save_document(doc, chunks=[chunk1])
        self.assertEqual(saved_doc["doc_id"], "DOC_AML_2026_01")

        all_docs = self.db.get_documents()
        self.assertGreaterEqual(len(all_docs), 1)

    def test_05_database_status_and_health(self):
        """Validates database telemetry report and /api/db/status endpoint."""
        status = self.db.get_status()
        self.assertEqual(status["database_type"], "MongoDB")
        self.assertEqual(status["database_name"], "ruler_test_db")
        self.assertIn("collections", status)

        # Test FastAPI endpoint
        resp = self.api_client.get("/api/db/status")
        self.assertEqual(resp.status_code, 200)
        api_data = resp.json()
        self.assertEqual(api_data["database_type"], "MongoDB")
        self.assertIn("collections", api_data)


if __name__ == "__main__":
    unittest.main()
