# Document Upload & Vector Indexing Execution Report

## Overview
Demonstration of dynamic document upload, token-aware chunking, vector embedding, ChromaDB indexing, and runtime searchability.

## Task 1: Upload Endpoint
- **Filename**: `sample_esg_regulatory_directives.txt`
- **Stored Filename**: `sample_esg_regulatory_directives_20260910_035228.txt`
- **Document ID**: `SAMPLE_ESG_REGULATORY_DIRECTIVES_20260910_035228`
- **HTTP Status**: `201`

## Task 2: Ingestion & Vector DB Indexing Summary
- **Chunks Indexed**: `1`
- **Total Tokens Indexed**: `352`
- **Embedding Model**: `text-embedding-3-small`
- **Embedding Dimension**: `1536`
- **Processing Time**: `2998.05 ms`

## Task 3: Runtime Searchability (Zero-Downtime Query Verification)
- **Query**: *"What is the penalty for Level 3 Severe Violations under the ESG directive?"*
- **Answer**: The penalty for Level 3 Severe Violations under the ESG directive is a non-negotiable statutory fine of 12,500,000 USD, accompanied by an immediate 90-day suspension of new sovereign debt syndication privileges [1].
- **Retrieved Sources Count**: 3
- **Is Grounded**: `True`

## Task 4: Error Handling Scenarios
| Test Scenario | Expected Status | Received Status | Status Message |
| :--- | :---: | :---: | :--- |
| `unsupported_format_exe` | 415 | 415 | Unsupported file format '.exe'. Allowed formats are: .csv, .json, .md, .pdf, .txt. |
| `empty_file` | 400 | 400 | The uploaded file 'empty_manifest.txt' is empty or contains no readable text. |
| `whitespace_only_file` | 400 | 400 | The uploaded file 'blank_document.txt' is empty or contains no readable text. |
| `oversized_file` | 413 | 413 | The uploaded file 'massive_dump.txt' (10.0 MB) exceeds the maximum allowed limit of 10.0 MB. |

## Task 5: Committed Artifacts
- `outputs/upload_sample_request.json`
- `outputs/upload_indexing_summary.json`
- `outputs/upload_followup_query_result.json`
- `outputs/upload_error_responses.json`
- `outputs/upload_indexing_report.md`
