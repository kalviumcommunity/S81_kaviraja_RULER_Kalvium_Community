"""
Test suite for Ruler FastAPI Web UI Endpoints.
Verifies /api/status, /api/sample-data, /api/chunk, /api/trace, and /api/recover-json.
"""

import unittest
from fastapi.testclient import TestClient
from src.server import app


class TestRulerApiEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_status_endpoint(self):
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("has_api_key", data)
        self.assertIn("token_chunker_available", data)

    def test_02_sample_data_endpoint(self):
        resp = self.client.get("/api/sample-data")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Banking Regulatory Compliance Framework", data["content"])
        self.assertEqual(data["filename"], "sample_banking_regulation.txt")

    def test_03_token_chunk_endpoint(self):
        payload = {
            "mode": "token",
            "chunk_size": 150,
            "chunk_overlap": 30,
            "filename": "sample_banking_regulation.txt"
        }
        resp = self.client.post("/api/chunk", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total_chunks"], 1)
        self.assertTrue(data["consistency_report"]["is_fully_consistent"])
        self.assertIsNotNone(data.get("boundary_preservation_demo"))

    def test_04_recover_json_endpoint(self):
        payload = {
            "raw_json": "```json\n{\n  \"answer\": \"Capital adequacy Tier 1 must be 10.5%.\",\n  \"source\": \"BRCF-2026 Page 2\",\n}\n```",
            "required_fields": ["answer", "source", "confidence"],
            "default_values": {"confidence": "high"}
        }
        resp = self.client.post("/api/recover-json", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["final_validated_object"]["confidence"], "high")

    def test_05_trace_endpoint(self):
        # First chunk the text
        chunk_resp = self.client.post("/api/chunk", json={"mode": "char", "chunk_size": 200, "chunk_overlap": 20})
        self.assertEqual(chunk_resp.status_code, 200)
        chunks = chunk_resp.json()["chunks"]
        self.assertGreater(len(chunks), 0)

        # Trace the first chunk
        trace_payload = {"chunk_data": chunks[0]}
        trace_resp = self.client.post("/api/trace", json=trace_payload)
        self.assertEqual(trace_resp.status_code, 200)
        trace_data = trace_resp.json()
        self.assertTrue(trace_data["is_traced_successfully"])
    def test_06_rerank_endpoint(self):
        payload = {
            "query": "What are the data breach reporting timeframe and encryption standards?",
            "initial_k": 5,
            "top_k": 2,
            "method": "custom",
            "candidates": [
                {
                    "chunk_id": "cand_01",
                    "text": "All financial models must be monitored.",
                    "metadata": {"doc": "model_policy.txt"},
                    "vector_distance": 0.20,
                    "vector_similarity": 0.80
                },
                {
                    "chunk_id": "cand_02",
                    "text": "Data breaches must be reported within 24 hours. AES-256 encryption is mandatory.",
                    "metadata": {"doc": "security_policy.txt"},
                    "vector_distance": 0.25,
                    "vector_similarity": 0.75
                }
            ]
        }
        resp = self.client.post("/api/rerank", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["initial_candidate_count"], 2)
        self.assertEqual(data["final_top_k_count"], 2)
        self.assertEqual(len(data["top_k_selected_chunks"]), 2)
        # Verify ground truth candidate was promoted to rank 1
        self.assertEqual(data["all_candidates_comparison"][0]["chunk_id"], "cand_02")
        self.assertEqual(data["all_candidates_comparison"][0]["final_rank"], 1)


if __name__ == "__main__":
    unittest.main()

