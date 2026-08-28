# RAG Assistant Architecture Overview

## Executive Summary
This document specifies the technical architecture of our Retrieval-Augmented Generation (RAG) assistant.

## Key Subsystems
1. **Document Extraction Engine**: Parses heterogeneous source documents (PDF, HTML, Markdown, TXT) into plain text representations tagged with source metadata.
2. **Vector Store & Indexing**: Employs dense vector embeddings stored in ChromaDB for high-dimensional semantic search.
3. **LLM Orchestration**: Combines retrieved context with structured system prompts to generate grounded, fact-checked responses.

## Performance Metrics
- **Retrieval Latency Target**: < 150ms per query
- **Context Groundedness Score**: > 0.95 factuality threshold
