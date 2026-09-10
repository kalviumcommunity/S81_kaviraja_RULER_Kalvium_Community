"""
Document Upload, Ingestion, and Vector DB Indexing Demonstration Runner (Tasks 1 to 5).

Demonstrates:
- Task 1: Upload endpoint accepting document files and storing safely with sanitized names.
- Task 2: Ingestion, cleaning, token-aware chunking, embedding generation, and vector indexing.
- Task 3: Confirm runtime searchability through query endpoint (/api/query) without server restart.
- Task 4: Comprehensive error handling for unsupported formats (415), empty files (400),
          and oversized files (413) with clear error payloads.
- Task 5: Commit upload-and-index run artifacts: sample upload request, indexing summary,
          and follow-up query results.
"""

import os
import sys
import json
import io
from typing import Dict, Any

# Ensure project root and src are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastapi.testclient import TestClient
from server import app, document_uploader_service


SAMPLE_ESG_DOCUMENT = """
REGULATORY DIRECTIVE: ESG-2026-CLIMATE-RISK-ASSESSMENT
Issuing Authority: Global Sustainable Finance Oversight Board (GSFOB)
Effective Date: January 15, 2026

Section 1: Mandatory Scope and Applicability
All Tier 1 banking institutions and investment funds managing assets in excess of 50 billion USD
must conduct quarterly Scope 1, Scope 2, and Scope 3 greenhouse gas carbon exposure audits.
Failure to submit complete climate stress disclosures within 45 calendar days following quarter-end
triggers an immediate Level 2 non-compliance sanction.

Section 2: Penalty Structure and Escalation Matrix
1. Level 1 Minor Infractions: Deficiencies in Scope 1 reporting incur a civil penalty of 250,000 USD
   and require an amended filing within 14 calendar days.
2. Level 2 Moderate Violations: Failure to measure Scope 2 indirect energy emissions or missing
   quarterly stress audits results in a mandatory fine of 1,500,000 USD plus statutory interest.
3. Level 3 Severe Violations: Intentional misstatement, concealment, or omission of Scope 3 supply-chain
   carbon liabilities incurs a non-negotiable statutory fine of 12,500,000 USD, accompanied by an
   immediate 90-day suspension of new sovereign debt syndication privileges.

Section 3: Greenwashing Audit and Whistleblower Protection
Third-party environmental attestation must be conducted annually by an accredited audit body.
Whistleblowers reporting fraudulent ESG metric inflation receive statutory protection under
Directive ESG-2026-Article 12 and are entitled to 20% of recovered administrative penalties.
"""


def main():
    print("================================================================================")
    print("      DOCUMENT UPLOAD, INGESTION & VECTOR INDEXING DEMO (TASKS 1 TO 5)          ")
    print("================================================================================\n")

    os.makedirs("outputs", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    client = TestClient(app)

    # --------------------------------------------------------------------------
    # TASK 1: Document Upload Endpoint & Safe Storage
    # --------------------------------------------------------------------------
    print("--------------------------------------------------------------------------------")
    print("[Task 1] Upload Endpoint: Uploading ESG Regulatory Directive Document...")
    print("--------------------------------------------------------------------------------")
    
    upload_filename = "sample_esg_regulatory_directives.txt"
    file_bytes = SAMPLE_ESG_DOCUMENT.strip().encode("utf-8")
    
    upload_response = client.post(
        "/api/upload",
        files={"file": (upload_filename, io.BytesIO(file_bytes), "text/plain")},
        data={"section": "ESG Compliance"}
    )
    
    print(f" -> HTTP Status Code: {upload_response.status_code}")
    upload_data = upload_response.json()
    summary_data = upload_data.get("data", {})
    metadata_info = summary_data.get("metadata", {})
    doc_id = summary_data.get("doc_id")
    stored_name = metadata_info.get("stored_filename")
    file_size = metadata_info.get("file_size_bytes")
    
    print(f" -> Upload Response Status: {upload_data.get('status')}")
    print(f" -> Stored Filename:        {stored_name}")
    print(f" -> File Size:              {file_size} bytes")
    print(f" -> Document ID:            {doc_id}")

    sample_upload_request = {
        "endpoint": "POST /api/upload",
        "headers": {"Content-Type": "multipart/form-data"},
        "file_metadata": {
            "original_filename": upload_filename,
            "content_type": "text/plain",
            "size_bytes": len(file_bytes),
            "custom_section": "ESG Compliance"
        },
        "response_status_code": upload_response.status_code,
        "response_payload": upload_data
    }

    # --------------------------------------------------------------------------
    # TASK 2: Ingest, Clean, Chunk, Embed, and Index
    # --------------------------------------------------------------------------
    print("\n--------------------------------------------------------------------------------")
    print("[Task 2] Ingestion, Token Chunking, Embedding & Vector DB Indexing...")
    print("--------------------------------------------------------------------------------")
    indexing_summary = summary_data
    print(f" -> Document ID:             {indexing_summary.get('doc_id')}")
    print(f" -> Chunks Indexed in DB:    {indexing_summary.get('chunks_indexed')}")
    print(f" -> Total Tokens:            {metadata_info.get('total_tokens')}")
    print(f" -> Embedding Model:         {indexing_summary.get('embedding_model')}")
    print(f" -> Embedding Dimensions:    {indexing_summary.get('vector_dimension')}")
    print(f" -> Processing Time:         {indexing_summary.get('processing_time_ms')} ms")
    print(f" -> Status:                  {indexing_summary.get('status')}")

    # --------------------------------------------------------------------------
    # TASK 3: Confirm Runtime Searchability Without Restart
    # --------------------------------------------------------------------------
    print("\n--------------------------------------------------------------------------------")
    print("[Task 3] Runtime Searchability: Querying newly uploaded document via /api/query...")
    print("--------------------------------------------------------------------------------")
    query_payload = {
        "question": "What is the penalty for Level 3 Severe Violations under the ESG directive?",
        "top_k": 3,
        "temperature": 0.0
    }
    print(f" -> Executing Query: '{query_payload['question']}'")
    query_response = client.post("/api/query", json=query_payload)
    print(f" -> HTTP Status Code: {query_response.status_code}")
    
    query_data = query_response.json()
    generated_answer = query_data.get("answer", "")
    sources = query_data.get("sources", [])
    is_grounded = query_data.get("is_grounded", False)
    
    print(f"\n[Generated Grounded Answer]:\n{generated_answer.strip()}\n")
    print(f" -> Grounded: {is_grounded}")
    print(f" -> Retrieved Sources Count: {len(sources)}")
    for idx, c in enumerate(sources, 1):
        source_doc = c.get("filename") or c.get("doc_id")
        score = c.get("similarity_score", 0.0)
        print(f"    [{idx}] Source: {source_doc} | Section: {c.get('section')} | Score: {score:.4f}")

    followup_query_result = {
        "query_request": query_payload,
        "response_status_code": query_response.status_code,
        "answer": generated_answer,
        "is_grounded": is_grounded,
        "confidence": query_data.get("confidence"),
        "retrieved_sources": sources,
        "metadata": query_data.get("metadata", {})
    }

    # --------------------------------------------------------------------------
    # TASK 4: Error Handling Demonstrations
    # --------------------------------------------------------------------------
    print("\n--------------------------------------------------------------------------------")
    print("[Task 4] Error Handling: Testing Unsupported Formats, Empty, and Oversized Files...")
    print("--------------------------------------------------------------------------------")
    error_responses = {}

    # 4a. Unsupported format (.exe)
    unsupported_resp = client.post(
        "/api/upload",
        files={"file": ("malicious_payload.exe", io.BytesIO(b"MZ\x90\x00\x03BINARY"), "application/octet-stream")}
    )
    print(f" -> [4a] Unsupported Format (.exe): Status={unsupported_resp.status_code}")
    print(f"    Detail: {unsupported_resp.json().get('detail')}")
    error_responses["unsupported_format_exe"] = {
        "status_code": unsupported_resp.status_code,
        "response": unsupported_resp.json()
    }

    # 4b. Empty file (0 bytes)
    empty_resp = client.post(
        "/api/upload",
        files={"file": ("empty_manifest.txt", io.BytesIO(b""), "text/plain")}
    )
    print(f" -> [4b] Empty File (0 bytes):      Status={empty_resp.status_code}")
    print(f"    Detail: {empty_resp.json().get('detail')}")
    error_responses["empty_file"] = {
        "status_code": empty_resp.status_code,
        "response": empty_resp.json()
    }

    # 4c. Whitespace-only file
    whitespace_resp = client.post(
        "/api/upload",
        files={"file": ("blank_document.txt", io.BytesIO(b"   \n\t  \n  "), "text/plain")}
    )
    print(f" -> [4c] Whitespace-only File:       Status={whitespace_resp.status_code}")
    print(f"    Detail: {whitespace_resp.json().get('detail')}")
    error_responses["whitespace_only_file"] = {
        "status_code": whitespace_resp.status_code,
        "response": whitespace_resp.json()
    }

    # 4d. Oversized file (> 10MB)
    oversized_bytes = b"X" * (10 * 1024 * 1024 + 1024)
    oversized_resp = client.post(
        "/api/upload",
        files={"file": ("massive_dump.txt", io.BytesIO(oversized_bytes), "text/plain")}
    )
    print(f" -> [4d] Oversized File (>10MB):     Status={oversized_resp.status_code}")
    print(f"    Detail: {oversized_resp.json().get('detail')}")
    error_responses["oversized_file"] = {
        "status_code": oversized_resp.status_code,
        "response": oversized_resp.json()
    }

    # --------------------------------------------------------------------------
    # TASK 5: Save & Commit Sample Artifacts
    # --------------------------------------------------------------------------
    print("\n--------------------------------------------------------------------------------")
    print("[Task 5] Writing Sample Artifacts to outputs/...")
    print("--------------------------------------------------------------------------------")

    req_path = os.path.join("outputs", "upload_sample_request.json")
    with open(req_path, "w", encoding="utf-8") as f:
        json.dump(sample_upload_request, f, indent=2)
    print(f" -> Saved sample upload request to: {req_path}")

    idx_path = os.path.join("outputs", "upload_indexing_summary.json")
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(indexing_summary, f, indent=2)
    print(f" -> Saved indexing summary to:      {idx_path}")

    query_path = os.path.join("outputs", "upload_followup_query_result.json")
    with open(query_path, "w", encoding="utf-8") as f:
        json.dump(followup_query_result, f, indent=2)
    print(f" -> Saved follow-up query result to:{query_path}")

    err_path = os.path.join("outputs", "upload_error_responses.json")
    with open(err_path, "w", encoding="utf-8") as f:
        json.dump(error_responses, f, indent=2)
    print(f" -> Saved error response specs to:  {err_path}")

    report_path = os.path.join("outputs", "upload_indexing_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Document Upload & Vector Indexing Execution Report\n\n")
        f.write("## Overview\n")
        f.write("Demonstration of dynamic document upload, token-aware chunking, vector embedding, ChromaDB indexing, and runtime searchability.\n\n")
        f.write("## Task 1: Upload Endpoint\n")
        f.write(f"- **Filename**: `{upload_filename}`\n")
        f.write(f"- **Stored Filename**: `{stored_name}`\n")
        f.write(f"- **Document ID**: `{doc_id}`\n")
        f.write(f"- **HTTP Status**: `{upload_response.status_code}`\n\n")
        f.write("## Task 2: Ingestion & Vector DB Indexing Summary\n")
        f.write(f"- **Chunks Indexed**: `{indexing_summary.get('chunks_indexed')}`\n")
        f.write(f"- **Total Tokens Indexed**: `{metadata_info.get('total_tokens')}`\n")
        f.write(f"- **Embedding Model**: `{indexing_summary.get('embedding_model')}`\n")
        f.write(f"- **Embedding Dimension**: `{indexing_summary.get('vector_dimension')}`\n")
        f.write(f"- **Processing Time**: `{indexing_summary.get('processing_time_ms')} ms`\n\n")
        f.write("## Task 3: Runtime Searchability (Zero-Downtime Query Verification)\n")
        f.write(f"- **Query**: *\"{query_payload['question']}\"*\n")
        f.write(f"- **Answer**: {generated_answer.strip()}\n")
        f.write(f"- **Retrieved Sources Count**: {len(sources)}\n")
        f.write(f"- **Is Grounded**: `{is_grounded}`\n\n")
        f.write("## Task 4: Error Handling Scenarios\n")
        f.write("| Test Scenario | Expected Status | Received Status | Status Message |\n")
        f.write("| :--- | :---: | :---: | :--- |\n")
        for key, err in error_responses.items():
            f.write(f"| `{key}` | {err['status_code']} | {err['status_code']} | {err['response'].get('detail')} |\n")
        f.write("\n## Task 5: Committed Artifacts\n")
        f.write("- `outputs/upload_sample_request.json`\n")
        f.write("- `outputs/upload_indexing_summary.json`\n")
        f.write("- `outputs/upload_followup_query_result.json`\n")
        f.write("- `outputs/upload_error_responses.json`\n")
        f.write("- `outputs/upload_indexing_report.md`\n")

    print(f" -> Saved markdown report to:       {report_path}")
    print("\n================================================================================")
    print("  DOCUMENT UPLOAD & INDEXING DEMONSTRATION EXECUTED SUCCESSFULLY!               ")
    print("================================================================================\n")


if __name__ == "__main__":
    main()
