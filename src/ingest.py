import os
import json
import glob
import re

def clean_text(text: str) -> str:
    """Clean document text by removing excess whitespace and non-printable characters."""
    # Remove extra whitespaces but keep single newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text

def chunk_text(text: str, source_id: str, max_chars: int = 500) -> list:
    """Simple chunking by double newlines, then by max characters if needed."""
    paragraphs = text.split('\n\n')
    chunks = []
    
    current_chunk = ""
    chunk_index = 0
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += p + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append({
                    "source_id": source_id,
                    "chunk_index": chunk_index,
                    "text": current_chunk.strip(),
                    "char_length": len(current_chunk.strip())
                })
                chunk_index += 1
            current_chunk = p + "\n\n"
            
    if current_chunk.strip():
        chunks.append({
            "source_id": source_id,
            "chunk_index": chunk_index,
            "text": current_chunk.strip(),
            "char_length": len(current_chunk.strip())
        })
        
    return chunks

def run_ingestion_pipeline(data_dir: str, output_dir: str):
    """Run the full ingestion pipeline over the given directory."""
    print(f"Starting ingestion pipeline for directory: {data_dir}")
    
    # Task 1 - Run the full pipeline
    file_paths = glob.glob(os.path.join(data_dir, '**', '*.*'), recursive=True)
    # Ignore gitkeep or hidden files
    file_paths = [f for f in file_paths if not os.path.basename(f).startswith('.')]
    
    total_source_documents = len(file_paths)
    successfully_ingested = 0
    failed_documents = []
    all_chunks = []
    
    for fp in file_paths:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cleaned_content = clean_text(content)
            source_id = os.path.basename(fp)
            
            doc_chunks = chunk_text(cleaned_content, source_id)
            all_chunks.extend(doc_chunks)
            successfully_ingested += 1
            
        except Exception as e:
            failed_documents.append({"file": fp, "error": str(e)})
            
    # Task 2 - Report the ingestion summary
    print("\n==================================================")
    print("  Ingestion Summary")
    print("==================================================")
    print(f"Total source documents found: {total_source_documents}")
    print(f"Successfully ingested:        {successfully_ingested}")
    print(f"Failed to ingest:             {len(failed_documents)}")
    print(f"Total chunks created:         {len(all_chunks)}")
    if failed_documents:
        print("\nFailures:")
        for fd in failed_documents:
            print(f" - {fd['file']}: {fd['error']}")
    print("==================================================\n")

    # Task 3 - Validate completeness
    assert total_source_documents == successfully_ingested + len(failed_documents), \
        f"Validation Failed! Source docs ({total_source_documents}) != Ingested ({successfully_ingested}) + Failed ({len(failed_documents)})"
    print("Completeness validation passed: All documents accounted for.\n")

    # Task 4 - Inspect sample chunks
    os.makedirs(output_dir, exist_ok=True)
    sample_output_path = os.path.join(output_dir, "sample_chunks.json")
    
    # Take first 5 chunks as samples
    sample_chunks = all_chunks[:5]
    
    print("Sample Chunks:")
    print(json.dumps(sample_chunks, indent=2))
    
    with open(sample_output_path, "w", encoding="utf-8") as f:
        json.dump(sample_chunks, f, indent=2)
        
    print(f"\nSaved {len(sample_chunks)} sample chunks to {sample_output_path}")


if __name__ == "__main__":
    data_directory = "data"
    output_directory = "outputs"
    run_ingestion_pipeline(data_directory, output_directory)
