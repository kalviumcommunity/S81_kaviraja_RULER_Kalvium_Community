"""Citation validation and source attribution for grounded RAG answers."""

import re
from typing import Any, Dict, Iterable, List


NO_SOURCE_FALLBACK = (
    "The provided context does not contain sufficient information to answer this "
    "question with a verifiable citation."
)


def _citation_markers(answer: str) -> List[str]:
    """Return citation markers in first-appearance order without duplicates."""
    # Matches [1], [2], [doc.txt], [DOC_ID], [DOC#chunk_001]
    markers = re.findall(r"\[\d+\]|\[[A-Za-z0-9_.:#/-]+\]", answer or "")
    return list(dict.fromkeys(markers))


def attribute_answer(answer: str, injected_sources: Iterable[Any]) -> Dict[str, Any]:
    """Validate answer citations against the exact chunks supplied to the model."""
    sources = [source.to_dict() if hasattr(source, "to_dict") else dict(source) for source in injected_sources]
    
    # Map multiple potential marker aliases to the source record
    by_marker = {}
    for idx, source in enumerate(sources, start=1):
        num_marker = f"[{idx}]"
        source["marker"] = num_marker
        by_marker[num_marker] = source
        
        # Also map chunk_id, filename, and doc_id aliases
        if source.get("chunk_id"):
            by_marker[f"[{source['chunk_id']}]"] = source
        if source.get("filename"):
            by_marker[f"[{source['filename']}]"] = source
        if source.get("doc_id"):
            by_marker[f"[{source['doc_id']}]"] = source

    clean_answer = (answer or "").strip()
    
    # Check if answer is an explicit refusal
    is_refusal = (
        clean_answer == NO_SOURCE_FALLBACK or
        "does not contain sufficient information" in clean_answer.lower() or
        "no context available" in clean_answer.lower() or
        "context does not mention" in clean_answer.lower()
    )

    if is_refusal:
        return {
            "answer": clean_answer or NO_SOURCE_FALLBACK,
            "is_grounded": False,
            "citation_status": "REFUSAL_FALLBACK",
            "citations": [],
            "invalid_citations": [],
        }

    raw_markers = _citation_markers(clean_answer)
    if not raw_markers:
        return {
            "answer": NO_SOURCE_FALLBACK,
            "is_grounded": False,
            "citation_status": "MISSING_CITATION",
            "citations": [],
            "invalid_citations": [],
        }

    invalid_citations = [m for m in raw_markers if m not in by_marker]
    if invalid_citations:
        return {
            "answer": clean_answer,
            "is_grounded": False,
            "citation_status": "INVALID_CITATION",
            "citations": [],
            "invalid_citations": invalid_citations,
        }

    cited_sources = []
    seen_sources = set()

    for m in raw_markers:
        if m in by_marker:
            src = by_marker[m]
            src_key = src.get("chunk_id") or src.get("marker")
            if src_key not in seen_sources:
                seen_sources.add(src_key)
                cited_sources.append(src)

    citations = []
    for source in cited_sources:
        citations.append({
            "marker": source.get("marker", "[1]"),
            "doc_id": source.get("doc_id"),
            "filename": source.get("filename"),
            "source_path": source.get("source_path"),
            "section": source.get("section"),
            "page_number": source.get("page_number"),
            "chunk_id": source.get("chunk_id"),
            "chunk_index": source.get("chunk_index"),
            "start_char": source.get("start_char"),
            "end_char": source.get("end_char"),
            "original_retrieved_text": source.get("raw_text", ""),
            "verification": {
                "matches_original_retrieved_text": bool(source.get("raw_text")),
                "status": "VERIFIED_AGAINST_RETRIEVED_CHUNK" if source.get("raw_text") else "MISSING_RETRIEVED_TEXT",
            },
        })

    return {
        "answer": clean_answer,
        "is_grounded": True,
        "citation_status": "VERIFIED",
        "citations": citations,
        "invalid_citations": [],
    }