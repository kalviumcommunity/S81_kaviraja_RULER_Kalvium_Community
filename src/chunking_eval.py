import os
import json

def read_document(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# Strategy A: Fixed-size with overlap
def chunk_fixed_size_overlap(text: str, chunk_size: int = 150, overlap: int = 30) -> list:
    """Chunks text into fixed-size character windows with a sliding overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        chunks.append({
            "strategy": "Fixed-size with overlap",
            "text": chunk_text,
            "char_length": len(chunk_text)
        })
        start += (chunk_size - overlap)
    return chunks

# Strategy B: Paragraph-based grouping
def chunk_paragraph_based(text: str, max_chars: int = 250) -> list:
    """Chunks text by paragraph boundaries, grouping them up to a max char limit."""
    # Normalize double newlines and split
    text = text.replace('\r\n', '\n')
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += p + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append({
                    "strategy": "Paragraph-based",
                    "text": current_chunk.strip(),
                    "char_length": len(current_chunk.strip())
                })
            current_chunk = p + "\n\n"
            
    if current_chunk.strip():
        chunks.append({
            "strategy": "Paragraph-based",
            "text": current_chunk.strip(),
            "char_length": len(current_chunk.strip())
        })
        
    return chunks

def calculate_stats(chunks: list) -> dict:
    count = len(chunks)
    avg_size = sum(c["char_length"] for c in chunks) / count if count > 0 else 0
    return {
        "count": count,
        "avg_size": round(avg_size, 2)
    }

def main():
    doc_path = os.path.join("data", "doc1.txt")
    if not os.path.exists(doc_path):
        print(f"Error: {doc_path} not found. Please run the ingestion script first to generate sample data.")
        return
        
    text = read_document(doc_path)
    
    print("==================================================")
    print("  Chunking Strategy Evaluation")
    print("==================================================\n")
    print(f"Document: {doc_path} (Total Length: {len(text)} chars)\n")
    
    # Run strategies
    strategy_a_chunks = chunk_fixed_size_overlap(text, chunk_size=150, overlap=30)
    strategy_b_chunks = chunk_paragraph_based(text, max_chars=300)
    
    # Calculate stats
    stats_a = calculate_stats(strategy_a_chunks)
    stats_b = calculate_stats(strategy_b_chunks)
    
    print("--- Strategy A: Fixed-size with Overlap (150 chars, 30 overlap) ---")
    print(f"Total Chunks: {stats_a['count']}")
    print(f"Average Chunk Size: {stats_a['avg_size']} chars\n")
    
    print("--- Strategy B: Paragraph-based Grouping (Max 300 chars) ---")
    print(f"Total Chunks: {stats_b['count']}")
    print(f"Average Chunk Size: {stats_b['avg_size']} chars\n")
    
    # Justification
    print("==================================================")
    print("  Justification for Chosen Strategy")
    print("==================================================")
    justification = (
        "Chosen Strategy: Strategy B (Paragraph-based Grouping).\n\n"
        "Why it fits this corpus:\n"
        "1. Semantic Preservation: Fixed-size chunking blindly cuts sentences in half, "
        "leaving critical context dangling (e.g., separating a subject from its verb). "
        "Paragraph chunking respects natural semantic boundaries authored by the writer.\n"
        "2. Retrieval Accuracy: Retrieving half a sentence reduces the LLM's ability to "
        "ground its generation properly. The paragraph-based approach ensures entire concepts "
        "are retrieved together.\n"
        "3. Less Redundancy: Fixed-overlap causes duplicated context in the index, whereas "
        "clean paragraph splitting minimizes token waste during generation."
    )
    print(justification)
    print("==================================================\n")
    
    # Save outputs
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "chunking_comparison.json")
    
    combined_output = {
        "document": doc_path,
        "strategy_a_fixed_size": strategy_a_chunks,
        "strategy_b_paragraph_based": strategy_b_chunks,
        "justification": justification
    }
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(combined_output, f, indent=2)
        
    print(f"Saved sample chunks for both strategies to: {out_path}")

if __name__ == "__main__":
    main()
