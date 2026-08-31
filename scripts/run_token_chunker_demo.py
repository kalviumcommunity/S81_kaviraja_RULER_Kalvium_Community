"""
Token-Aware Chunker Execution & Output Generator (Tasks 1 - 5).

Executes token-aware chunking on sample documents, demonstrates boundary context preservation,
applies settings justification, and persists output artifacts.
"""

import os
import json
import sys

# Ensure src directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from token_chunker import TokenAwareChunker, TokenChunk


def run_token_chunker_pipeline():
    print("==================================================================")
    print("        RAG Pipeline — Token-Aware Chunker Engine Demo           ")
    print("==================================================================\n")

    outputs_dir = "outputs"
    os.makedirs(outputs_dir, exist_ok=True)

    json_output_path = os.path.join(outputs_dir, "token_chunker_results.json")
    txt_output_path = os.path.join(outputs_dir, "token_chunker_output.txt")

    # Task 1 & 2: Initialize token-aware chunker with justified settings
    chunk_size = 512
    chunk_overlap = 64
    encoding_name = "cl100k_base"

    print(f"[Task 1 & 2] Initializing TokenAwareChunker (Size: {chunk_size} tokens, Overlap: {chunk_overlap} tokens, Encoding: {encoding_name})...")
    chunker = TokenAwareChunker(
        chunk_size_tokens=chunk_size,
        chunk_overlap_tokens=chunk_overlap,
        encoding_name=encoding_name
    )

    # Load corpus documents or fallback sample text
    sample_docs = []

    corpus_dir = os.path.join("data", "sample_corpus")
    doc_paths = [
        os.path.join("data", "sample_banking_regulation.txt"),
        os.path.join(corpus_dir, "banking_policy.pdf"),
        os.path.join(corpus_dir, "compliance_faq.html"),
        os.path.join(corpus_dir, "rag_architecture.md"),
        os.path.join(corpus_dir, "system_notes.txt"),
    ]

    loaded_text = ""
    for path in doc_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if content.strip():
                        sample_docs.append((path, os.path.basename(path), content))
                        loaded_text += content + "\n\n"
            except Exception as e:
                print(f"  [Warning] Could not read {path}: {e}")

    if not loaded_text.strip():
        # Baseline fallback document if files are missing
        loaded_text = (
            "# Global Banking Compliance & Regulatory Framework 2026\n\n"
            "## Section 1: Executive Summary & Overview\n"
            "Financial institutions operating within international jurisdictions must establish automated compliance "
            "monitoring systems to detect, prevent, and report suspicious transactions under Anti-Money Laundering (AML) "
            "and Counter-Terrorism Financing (CTF) directives. All automated systems must evaluate transaction velocities, "
            "beneficiary country risk scores, and entity sanction lists in real time prior to authorization.\n\n"
            "## Section 2: Capital Reserves & Liquidity Ratios\n"
            "Under Basel IV capital adequacy standards, Tier 1 common equity capital must remain above 10.5% of total "
            "risk-weighted assets at all times. In addition, institutions must hold high-quality liquid assets (HQLA) "
            "sufficient to cover total net cash outflows over a 30-day stress period. "
            "The Liquidity Coverage Ratio (LCR) must be calculated daily and submitted to regional financial regulatory bodies.\n\n"
            "## Section 3: High-Value Transaction Authorization Thresholds\n"
            "Standard retail banking policies mandate that routine vendor payments under $50,000 may be approved directly "
            "by designated department heads without requiring senior executive approval. "
            "However, any single capital expenditure or vendor disbursement exceeding $50,000 requires unanimous board authorization "
            "and an independent audit report prior to disbursement. "
            "Failure to obtain board authorization for high-value transactions results in immediate suspension of procurement privileges "
            "and mandatory compliance audit review."
        )
        sample_docs.append(("data/sample_banking_regulation.txt", "sample_banking_regulation.txt", loaded_text))

    print(f" -> Loaded {len(sample_docs)} source document(s) for token chunking.")

    all_chunks: list[TokenChunk] = []

    for path, filename, content in sample_docs:
        doc_id = filename.replace(".", "_")
        doc_chunks = chunker.chunk_text(
            text=content,
            doc_id=doc_id,
            filename=filename,
            source_path=path,
            section="Document Body"
        )
        all_chunks.extend(doc_chunks)

    print(f" -> Generated total of {len(all_chunks)} token-aware chunks across corpus.\n")

    # Task 3: Execute boundary context preservation demonstration
    print("[Task 3] Executing Boundary Context Preservation Demonstration (With vs Without Overlap)...")
    boundary_demo = chunker.demonstrate_boundary_context()
    print(" -> Boundary context demonstration executed successfully.")

    # Task 4: Execute settings justification
    print("[Task 4] Generating Token Size and Overlap Technical Justification...")
    justification = chunker.justify_settings()
    print(" -> Settings justification report generated.")

    # Task 5: Persist results JSON & TXT output logs
    print("[Task 5] Persisting Chunk Output and Verification Reports...")

    results_payload = {
        "token_chunker_version": "1.0.0",
        "settings_justification": justification,
        "boundary_context_demonstration": boundary_demo,
        "chunking_summary": {
            "total_documents_processed": len(sample_docs),
            "total_chunks_generated": len(all_chunks),
            "configured_chunk_size_tokens": chunk_size,
            "configured_overlap_tokens": chunk_overlap,
            "encoding_name": encoding_name
        },
        "sample_chunks": [c.to_dict() for c in all_chunks]
    }

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    # Format human-readable output text log
    with open(txt_output_path, "w", encoding="utf-8") as f:
        f.write("==================================================================\n")
        f.write("        RAG PIPELINE — TOKEN-AWARE CHUNKER EXECUTION REPORT       \n")
        f.write("==================================================================\n\n")

        f.write("--- TASK 1 & TASK 2: CONFIGURATION & SUMMARY ---\n")
        f.write(f"Encoding Engine: {encoding_name}\n")
        f.write(f"Chunk Size Limit: {chunk_size} tokens\n")
        f.write(f"Controlled Overlap: {chunk_overlap} tokens ({round(chunk_overlap/chunk_size*100, 1)}%)\n")
        f.write(f"Total Documents Processed: {len(sample_docs)}\n")
        f.write(f"Total Chunks Generated: {len(all_chunks)}\n\n")

        f.write("--- TASK 3: BOUNDARY CONTEXT DEMONSTRATION ---\n")
        f.write("Target Passage:\n")
        f.write(f"\"{boundary_demo['target_passage']}\"\n\n")

        f.write("1. WITHOUT OVERLAP (Overlap = 0 tokens):\n")
        f.write(f"   Chunk 1: \"{boundary_demo['without_overlap']['chunk_1_full']}\"\n")
        f.write(f"   Chunk 2: \"{boundary_demo['without_overlap']['chunk_2_full']}\"\n")
        f.write(f"   Issue: {boundary_demo['without_overlap']['boundary_issue']}\n\n")

        f.write("2. WITH CONTROLLED OVERLAP (Overlap = 12 tokens):\n")
        f.write(f"   Chunk 1: \"{boundary_demo['with_overlap']['chunk_1_full']}\"\n")
        f.write(f"   Chunk 2: \"{boundary_demo['with_overlap']['chunk_2_full']}\"\n")
        f.write(f"   Repeated Overlap Snippet: \"{boundary_demo['with_overlap']['overlapping_repeated_text']}\"\n")
        f.write(f"   Context Result: {boundary_demo['with_overlap']['preserved_boundary_context']}\n\n")

        f.write("--- TASK 4: TECHNICAL JUSTIFICATION ---\n")
        f.write(f"Target Model Family: {justification['model_family']}\n")
        for key, val in justification['justifications'].items():
            f.write(f"- {key.upper()}: {val}\n")
        f.write("\n")

        f.write("--- TASK 5: SAMPLE CHUNKS PREVIEW ---\n")
        for idx, chunk in enumerate(all_chunks[:5], 1):
            f.write(f"Chunk #{idx} [{chunk.chunk_id}]:\n")
            f.write(f"  Source: {chunk.filename} ({chunk.source_path})\n")
            f.write(f"  Token Count: {chunk.token_count} tokens (Range: {chunk.start_token} -> {chunk.end_token})\n")
            f.write(f"  Overlap Tokens: {chunk.overlap_tokens} tokens\n")
            f.write(f"  Char Bounds: [{chunk.start_char}, {chunk.end_char}]\n")
            f.write(f"  Text Preview: \"{chunk.text[:150]}...\"\n")
            f.write("------------------------------------------------------------------\n")

    print(f" -> Persisted JSON results to: '{json_output_path}'")
    print(f" -> Persisted human-readable log to: '{txt_output_path}'")
    print("\n==================================================================")
    print("      TOKEN-AWARE CHUNKER DEMO EXECUTED SUCCESSFULLY!            ")
    print("==================================================================")


if __name__ == "__main__":
    run_token_chunker_pipeline()
