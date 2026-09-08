"""
FastAPI Server for RAG Application Starter UI.
Provides REST endpoints for:
- Multi-turn structured chat completions
- Token-aware and character-based document chunking
- Exact source character-span tracing and verification
- Metadata schema consistency validation
- JSON error recovery and field validation simulations
- Serving the frontend web app
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Project internal modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from llm_client import LLMClient
from structured_output import parse_json_response, validate_required_fields, count_tokens
from chunk_metadata import DocumentChunker, trace_chunk_to_source, verify_metadata_consistency, Chunk, ChunkMetadata
from context_injection import ContextInjector, TokenBudgetConfig
from citation_attribution import attribute_answer, NO_SOURCE_FALLBACK
try:
    from src.token_chunker import TokenAwareChunker
except ImportError:
    try:
        from token_chunker import TokenAwareChunker
    except ImportError:
        TokenAwareChunker = None

try:
    from src.prompts.templates import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
except ImportError:
    try:
        from prompts.templates import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
    except ImportError:
        RAG_SYSTEM_PROMPT = None
        RAG_USER_PROMPT = None

try:
    from src.reranker import ChunkReranker, CandidateChunk
    from src.vector_db import VectorDBClient
except ImportError:
    try:
        from reranker import ChunkReranker, CandidateChunk
        from vector_db import VectorDBClient
    except ImportError:
        ChunkReranker = None
        VectorDBClient = None


app = FastAPI(
    title="RAG Application & Token Chunker Studio",
    description="Interactive Web UI and API for RAG Pipeline, Token Chunking, Source Tracing & Structured Output",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global LLM Client instance
llm_client = LLMClient(log_file=os.path.join("outputs", "sample_output.txt"))

# Base paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")


# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------

class ChatRequest(BaseModel):
    user_message: str
    system_role: Optional[str] = "RAG"
    required_fields: Optional[List[str]] = ["answer", "source", "confidence"]
    temperature: Optional[float] = 0.2
    use_mock: Optional[bool] = False


class ChunkRequest(BaseModel):
    content: Optional[str] = None
    doc_id: Optional[str] = "DOC_BRCF_2026_001"
    filename: Optional[str] = "sample_banking_regulation.txt"
    mode: Optional[str] = "token"  # 'token' or 'char'
    chunk_size: Optional[int] = 512
    chunk_overlap: Optional[int] = 64


class TraceRequest(BaseModel):
    chunk_data: Dict[str, Any]
    doc_content: Optional[str] = None


class RecoverJSONRequest(BaseModel):
    raw_json: str
    required_fields: Optional[List[str]] = ["answer", "source", "confidence"]
    default_values: Optional[Dict[str, Any]] = {"source": "Fallback_Source", "confidence": "medium"}


class RerankRequest(BaseModel):
    query: str
    initial_k: Optional[int] = 10
    top_k: Optional[int] = 3
    method: Optional[str] = "hybrid"
    candidates: Optional[List[Dict[str, Any]]] = None


def _retrieve_sample_chunks(question: str) -> List[Chunk]:
    """Retrieve local evidence for the demo chat without inventing source data."""
    chunks = []
    for filename in sorted(name for name in os.listdir(DATA_DIR) if name.endswith(".txt")):
        sample_path = os.path.join(DATA_DIR, filename)
        with open(sample_path, "r", encoding="utf-8") as source_file:
            content = source_file.read()
        chunks.extend(DocumentChunker(chunk_size=500, chunk_overlap=40).chunk_document(
            content=content,
            doc_id=os.path.splitext(filename)[0].upper(),
            filename=filename,
            source_path=os.path.join("data", filename),
        ))
    query_terms = {term.lower() for term in question.split() if len(term) > 2}
    ranked = sorted(
        chunks,
        key=lambda chunk: sum(term in chunk.text.lower() for term in query_terms),
        reverse=True,
    )
    matches = [chunk for chunk in ranked if any(term in chunk.text.lower() for term in query_terms)]
    return matches[:3]


# -------------------------------------------------------------
# API ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/status")
def get_status():
    """Returns application configuration, model settings, and pipeline health."""
    has_api_key = bool(llm_client.api_key and llm_client.api_key != "missing_api_key_placeholder")
    return {
        "status": "online",
        "base_url": llm_client.base_url,
        "model_name": llm_client.model_name,
        "has_api_key": has_api_key,
        "token_chunker_available": TokenAwareChunker is not None,
        "prompt_templates_available": RAG_SYSTEM_PROMPT is not None,
        "recorded_conversations_count": len(llm_client.get_user_questions())
    }


@app.get("/api/sample-data")
def get_sample_data():
    """Fetches default sample regulation documents and existing output summaries."""
    sample_file = os.path.join(DATA_DIR, "sample_banking_regulation.txt")
    doc_content = ""
    if os.path.exists(sample_file):
        with open(sample_file, "r", encoding="utf-8") as f:
            doc_content = f.read()

    # Read latest structured output sample if available
    structured_sample_file = os.path.join(OUTPUTS_DIR, "structured_output_sample.json")
    sample_json = {}
    if os.path.exists(structured_sample_file):
        try:
            with open(structured_sample_file, "r", encoding="utf-8") as f:
                sample_json = json.load(f)
        except Exception:
            pass

    return {
        "filename": "sample_banking_regulation.txt",
        "doc_id": "DOC_BRCF_2026_001",
        "content": doc_content,
        "character_count": len(doc_content),
        "estimated_tokens": count_tokens(doc_content),
        "structured_sample": sample_json
    }


@app.post("/api/chat")
def handle_chat(req: ChatRequest):
    """Generate a structured answer whose citations are checked against retrieved chunks."""
    retrieved_chunks = _retrieve_sample_chunks(req.user_message)
    if not retrieved_chunks:
        return {
            "success": True,
            "was_fallback": True,
            "parsed_object": {
                "answer": NO_SOURCE_FALLBACK,
                "source": None,
                "confidence": "low",
                "citations": [],
                "citation_status": "NO_RETRIEVED_SOURCES",
            },
            "token_usage": {"prompt_tokens": count_tokens(req.user_message), "completion_tokens": 0, "total_tokens": count_tokens(req.user_message)},
            "chat_history": llm_client.get_chat_history(),
        }

    injector = ContextInjector(budget_config=TokenBudgetConfig(max_answer_tokens=300))
    augmented_prompt = injector.build_augmented_prompt(
        question=req.user_message,
        retrieved_chunks=retrieved_chunks,
    )
    if RAG_SYSTEM_PROMPT and hasattr(RAG_SYSTEM_PROMPT, "render"):
        sys_prompt = RAG_SYSTEM_PROMPT.render(role=req.system_role or "RAG")
    else:
        sys_prompt = f"You are a helpful {req.system_role or 'RAG'} specialized AI assistant."

    mock_resp = None
    if req.use_mock:
        mock_resp = json.dumps({
            "answer": f"The retrieved regulation addresses '{req.user_message}'. [1]",
            "source": "sample_banking_regulation.txt",
            "confidence": "high"
        }, indent=2)

    res, usage = llm_client.create_structured_completion(
        system_message=augmented_prompt.system_prompt,
        user_message=augmented_prompt.user_prompt,
        required_fields=req.required_fields or ["answer", "source", "confidence"],
        default_values={"source": "Regulatory_Store_v1", "confidence": "high"},
        temperature=req.temperature or 0.2,
        mock_response=mock_resp
    )

    if not res:
        # Fallback if external API is unreachable or rate limited
        fallback_answer = {"answer": NO_SOURCE_FALLBACK, "source": None, "confidence": "low", "citations": [], "citation_status": "LLM_UNAVAILABLE"}
        return {
            "success": True,
            "was_fallback": True,
            "parsed_object": fallback_answer,
            "token_usage": {"prompt_tokens": count_tokens(req.user_message), "completion_tokens": 40, "total_tokens": count_tokens(req.user_message) + 40},
            "chat_history": llm_client.get_chat_history()
        }

    source_records = [
        {"marker": f"[{index}]", "doc_id": chunk.metadata.doc_id, "filename": chunk.metadata.filename,
         "source_path": chunk.metadata.source_path, "section": chunk.metadata.section,
         "page_number": chunk.metadata.page_number, "chunk_id": chunk.chunk_id,
         "chunk_index": chunk.metadata.chunk_index, "start_char": chunk.metadata.start_char,
         "end_char": chunk.metadata.end_char, "raw_text": chunk.text}
        for index, chunk in enumerate(retrieved_chunks, start=1)
    ]
    attribution = attribute_answer(res.get("answer", ""), source_records)
    res["answer"] = attribution["answer"]
    res["citations"] = attribution["citations"]
    res["citation_status"] = attribution["citation_status"]
    res["is_grounded"] = attribution["is_grounded"]
    res["source"] = ", ".join(citation["filename"] for citation in attribution["citations"]) or None

    return {
        "success": True,
        "was_fallback": False,
        "parsed_object": res,
        "token_usage": usage or {"prompt_tokens": count_tokens(req.user_message), "completion_tokens": 50, "total_tokens": count_tokens(req.user_message) + 50},
        "chat_history": llm_client.get_chat_history()
    }


@app.post("/api/chunk")
def handle_chunk(req: ChunkRequest):
    """Splits document content into structured chunks with consistent metadata tags."""
    content = req.content
    if not content:
        sample_path = os.path.join(DATA_DIR, req.filename or "sample_banking_regulation.txt")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            raise HTTPException(status_code=400, detail="No content provided and sample document not found.")

    doc_id = req.doc_id or "DOC_BRCF_2026_001"
    filename = req.filename or "sample_banking_regulation.txt"
    source_path = os.path.join("data", filename)

    if req.mode == "token" and TokenAwareChunker is not None:
        chunker = TokenAwareChunker(
            chunk_size_tokens=req.chunk_size or 512,
            chunk_overlap_tokens=req.chunk_overlap or 64
        )
        token_chunks = chunker.chunk_text(
            text=content,
            doc_id=doc_id,
            filename=filename,
            source_path=source_path
        )
        chunks_payload = [c.to_dict() for c in token_chunks]
        
        # Build standard Chunk representations for consistency check
        std_chunks = []
        for tc in token_chunks:
            meta = ChunkMetadata(
                doc_id=tc.doc_id,
                filename=tc.filename,
                source_path=tc.source_path,
                section=tc.section,
                page_number=tc.page_number,
                chunk_index=tc.chunk_index,
                total_chunks=tc.total_chunks,
                start_char=tc.start_char,
                end_char=tc.end_char
            )
            std_chunks.append(Chunk(chunk_id=tc.chunk_id, text=tc.text, metadata=meta))
        
        consistency = verify_metadata_consistency(std_chunks)
        boundary_demo = (
            chunker.demonstrate_boundary_context()
            if hasattr(chunker, "demonstrate_boundary_context")
            else (chunker.demonstrate_boundary_preservation() if hasattr(chunker, "demonstrate_boundary_preservation") else None)
        )

        return {
            "mode": "token",
            "total_chunks": len(chunks_payload),
            "chunk_size_tokens": req.chunk_size,
            "chunk_overlap_tokens": req.chunk_overlap,
            "consistency_report": consistency,
            "boundary_preservation_demo": boundary_demo,
            "chunks": chunks_payload
        }
    else:
        # Character-based DocumentChunker
        chunker = DocumentChunker(
            chunk_size=req.chunk_size or 350,
            chunk_overlap=req.chunk_overlap or 40
        )
        chunks = chunker.chunk_document(
            content=content,
            doc_id=doc_id,
            filename=filename,
            source_path=source_path
        )
        consistency = verify_metadata_consistency(chunks)
        return {
            "mode": "character",
            "total_chunks": len(chunks),
            "chunk_size": req.chunk_size,
            "chunk_overlap": req.chunk_overlap,
            "consistency_report": consistency,
            "chunks": [c.to_dict() for c in chunks]
        }


@app.post("/api/trace")
def handle_trace(req: TraceRequest):
    """Traces a selected chunk back to its source document with exact character span matching."""
    chunk_dict = req.chunk_data
    doc_content = req.doc_content

    if not doc_content:
        doc_path = os.path.join(DATA_DIR, "sample_banking_regulation.txt")
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_content = f.read()

    doc_id = chunk_dict.get("metadata", {}).get("doc_id", "DOC_BRCF_2026_001")
    corpus = {doc_id: doc_content}

    chunk_obj = Chunk.from_dict(chunk_dict)
    trace_result = trace_chunk_to_source(chunk_obj, corpus)
    return trace_result


@app.post("/api/recover-json")
def handle_recover_json(req: RecoverJSONRequest):
    """Demonstrates malformed JSON regex recovery and missing field validation."""
    parsed, was_recovered, error = parse_json_response(req.raw_json, logger=llm_client.logger)
    is_valid = False
    validated = {}
    missing = req.required_fields or []

    if parsed is not None:
        is_valid, validated, missing = validate_required_fields(
            parsed,
            required_fields=req.required_fields or ["answer", "source", "confidence"],
            default_values=req.default_values or {},
            logger=llm_client.logger
        )

    return {
        "raw_input": req.raw_json,
        "was_recovered": was_recovered,
        "parse_error": error,
        "parsed_object": parsed,
        "is_valid": is_valid,
        "missing_fields": missing,
        "final_validated_object": validated if is_valid else None
    }


@app.post("/api/rerank")
def handle_rerank(req: RerankRequest):
    """
    Two-Stage Retrieval & Re-ranking endpoint (Tasks 1 to 4).
    Accepts a query and optional candidate list, scores candidates,
    and returns before-and-after ranking comparisons.
    """
    if ChunkReranker is None:
        raise HTTPException(status_code=500, detail="ChunkReranker module is not available.")

    reranker = ChunkReranker(llm_client=llm_client)

    candidate_objs: List[CandidateChunk] = []

    if req.candidates:
        # User provided explicit candidate chunks
        for idx, c in enumerate(req.candidates, start=1):
            candidate_objs.append(
                CandidateChunk(
                    chunk_id=c.get("chunk_id", f"cand_{idx}"),
                    text=c.get("text", ""),
                    metadata=c.get("metadata", {}),
                    initial_rank=idx,
                    vector_distance=float(c.get("vector_distance", 0.2)),
                    vector_similarity=float(c.get("vector_similarity", 0.8))
                )
            )
    else:
        # Automatically retrieve candidates from Vector DB if available
        try:
            if VectorDBClient is not None:
                v_db = VectorDBClient(collection_name="reranking_precision_collection")
                if v_db.get_collection_count() == 0:
                    v_db = VectorDBClient(collection_name="document_chunks")
                
                candidate_objs = reranker.retrieve_candidate_set(
                    vector_db=v_db,
                    query=req.query,
                    initial_k=req.initial_k or 10
                )
        except Exception as e:
            # Fallback to sample regulation chunk generation if DB is empty
            from chunk_metadata import DocumentChunker
            sample_file = os.path.join(DATA_DIR, "sample_banking_regulation.txt")
            if os.path.exists(sample_file):
                with open(sample_file, "r", encoding="utf-8") as f:
                    content = f.read()
                ch_list = DocumentChunker(chunk_size=200, chunk_overlap=30).chunk_document(
                    content, "DOC_BRCF", "sample_banking_regulation.txt", sample_file
                )
                for idx, ch in enumerate(ch_list[:req.initial_k or 10], start=1):
                    sim = max(0.5, 0.95 - (idx * 0.05))
                    candidate_objs.append(
                        CandidateChunk(
                            chunk_id=ch.chunk_id,
                            text=ch.text,
                            metadata=ch.metadata.to_dict(),
                            initial_rank=idx,
                            vector_distance=1.0 - sim,
                            vector_similarity=sim
                        )
                    )

    if not candidate_objs:
        raise HTTPException(status_code=400, detail="No candidates available for re-ranking.")

    reranked_all, top_k = reranker.rerank(
        query=req.query,
        candidates=candidate_objs,
        top_k=req.top_k or 3,
        method=req.method or "hybrid"
    )

    comparison = reranker.compare_rankings(
        query=req.query,
        initial_candidates=candidate_objs,
        reranked_candidates=reranked_all,
        top_k=req.top_k or 3
    )

    return comparison


# -------------------------------------------------------------
# STATIC FILE SERVING
# -------------------------------------------------------------

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "RAG Application API running. Frontend index.html not found."}


if __name__ == "__main__":
    import uvicorn
    print("Starting RAG Application Web UI Server on http://localhost:8000 ...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
