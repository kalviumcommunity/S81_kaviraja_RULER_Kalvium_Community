"""
RAG Application Starter - Main Entry Point for Multi-Format Document Loader.

Demonstrates Tasks 1 to 5:
- Task 1: Load documents in multiple formats (PDF, HTML, MD, TXT) into common plain text.
- Task 2: Handle missing, corrupt, and unsupported files gracefully without crashing.
- Task 3: Preserve source identity metadata for citation.
- Task 4: Confirm intake with text length and sample preview outputs.
- Task 5: Execute over sample corpus in data/sample_corpus/ and save intake logs.
"""

import os
import json
from document_loader import DocumentLoader, Document


def main():
    corpus_dir = os.path.join("data", "sample_corpus")
    output_log_path = os.path.join("outputs", "sample_output.txt")
    results_json_path = os.path.join("outputs", "document_loader_results.json")

    os.makedirs("outputs", exist_ok=True)

    print("==================================================================")
    print("      RAG Assistant — Multi-Format Document Loader Demo           ")
    print("==================================================================\n")

    loader = DocumentLoader()

    # Ensure sample corpus exists
    if not os.path.exists(corpus_dir):
        print(f"Sample corpus directory '{corpus_dir}' not found. Generating sample corpus...")
        import subprocess
        subprocess.run(["python", "scripts/generate_sample_corpus.py"], check=True)

    # --------------------------------------------------------------------
    # Define batch list including valid documents, corrupt file, unsupported format, and a missing file
    # --------------------------------------------------------------------
    batch_files = [
        os.path.join(corpus_dir, "banking_policy.pdf"),     # Task 1: PDF format
        os.path.join(corpus_dir, "compliance_faq.html"),    # Task 1: HTML format
        os.path.join(corpus_dir, "rag_architecture.md"),    # Task 1: Markdown format
        os.path.join(corpus_dir, "system_notes.txt"),       # Task 1: Plain Text format
        os.path.join(corpus_dir, "corrupt_doc.pdf"),        # Task 2: Corrupt file
        os.path.join(corpus_dir, "unsupported_doc.docx"),   # Task 2: Unsupported extension
        os.path.join(corpus_dir, "non_existent_file.pdf"),  # Task 2: Missing file
    ]

    print("[Task 1, 2 & 3] Loading multi-format corpus with source identity & error handling...\n")
    documents = loader.load_batch(batch_files)

    # --------------------------------------------------------------------
    # Task 4: Confirm Intake with formatted output
    # --------------------------------------------------------------------
    loader.print_intake_summary(documents)

    # Save results to JSON
    json_output = [doc.to_dict() for doc in documents]
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2)

    # Write summary text log to outputs/sample_output.txt
    with open(output_log_path, "w", encoding="utf-8") as f:
        f.write("RAG DOCUMENT LOADER EXECUTION LOG\n")
        f.write("==================================================\n\n")
        for doc in documents:
            f.write(f"Source: {doc.source}\n")
            f.write(f"Filename: {doc.filename}\n")
            f.write(f"Format: {doc.format}\n")
            f.write(f"Status: {doc.status}\n")
            if doc.status == "success":
                f.write(f"Length: {doc.char_count} chars, {doc.word_count} words\n")
                f.write(f"Preview: {doc.preview(100)}\n")
            else:
                f.write(f"Error: {doc.error_message}\n")
            f.write("--------------------------------------------------\n\n")

    print("[Task 5] Results successfully persisted:")
    print(f"  - Summary JSON: {results_json_path}")
    print(f"  - Detailed Log: {output_log_path}")
    print("\n==================================================================")
    print("  ALL TASKS COMPLETED SUCCESSFULLY!                               ")
    print("==================================================================")


if __name__ == "__main__":
    main()
