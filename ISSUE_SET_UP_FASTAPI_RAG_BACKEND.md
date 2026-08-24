# Issue: Implement FastAPI RAG Backend for Regulatory Document Retrieval using Qdrant and BGE-M3

**Title:** Implement FastAPI RAG Backend for Regulatory Document Retrieval using Qdrant and BGE-M3    
**Labels:** `feature`, `rag-backend`, `fastapi`, `qdrant`, `data-pipeline`  

---

## 📝 Description

### Why This Work Matters
Regulatory documents are complex, dense, and critical for compliance and decision-making. Building an automated, scalable Retrieval-Augmented Generation (RAG) backend foundation using FastAPI, LlamaIndex, Qdrant, and BGE-M3 enables high-precision semantic search across large regulatory datasets. 

This backend acts as the core search engine for downstream LLM synthesis, ensuring that document chunks are efficiently indexed, vectorized with state-of-the-art multi-lingual/dense embeddings (BGE-M3), and quickly retrieved with metadata provenance (source, page numbers, section headers).

### Definition of Done ("What Done Means")
This issue is considered **Done** when:
1. A modular FastAPI service is structured and runnable via `uvicorn`.
2. LlamaIndex is configured with Qdrant as the vector store and BGE-M3 as the embedding model.
3. An automated chunking and indexing pipeline extracts, chunks, generates embeddings, and stores document payloads into Qdrant collections.
4. A validated API endpoint (e.g., `POST /api/v1/query`) accepts user questions and returns top-k relevant document chunks along with source metadata and similarity scores.
5. Basic error handling, logging, and environment configuration are in place.

---

## 🛠 Tasks

- [ ] **FastAPI Project Structure**: Set up FastAPI directory structure (`app/main.py`, `app/api/`, `app/core/`, `app/services/`).
- [ ] **LlamaIndex Configuration**: Initialize LlamaIndex settings and orchestrate custom node parsers/chunkers.
- [ ] **Qdrant Setup**: Configure Qdrant client connection (local/cloud instance) and vector collection initialization.
- [ ] **BGE-M3 Embeddings Integration**: Configure BGE-M3 embedding model provider within the LlamaIndex embedding interface.
- [ ] **Document Chunking & Indexing Pipeline**: Implement document loading, splitting into semantic chunks, and node creation.
- [ ] **Vector Storage & Embedding Generation**: Generate BGE-M3 dense embeddings and persist chunk nodes with metadata into Qdrant.
- [ ] **Query API Endpoint**: Create API endpoint (e.g., `POST /api/v1/query` or `POST /retrieve`) accepting search queries and parameters.
- [ ] **Response Formatting**: Format endpoint output to include retrieved text snippets, score metrics, document metadata (file name, page, title).

---

## 🎯 Expected Output

A functional FastAPI backend service providing an endpoint where clients submit natural language questions and receive accurate regulatory document chunks.

### Sample Endpoint Payload

#### **Request:** `POST /api/v1/query`
```json
{
  "query": "What are the compliance requirements for data privacy under Article 5?",
  "top_k": 3
}
```

#### **Response:** `200 OK`
```json
{
  "query": "What are the compliance requirements for data privacy under Article 5?",
  "results": [
    {
      "chunk_id": "chunk-102948",
      "content": "Article 5 requires personal data to be processed lawfully, fairly, and in a transparent manner...",
      "score": 0.892,
      "source_info": {
        "document_name": "regulatory_compliance_guidelines_2024.pdf",
        "page_number": 14,
        "section": "Article 5 - General Principles"
      }
    }
  ]
}
```
