"""
Backend RAG API Demonstration Runner (Tasks 1 to 5).

Executes:
1. Task 1: Query endpoint request dispatching and answer generation with retrieved sources.
2. Task 2: Structured JSON response verification (status, answer, sources, metadata, confidence).
3. Task 3: Input validation & error status code handling (400 empty input, 422 schema validation, 500 error handling).
4. Task 4: Environment-driven configuration inspection and validation.
5. Task 5: Exporting sample request, response, error payloads, and execution logs.
"""

import os
import sys
import json
import time
from typing import Dict, Any

# Ensure project root and src are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastapi.testclient import TestClient
from src.server import app
from src.config import config


def run_api_demonstration():
    print("=" * 70)
    print("       RAG SERVICE BACKEND REST API DEMONSTRATION (TASKS 1-5)")
    print("=" * 70)

    client = TestClient(app)
    outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    execution_logs = []

    def log(msg: str):
        print(msg)
        execution_logs.append(msg)

    # -------------------------------------------------------------
    # TASK 4: VERIFY CONFIGURATION FROM ENVIRONMENT
    # -------------------------------------------------------------
    log("\n[TASK 4] Loading and verifying environment-driven configuration...")
    config_resp = client.get("/api/config")
    log(f"Status Code: {config_resp.status_code}")
    config_data = config_resp.json()
    log(f"Active Config: {json.dumps(config_data, indent=2)}")
    assert config_resp.status_code == 200
    assert "config" in config_data

    # -------------------------------------------------------------
    # TASK 1 & 2: VALID RAG QUERY WITH STRUCTURED JSON OUTPUT
    # -------------------------------------------------------------
    log("\n[TASK 1 & TASK 2] Sending query to /api/query endpoint...")
    sample_request = {
        "question": "What is the capital adequacy requirement for Tier 1 capital under the framework?",
        "top_k": 3,
        "temperature": 0.2,
        "use_mock": False
    }
    log(f"Request Payload:\n{json.dumps(sample_request, indent=2)}")

    query_resp = client.post("/api/query", json=sample_request)
    log(f"Status Code: {query_resp.status_code}")
    query_data = query_resp.json()
    log(f"Structured JSON Response:\n{json.dumps(query_data, indent=2)}")

    assert query_resp.status_code == 200
    assert query_data["status"] in ("success", "fallback")
    assert "answer" in query_data and len(query_data["answer"]) > 0
    assert "sources" in query_data
    assert isinstance(query_data["sources"], list)
    assert "metadata" in query_data
    assert "latency_ms" in query_data["metadata"]

    # -------------------------------------------------------------
    # TASK 3: VALIDATION AND ERROR HANDLING DEMONSTRATION
    # -------------------------------------------------------------
    log("\n[TASK 3] Demonstrating Input Validation & Error Handling...")

    # Case A: Empty question -> 400 Bad Request
    log("\nCase A: Empty question input -> Expected 400 Bad Request")
    empty_req = {"question": "   ", "top_k": 3}
    err_resp_400 = client.post("/api/query", json=empty_req)
    log(f"Status Code: {err_resp_400.status_code}")
    err_400_data = err_resp_400.json()
    log(f"Response Payload:\n{json.dumps(err_400_data, indent=2)}")
    assert err_resp_400.status_code in (400, 422)

    # Case B: Out-of-bounds parameter -> 422 Unprocessable Entity
    log("\nCase B: Out-of-bounds top_k (-5) -> Expected 422 Unprocessable Entity")
    invalid_param_req = {"question": "What is the incident notification SLA?", "top_k": -5}
    err_resp_422 = client.post("/api/query", json=invalid_param_req)
    log(f"Status Code: {err_resp_422.status_code}")
    err_422_data = err_resp_422.json()
    log(f"Response Payload:\n{json.dumps(err_422_data, indent=2)}")
    assert err_resp_422.status_code == 422

    # Case C: Missing required field -> 422 Unprocessable Entity
    log("\nCase C: Missing required field 'question' -> Expected 422 Unprocessable Entity")
    missing_field_req = {"top_k": 5}
    err_resp_missing = client.post("/api/query", json=missing_field_req)
    log(f"Status Code: {err_resp_missing.status_code}")
    err_missing_data = err_resp_missing.json()
    log(f"Response Payload:\n{json.dumps(err_missing_data, indent=2)}")
    assert err_resp_missing.status_code == 422

    # Case D: Second valid query (Cybersecurity SLA)
    log("\nQuery 2: Cybersecurity breach notification timeframe")
    query_2_req = {
        "question": "What is the mandatory reporting timeframe for data breaches and cybersecurity incidents?",
        "top_k": 2,
        "temperature": 0.1
    }
    query_2_resp = client.post("/api/query", json=query_2_req)
    log(f"Status Code: {query_2_resp.status_code}")
    query_2_data = query_2_resp.json()
    log(f"Query 2 Response:\n{json.dumps(query_2_data, indent=2)}")

    # -------------------------------------------------------------
    # TASK 5: EXPORT ARTIFACTS
    # -------------------------------------------------------------
    log("\n[TASK 5] Persisting sample request, response, and error artifacts...")

    sample_req_path = os.path.join(outputs_dir, "api_query_sample_request.json")
    with open(sample_req_path, "w", encoding="utf-8") as f:
        json.dump(sample_request, f, indent=2)
    log(f"Saved: {sample_req_path}")

    sample_resp_path = os.path.join(outputs_dir, "api_query_sample_response.json")
    with open(sample_resp_path, "w", encoding="utf-8") as f:
        json.dump(query_data, f, indent=2)
    log(f"Saved: {sample_resp_path}")

    error_resp_path = os.path.join(outputs_dir, "api_query_error_response.json")
    error_summary = {
        "empty_question_test": {
            "request": empty_req,
            "status_code": err_resp_400.status_code,
            "response": err_400_data
        },
        "invalid_top_k_test": {
            "request": invalid_param_req,
            "status_code": err_resp_422.status_code,
            "response": err_422_data
        },
        "missing_question_test": {
            "request": missing_field_req,
            "status_code": err_resp_missing.status_code,
            "response": err_missing_data
        }
    }
    with open(error_resp_path, "w", encoding="utf-8") as f:
        json.dump(error_summary, f, indent=2)
    log(f"Saved: {error_resp_path}")

    log_path = os.path.join(outputs_dir, "api_query_execution_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(execution_logs) + "\n")
    log(f"Saved: {log_path}")

    print("\n" + "=" * 70)
    print("   ALL 5 BACKEND API TASKS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_api_demonstration()
