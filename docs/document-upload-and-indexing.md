# Document Upload, Ingestion, and Vector Database Indexing Documentation

## 1. Motivation & Problem Statement
In production RAG systems, knowledge bases cannot remain static. New policies, regulatory updates, audit reports, and legal directives are continuously published and must be integrated immediately without requiring application downtime or server restarts.

Traditional architectures suffer from two main flaws:
1. **Downtime / Cold Restarts**: Requiring batch pipeline re-indexing and server restarts before newly published guidelines become searchable.
2. **Fragile Ingestion & Security Vulnerabilities**: Accepting unchecked file uploads without size limits, extension whitelisting, filename sanitization, or text normalization leads to directory traversal attacks, memory exhaustion, unhandled parse exceptions, or corrupted vector embeddings.

The **Document Upload & Vector Indexing Subsystem** provides an enterprise-grade ingestion and retrieval lifecycle:
- Secure upload endpoint with path sanitization and multi-layered validation.
- Automated extraction, text normalization, and token-aware chunking.
- Dense vector embedding generation and ChromaDB persistent indexing.
- Immediate zero-downtime runtime searchability across `/api/query` and conversational pipelines.
- Deterministic and structured HTTP error responses for client robustness.

---

## 2. Ingestion & Indexing Architecture

```mermaid
graph TD
    Client["Client / Web UI / CLI"] -->|POST /api/upload| Endpoint["Upload Endpoint (src/server.py)"]
    Endpoint --> Validation{"Format & Size Validation"}
    Validation -- Invalid Format (415) --> Err415["415 Unsupported Media Type"]
    Validation -- Empty / Corrupted (400/422) --> Err400["400/422 Error Response"]
    Validation -- Exceeds 10MB (413) --> Err413["413 Payload Too Large"]
    Validation -- Valid --> Storage["Safe Storage (data/uploads/)"]
    Storage --> Cleaning["Ingestion Text Cleaning & Normalization"]
    Cleaning --> Chunker["Token-Aware Chunker (src/token_chunker.py)"]
    Chunker --> Embedder["Embedding Generator (LLMClient / OpenAI / Gemini)"]
    Embedder --> VectorDB["ChromaDB Vector Database (src/vector_db.py)"]
    VectorDB --> RuntimeRegistry["In-Memory Runtime Chunk Registry"]
    RuntimeRegistry --> QueryEngine["Query Endpoint (/api/query)"]
    Client -->|POST /api/query (No Restart)| QueryEngine
    QueryEngine --> GroundedAnswer["Grounded Cited Answer Generated"]
```

---

## 3. Tasks Breakdown

### Task 1 — Document Upload Endpoint & Safe Storage
- **Endpoints**: `POST /api/upload` (and alias `POST /upload`).
- **Safe File Storage**:
  - `sanitize_filename()` strips illegal filesystem characters and directory traversal markers (`../`, `..\\`).
  - Stored under `data/uploads/` with timestamped unique identifiers to prevent accidental file overwriting.
  - Generates unique uppercase `doc_id` for downstream lineage tracing.

### Task 2 — Ingest, Clean, Chunk, Embed, and Index
- **Cleaning (`clean_extracted_text`)**:
  - Strips null bytes (`\x00`).
  - Normalizes carriage returns (`\r\n` -> `\n`).
  - Collapses redundant vertical whitespace (`\n{3,}` -> `\n\n`) and collapses multiple consecutive inline spaces.
- **Token-Aware Chunking**:
  - Employs `TokenAwareChunker` with target token limit (default: 512 tokens) and configurable sliding overlap (default: 64 tokens).
  - Preserves sentence boundaries and token count precision.
- **Dense Embedding Generation**:
  - Embeds chunk texts via `LLMClient.create_embeddings()` using `text-embedding-3-small` (1536 dimensions) or configured provider.
- **Vector Database Indexing**:
  - Persists vectors, documents, and chunk metadata in `VectorDBClient` (ChromaDB collection `ruler_rag_knowledge_base`).
  - Generates comprehensive metadata: `doc_id`, `filename`, `original_filename`, `section`, `category`, `token_count`, `chunk_index`, and `indexed_at`.

### Task 3 — Confirm Runtime Searchability Without Restart
- Newly uploaded documents are immediately indexed in ChromaDB and registered in the `DocumentUploaderService.indexed_chunks` registry.
- Server retrieval logic (`_retrieve_evidence_chunks`) polls both ChromaDB and active in-memory runtime chunks, ensuring that newly uploaded documents are immediately visible to:
  - `POST /api/query`
  - `POST /api/chat`
  - Conversational RAG multi-turn workflows.
- Zero server restarts or worker reboots required.

### Task 4 — Comprehensive Error Handling
The endpoint intercepts invalid payloads before processing and returns structured HTTP error responses:

| HTTP Status Code | Condition | Example Reason |
| :--- | :--- | :--- |
| **`415 Unsupported Media Type`** | File extension not in whitelist (`.txt`, `.md`, `.json`, `.csv`, `.pdf`) | Uploading `.exe`, `.zip`, `.py`, `.bin` |
| **`400 Bad Request`** | 0-byte file or whitespace-only content | Uploading empty file or file with spaces/newlines only |
| **`413 Payload Too Large`** | Content size strictly exceeds 10 MB limit | Uploading files > 10,485,760 bytes |
| **`422 Unprocessable Entity`** | Encoding errors or unparseable document text | Corrupted binary streams masquerading as text |

### Task 5 — Demonstration & Artifact Export
Demonstration script `scripts/run_upload_and_index_demo.py` executes the end-to-end lifecycle and exports committed artifacts into `outputs/`:
- `outputs/upload_sample_request.json`: Sample multipart upload request payload and HTTP response.
- `outputs/upload_indexing_summary.json`: Chunk count, token metrics, embedding dimension, and vector DB indexing latency.
- `outputs/upload_followup_query_result.json`: Grounded answer generated from the newly uploaded document with retrieved context sources and citations.
- `outputs/upload_error_responses.json`: Verified JSON error payloads for status codes 415, 400, and 413.
- `outputs/upload_indexing_report.md`: Markdown summary report of the execution run.

---

## 4. API Reference

### `POST /api/upload`
Upload a document file for immediate ingestion, chunking, and vector indexing.

#### Request Headers
- `Content-Type: multipart/form-data`

#### Form Parameters
- `file` (*UploadFile*, required): Document file to upload (`.txt`, `.md`, `.json`, `.csv`, `.pdf`).
- `category` (*string*, optional): Document classification (default: `"Institutional Regulation"`).
- `doc_id` (*string*, optional): Explicit document identifier override.
- `chunk_size` (*int*, optional): Target chunk size in tokens (default: `512`).
- `chunk_overlap` (*int*, optional): Token overlap between adjacent chunks (default: `64`).

#### Successful Response (`201 Created`)
```json
{
  "status": "success",
  "message": "Document 'sample_esg_regulatory_directives.txt' uploaded, chunked, embedded, and indexed successfully.",
  "data": {
    "doc_id": "SAMPLE_ESG_REGULATORY_DIRECTIVES_20260910_035228",
    "filename": "sample_esg_regulatory_directives.txt",
    "status": "indexed_successfully",
    "chunks_indexed": 1,
    "embedding_model": "text-embedding-3-small",
    "vector_dimension": 1536,
    "processing_time_ms": 2998.05,
    "chunk_ids": [
      "SAMPLE_ESG_REGULATORY_DIRECTIVES_20260910_035228#chunk_001"
    ],
    "sample_chunk_preview": {
      "chunk_id": "SAMPLE_ESG_REGULATORY_DIRECTIVES_20260910_035228#chunk_001",
      "token_count": 352,
      "snippet": "REGULATORY DIRECTIVE: ESG-2026-CLIMATE-RISK-ASSESSMENT...",
      "metadata": { ... }
    },
    "metadata": {
      "stored_filename": "sample_esg_regulatory_directives_20260910_035228.txt",
      "file_size_bytes": 1570,
      "total_tokens": 352,
      "category": "Institutional Regulation"
    }
  }
}
```

### `GET /api/documents`
List all uploaded and indexed documents in the active session.

#### Successful Response (`200 OK`)
```json
{
  "total_documents": 1,
  "total_runtime_chunks": 1,
  "documents": [
    {
      "doc_id": "SAMPLE_ESG_REGULATORY_DIRECTIVES_20260910_035228",
      "original_filename": "sample_esg_regulatory_directives.txt",
      "stored_filename": "sample_esg_regulatory_directives_20260910_035228.txt",
      "stored_path": "E:\\S81_kaviraja_RULER_Kalvium_Community\\data\\uploads\\sample_esg_regulatory_directives_20260910_035228.txt",
      "file_size_bytes": 1570,
      "category": "Institutional Regulation",
      "upload_timestamp": "2026-09-10T03:52:28.123456+00:00",
      "character_count": 1466,
      "token_count": 352,
      "chunks_count": 1,
      "chunk_ids": [
        "SAMPLE_ESG_REGULATORY_DIRECTIVES_20260910_035228#chunk_001"
      ]
    }
  ]
}
```

---

## 5. Verification & Testing

Run unit and integration tests:
```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_upload_indexing.py -v
```

Execute the end-to-end demonstration and generate sample artifacts:
```powershell
.\.venv\Scripts\python.exe scripts\run_upload_and_index_demo.py
```
