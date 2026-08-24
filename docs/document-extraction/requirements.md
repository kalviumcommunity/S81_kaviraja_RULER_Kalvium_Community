# Document Extraction Requirements

## Input

The pipeline accepts regulatory PDF documents.

## Supported Documents

- Text-based PDFs
- Scanned PDFs
- Image-based PDF pages

## Extraction Requirements

The pipeline should:

- Extract searchable text
- Preserve page information where possible
- Handle scanned documents through OCR
- Produce output suitable for downstream RAG processing
- Handle document-processing failures gracefully

## Planned Components

### Docling

Docling will be used for processing text-based PDF documents.

### PaddleOCR

PaddleOCR will be used when document pages contain scanned or image-based content.

## Output

The processed document should contain extracted text and relevant page information so that the next RAG stage can use it for chunking and retrieval.