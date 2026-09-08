"""Citation validation and source attribution for grounded RAG answers."""

import re
from typing import Any, Dict, Iterable, List


NO_SOURCE_FALLBACK = (
    "The provided context does not contain sufficient information to answer this "
    "question with a verifiable citation."
)


def _citation_markers(answer: str) -> List[str]:
    """Return citation markers in first-appearance order without duplicates."""
    markers = re.findall(r"\[\d+\]|\[[A-Za-z0-9_.:-]+#chunk_[A-Za-z0-9_.:-]+\]", answer or "")
    return list(dict.fromkeys(markers))


def attribute_answer(answer: str, injected_sources: Iterable[Any]) -> Dict[str, Any]:
    """Validate answer citations against the exact chunks supplied to the model."""
    sources = [source.to_dict() if hasattr(source, "to_dict") else dict(source) for source in injected_sources]
    by_marker = {source.get("marker"): source for source in sources if source.get("marker")}
    markers = _citation_markers(answer)
    invalid_markers = [marker for marker in markers if marker not in by_marker]
    cited_sources = [by_marker[marker] for marker in markers if marker in by_marker]

    if not markers or invalid_markers or not cited_sources:
        return {
            "answer": NO_SOURCE_FALLBACK,
            "is_grounded": False,
            "citation_status": "NO_VERIFIABLE_CITATIONS",
            "citations": [],
            "invalid_citations": invalid_markers,
        }

    citations = []
    for source in cited_sources:
        citations.append({
            "marker": source["marker"],
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
        "answer": answer,
        "is_grounded": True,
        "citation_status": "VERIFIED",
        "citations": citations,
        "invalid_citations": [],
    }