"""
Unit and Integration Tests for Document Upload, Ingestion, Embedding, and Indexing (Tasks 1 to 5).
"""

import os
import io
import json
import pytest
import unittest
from fastapi.testclient import TestClient

from src.server import app
from src.document_uploader import (
    DocumentUploaderService,
    document_uploader_service,
    UnsupportedFormatError,
    EmptyFileError,
    OversizedFileError,
    DocumentProcessingError,
)


class TestDocumentUploadAndIndexing(unittest.TestCase):
    """Test suite covering Tasks 1 to 5 for Document Upload and Ingestion."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_doc_content = (
            "# Global ESG Compliance & Sustainable Finance Directives 2026\n\n"
            "## Section 1: Green Asset Ratio (GAR) Mandates\n"
            "All commercial banking institutions with assets under management exceeding $10 billion "
            "must report their verified Green Asset Ratio (GAR) on a quarterly basis to regional sustainability boards. "
            "The mandatory minimum target for the Green Asset Ratio is set strictly at 18.5% of total eligible balance sheet assets.\n\n"
            "## Section 2: Penalties for Non-Compliance\n"
            "Financial institutions that fail to meet the 18.5% Green Asset Ratio threshold for two consecutive quarters "
            "are subject to an automatic 2.5% surcharge on central bank reserve borrowing facilities and mandatory public disclosure "
            "in quarterly financial audit filings."
        )
        cls.test_filename = "sample_esg_regulatory_directives.txt"

    def test_01_upload_valid_document_success(self):
        """Task 1 & Task 2: Upload valid document, store safely, clean, chunk, embed, and index."""
        file_bytes = self.test_doc_content.encode("utf-8")
        files = {
            "file": (self.test_filename, io.BytesIO(file_bytes), "text/plain")
        }
        data = {
            "category": "ESG Sustainability Regulation",
            "chunk_size": 256,
            "chunk_overlap": 32,
        }

        resp = self.client.post("/api/upload", files=files, data=data)
        self.assertEqual(resp.status_code, 201)
        res_json = resp.json()

        self.assertEqual(res_json["status"], "success")
        self.assertIn("data", res_json)
        summary = res_json["data"]
        self.assertEqual(summary["filename"], self.test_filename)
        self.assertGreater(summary["chunks_indexed"], 0)
        self.assertEqual(summary["vector_dimension"], 1536)
        self.assertIn("sample_chunk_preview", summary)

        # Verify safe storage on disk
        stored_filename = summary["metadata"]["stored_filename"]
        stored_path = os.path.join("data", "uploads", stored_filename)
        self.assertTrue(os.path.exists(stored_path), f"Stored file not found at: {stored_path}")

    def test_02_runtime_searchability_without_restart(self):
        """Task 3: Confirm new uploaded content becomes searchable immediately through /api/query."""
        query_payload = {
            "question": "What is the mandatory minimum target for the Green Asset Ratio (GAR)?",
            "top_k": 3,
            "temperature": 0.1,
            "use_mock": False,
        }
        resp = self.client.post("/api/query", json=query_payload)
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()

        # Verify search found the newly uploaded document chunks
        self.assertEqual(res_json["status"], "success")
        self.assertGreater(len(res_json["sources"]), 0)
        
        # Check that the answer or source includes the ESG content
        source_texts = " ".join([s["text"] for s in res_json["sources"]])
        self.assertTrue("Green Asset Ratio" in source_texts or "18.5%" in source_texts)
        self.assertTrue("18.5%" in res_json["answer"] or "Green Asset Ratio" in res_json["answer"])

    def test_03_query_penalties_from_uploaded_document(self):
        """Task 3: Query specific penalty clause from newly uploaded document."""
        query_payload = {
            "question": "What are the penalties if a financial institution fails to meet the Green Asset Ratio threshold?",
            "top_k": 3,
            "temperature": 0.1,
        }
        resp = self.client.post("/api/query", json=query_payload)
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()

        self.assertEqual(res_json["status"], "success")
        source_texts = " ".join([s["text"] for s in res_json["sources"]])
        self.assertIn("surcharge", source_texts.lower())

    def test_04_upload_empty_file_error(self):
        """Task 4: Uploading an empty 0-byte file returns HTTP 400 Bad Request."""
        empty_files = {
            "file": ("empty_policy.txt", io.BytesIO(b""), "text/plain")
        }
        resp = self.client.post("/api/upload", files=empty_files)
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("empty", str(data).lower())

    def test_05_upload_whitespace_only_file_error(self):
        """Task 4: Uploading whitespace-only file returns HTTP 400 Bad Request."""
        ws_files = {
            "file": ("whitespace.txt", io.BytesIO(b"   \n\n\t   \n  "), "text/plain")
        }
        resp = self.client.post("/api/upload", files=ws_files)
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("empty", str(data).lower())

    def test_06_upload_unsupported_format_error(self):
        """Task 4: Uploading unsupported format (.exe / .zip / .bin) returns HTTP 415."""
        unsupported_files = {
            "file": ("malicious_payload.exe", io.BytesIO(b"MZ\x90\x00\x03\x00"), "application/octet-stream")
        }
        resp = self.client.post("/api/upload", files=unsupported_files)
        self.assertEqual(resp.status_code, 415)
        data = resp.json()
        self.assertIn("unsupported", str(data).lower())

    def test_07_upload_oversized_file_error(self):
        """Task 4: Uploading oversized file exceeding size limit returns HTTP 413."""
        # Create a service with a tiny 100-byte limit to test size rejection
        tiny_service = DocumentUploaderService(max_file_size=100)
        with self.assertRaises(OversizedFileError) as ctx:
            tiny_service.validate_file("large_doc.txt", b"A" * 500)
        self.assertEqual(ctx.exception.status_code, 413)

    def test_08_list_documents_endpoint(self):
        """Task 1 & Task 3: /api/documents endpoint lists uploaded documents."""
        resp = self.client.get("/api/documents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_documents", data)
        self.assertIn("documents", data)
        self.assertGreaterEqual(data["total_documents"], 1)


if __name__ == "__main__":
    unittest.main()
