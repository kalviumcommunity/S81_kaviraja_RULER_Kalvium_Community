"""
Script to generate a sample multi-format corpus for RAG document loader testing.
Generates PDF, HTML, Markdown, Plain Text, Corrupt PDF, and Unsupported files.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

CORPUS_DIR = os.path.join("data", "sample_corpus")


def generate_pdf(filepath):
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Global Banking Regulatory Compliance Framework 2026")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 720, "1. Capital Adequacy Ratio (CAR)")
    c.setFont("Helvetica", 10)
    c.drawString(50, 700, "Commercial financial institutions must maintain a minimum Common Equity Tier 1 (CET1)")
    c.drawString(50, 685, "capital ratio of 4.5% of risk-weighted assets at all times to absorb unexpected losses.")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 650, "2. Anti-Money Laundering (AML) Protocols")
    c.setFont("Helvetica", 10)
    c.drawString(50, 630, "Customer Due Diligence (CDD) and Enhanced Due Diligence (EDD) must be conducted")
    c.drawString(50, 615, "for all high-risk accounts. Suspicious Activity Reports (SARs) must be submitted")
    c.drawString(50, 600, "to regulatory authorities within 30 days of initial detection.")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 565, "3. Liquidity Coverage Ratio (LCR)")
    c.setFont("Helvetica", 10)
    c.drawString(50, 545, "Financial institutions are required to hold unencumbered High Quality Liquid Assets (HQLA)")
    c.drawString(50, 530, "sufficient to cover net cash outflows over a 30-day severe stress period.")

    c.save()
    print(f"Created PDF sample: {filepath}")


def generate_html(filepath):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Compliance FAQ & Operational Guidelines</title>
</head>
<body>
    <h1>Compliance FAQ & Operational Guidelines</h1>
    <section>
        <h2>Data Governance & Privacy</h2>
        <p>All sensitive customer financial records must be encrypted at rest using AES-256 standards. Access is strictly granted based on Least Privilege principles.</p>
    </section>
    <section>
        <h2>Audit Protocols</h2>
        <p>Internal compliance audits are mandated bi-annually. External third-party security assessments must be performed annually.</p>
        <ul>
            <li>Quarterly access log reviews</li>
            <li>Incident response drills every six months</li>
            <li>Real-time transaction monitoring for anomalous behavior</li>
        </ul>
    </section>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Created HTML sample: {filepath}")


def generate_markdown(filepath):
    md_content = """# RAG Assistant Architecture Overview

## Executive Summary
This document specifies the technical architecture of our Retrieval-Augmented Generation (RAG) assistant.

## Key Subsystems
1. **Document Extraction Engine**: Parses heterogeneous source documents (PDF, HTML, Markdown, TXT) into plain text representations tagged with source metadata.
2. **Vector Store & Indexing**: Employs dense vector embeddings stored in ChromaDB for high-dimensional semantic search.
3. **LLM Orchestration**: Combines retrieved context with structured system prompts to generate grounded, fact-checked responses.

## Performance Metrics
- **Retrieval Latency Target**: < 150ms per query
- **Context Groundedness Score**: > 0.95 factuality threshold
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Created Markdown sample: {filepath}")


def generate_txt(filepath):
    txt_content = """RAG Application System Notes & Operations Log

1. Operational Status: All core indexing microservices are operational.
2. Indexing Strategy: Incremental document loading enabled with source citation tagging.
3. Support Contact: Engineering team contact email is dev-support@bank-rag-app.internal.
4. Maintenance Window: Scheduled index maintenance occurs every Sunday at 02:00 UTC.
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(txt_content)
    print(f"Created TXT sample: {filepath}")


def generate_corrupt_pdf(filepath):
    # Header resembling PDF but containing completely invalid corrupt byte sequence
    corrupt_bytes = b"%PDF-1.4\n%INVALID_BINARY_HEADER\n\xFF\xFE\xFD\xFCBROKEN_STREAM_DATA_CORRUPTED_EOF"
    with open(filepath, "wb") as f:
        f.write(corrupt_bytes)
    print(f"Created Corrupt PDF sample: {filepath}")


def generate_unsupported_file(filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("Unsupported Binary DOCX Format Sample Content")
    print(f"Created Unsupported file sample: {filepath}")


def main():
    os.makedirs(CORPUS_DIR, exist_ok=True)
    generate_pdf(os.path.join(CORPUS_DIR, "banking_policy.pdf"))
    generate_html(os.path.join(CORPUS_DIR, "compliance_faq.html"))
    generate_markdown(os.path.join(CORPUS_DIR, "rag_architecture.md"))
    generate_txt(os.path.join(CORPUS_DIR, "system_notes.txt"))
    generate_corrupt_pdf(os.path.join(CORPUS_DIR, "corrupt_doc.pdf"))
    generate_unsupported_file(os.path.join(CORPUS_DIR, "unsupported_doc.docx"))
    print("\nSample corpus generation complete.")


if __name__ == "__main__":
    main()
