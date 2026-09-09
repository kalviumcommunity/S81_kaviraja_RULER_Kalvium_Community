"""
Test suite for Ruler FastAPI Web & RAG Service REST Endpoints.
Verifies:
- Task 1 & 2: /api/query endpoint and structured JSON response formatting
- Task 3: Input validation, missing field handling, out-of-range bounds, and HTTP status codes (400, 422, 500)
- Task 4: /api/config endpoint and environment-driven configuration loading
- Legacy endpoints: /api/status, /api/sample-data, /api/chunk, /api/trace, /api/recover-json, /api/rerank, /api/chat
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
        chunk_resp = self.client.post("/api/chunk", json={"mode": "char", "chunk_size": 200, "chunk_overlap": 20})
        self.assertEqual(chunk_resp.status_code, 200)
        chunks = chunk_resp.json()["chunks"]
        self.assertGreater(len(chunks), 0)

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
        self.assertEqual(data["all_candidates_comparison"][0]["chunk_id"], "cand_02")
        self.assertEqual(data["all_candidates_comparison"][0]["final_rank"], 1)

    # -------------------------------------------------------------
    # TASK 1 & TASK 2: QUERY ENDPOINT & STRUCTURED JSON RESPONSE
    # -------------------------------------------------------------
    def test_07_query_endpoint_success(self):
        payload = {
            "question": "What is the capital adequacy requirement for Tier 1 capital?",
            "top_k": 3,
            "temperature": 0.2,
            "use_mock": False
        }
        resp = self.client.post("/api/query", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Verify structured JSON top-level fields (Task 2)
        self.assertIn("status", data)
        self.assertIn(data["status"], ["success", "fallback"])
        self.assertEqual(data["question"], payload["question"])
        self.assertIn("answer", data)
        self.assertIsInstance(data["answer"], str)
        self.assertGreater(len(data["answer"]), 0)

        # Verify sources list and fields
        self.assertIn("sources", data)
        self.assertIsInstance(data["sources"], list)
        self.assertGreaterEqual(len(data["sources"]), 1)
        source = data["sources"][0]
        self.assertIn("doc_id", source)
        self.assertIn("filename", source)
        self.assertIn("chunk_id", source)
        self.assertIn("text", source)

        # Verify metadata object
        self.assertIn("metadata", data)
        self.assertIn("model", data["metadata"])
        self.assertIn("latency_ms", data["metadata"])
        self.assertIn("tokens_used", data["metadata"])
        self.assertIn("timestamp", data["metadata"])

    def test_08_query_endpoint_alias(self):
        payload = {
            "question": "What is the mandatory incident reporting SLA?",
            "top_k": 2
        }
        resp = self.client.post("/query", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertIn("sources", data)

    # -------------------------------------------------------------
    # TASK 3: VALIDATE INPUT & HANDLE ERRORS
    # -------------------------------------------------------------
    def test_09_query_validation_empty_whitespace_question(self):
        payload = {"question": "    "}
        resp = self.client.post("/api/query", json=payload)
        # Should return 400 Bad Request or 422 Unprocessable Entity
        self.assertIn(resp.status_code, [400, 422])
        data = resp.json()
        self.assertEqual(data["status"], "error")

    def test_10_query_validation_missing_question_field(self):
        payload = {"top_k": 5}
        resp = self.client.post("/api/query", json=payload)
        self.assertEqual(resp.status_code, 422)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("detail", data)

    def test_11_query_validation_invalid_top_k(self):
        payload = {
            "question": "What is the capital requirement?",
            "top_k": -2
        }
        resp = self.client.post("/api/query", json=payload)
        self.assertEqual(resp.status_code, 422)
        data = resp.json()
        self.assertEqual(data["status"], "error")

    def test_12_query_validation_invalid_temperature(self):
        payload = {
            "question": "What is the capital requirement?",
            "temperature": 15.0
        }
        resp = self.client.post("/api/query", json=payload)
        self.assertEqual(resp.status_code, 422)
        data = resp.json()
        self.assertEqual(data["status"], "error")

    # -------------------------------------------------------------
    # TASK 4: LOAD CONFIG FROM ENVIRONMENT
    # -------------------------------------------------------------
    def test_13_config_endpoint(self):
        resp = self.client.get("/api/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("config", data)
        cfg = data["config"]
        self.assertIn("chat_model", cfg)
        self.assertIn("embedding_model", cfg)
        self.assertIn("chroma_db_path", cfg)

    # -------------------------------------------------------------
    # LEGACY CHAT ENDPOINT
    # -------------------------------------------------------------
    def test_14_legacy_chat_endpoint(self):
        payload = {"user_message": "What is the reserve requirement?"}
        resp = self.client.post("/api/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success", False))


if __name__ == "__main__":
    unittest.main()
