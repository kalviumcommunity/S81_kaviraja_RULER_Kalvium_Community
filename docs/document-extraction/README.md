# Document Extraction and OCR Pipeline

This module will provide document extraction for the Banking Regulatory RAG application.

The pipeline needs to support two types of regulatory PDFs:

1. Normal text-based PDFs
2. Scanned or image-based PDFs

## Planned Processing Flow

PDF Input
    ↓
Document Type Detection
    ↓
Text Extraction
    ↓
OCR for Scanned Documents
    ↓
Page Information Preservation
    ↓
Processed Document Output
    ↓
Next RAG Processing Stage

## Planned Tools

- Docling for normal PDF/document processing
- PaddleOCR for scanned and image-based PDFs

The implementation will be added in a later development stage.