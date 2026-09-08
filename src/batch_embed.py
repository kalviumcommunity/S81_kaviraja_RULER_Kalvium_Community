import os
import json
import hashlib
from typing import List, Dict, Any
from llm_client import LLMClient

# Constants
COST_PER_1M_TOKENS = 0.02
BATCH_SIZE = 5

def compute_hash(text: str) -> str:
    """Compute MD5 hash for a text to uniquely identify it."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def batch_generator(data: List[Any], batch_size: int):
    """Yield successive batches from a list."""
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

def load_json(path: str, default: Any = None) -> Any:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else []

def save_json(data: Any, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def run_batch_embedding_pipeline():
    chunks_path = os.path.join("outputs", "sample_chunks.json")
    cache_path = os.path.join("outputs", "embeddings_cache.json")
    log_output_path = os.path.join("outputs", "batch_embed_log.txt")

    if not os.path.exists(chunks_path):
        print(f"Error: {chunks_path} not found. Run ingest.py first to generate chunks.")
        return

    print("==================================================")
    print("  Batch Embedding Pipeline Started")
    print("==================================================")

    # Initialize client
    client = LLMClient(log_file=log_output_path)
    
    # Load chunks and cache
    chunks = load_json(chunks_path)
    cache = load_json(cache_path, default={})
    
    total_chunks = len(chunks)
    skipped_chunks = 0
    failed_chunks = 0
    embedded_chunks = 0
    total_tokens = 0
    
    # Filter chunks that need embedding
    chunks_to_embed = []
    chunk_hashes = []
    
    for chunk in chunks:
        text = chunk["text"]
        chunk_hash = compute_hash(text)
        if chunk_hash in cache:
            skipped_chunks += 1
        else:
            chunks_to_embed.append(chunk)
            chunk_hashes.append(chunk_hash)
            
    print(f"Total chunks: {total_chunks}")
    print(f"Already embedded (skipping): {skipped_chunks}")
    print(f"Chunks to embed: {len(chunks_to_embed)}\n")
    
    if chunks_to_embed:
        print(f"Processing in batches of {BATCH_SIZE}...")
        
        for batch_idx, batch_data in enumerate(batch_generator(list(zip(chunks_to_embed, chunk_hashes)), BATCH_SIZE)):
            batch_chunks, batch_hashes = zip(*batch_data)
            batch_texts = [c["text"] for c in batch_chunks]
            
            try:
                embeddings, usage = client.create_embeddings(batch_texts)
                
                # Update cache
                for chunk, c_hash, emb in zip(batch_chunks, batch_hashes, embeddings):
                    cache[c_hash] = {
                        "source_id": chunk["source_id"],
                        "chunk_index": chunk["chunk_index"],
                        "embedding": emb
                    }
                
                embedded_chunks += len(batch_texts)
                total_tokens += usage.get("total_tokens", 0)
                
                print(f" - Batch {batch_idx + 1} succeeded: Embedded {len(batch_texts)} chunks.")
                
            except Exception as e:
                print(f" - Batch {batch_idx + 1} failed: {str(e)}")
                failed_chunks += len(batch_texts)
                
        # Save updated cache
        save_json(cache, cache_path)
        print(f"\nSaved embeddings to {cache_path}")
    else:
        print("No new chunks to embed.")

    # Calculate approximate cost
    approximate_cost = (total_tokens / 1_000_000) * COST_PER_1M_TOKENS

    print("\n==================================================")
    print("  Run Summary")
    print("==================================================")
    print(f"Total chunks processed: {total_chunks}")
    print(f"Embeddings generated:   {embedded_chunks}")
    print(f"Skipped chunks:         {skipped_chunks}")
    print(f"Failed chunks:          {failed_chunks}")
    print(f"Total tokens used:      {total_tokens}")
    print(f"Approximate cost:       ${approximate_cost:.6f}")
    print("==================================================")

if __name__ == "__main__":
    run_batch_embedding_pipeline()
