import os
import sys
import json

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.vector_db import VectorDBClient

def main():
    print("--- Testing Vector Database Setup ---")
    
    # Task 1 & 2: Set up Vector DB and create collection
    db_client = VectorDBClient(db_path="./chroma_db", collection_name="test_collection")
    
    # Task 3: Design schema 
    # ID: string (e.g., 'doc1_chunk1')
    # Vector: list of floats (simulating a 1536-dimensional embedding from text-embedding-3-small)
    # Text: Source document text chunk
    # Metadata: {source_document: str, chunk_index: int, section: str, page: int}
    
    # Task 4: Insert and read back a test record
    test_id = "doc1_chunk1"
    
    # Simulating a vector of size 1536 for text-embedding-3-small
    test_embedding = [0.01] * 1536 
    
    test_text = "This is a test document chunk that contains information about vector databases."
    
    test_metadata = {
        "source_document": "vector_db_guide.pdf",
        "chunk_index": 1,
        "section": "Introduction",
        "page": 2
    }
    
    # Insert record
    print(f"\nInserting test record '{test_id}'...")
    db_client.add_records(
        ids=[test_id],
        embeddings=[test_embedding],
        documents=[test_text],
        metadatas=[test_metadata]
    )
    
    # Read back the record
    print(f"\nReading back record '{test_id}'...")
    result = db_client.get_record(test_id)
    
    print("\n--- Readback Output ---")
    print(f"ID: {result['ids'][0] if result.get('ids') else 'Not Found'}")
    
    if result.get("embeddings") is not None and len(result["embeddings"]) > 0:
        vector_length = len(result["embeddings"][0])
        print(f"Vector Length: {vector_length}")
    else:
        print("Vector Length: Not Found")
        
    print(f"Text: {result['documents'][0] if result.get('documents') else 'Not Found'}")
    
    if result.get("metadatas") is not None and len(result["metadatas"]) > 0:
        metadata_str = json.dumps(result["metadatas"][0], indent=2)
        print(f"Metadata:\n{metadata_str}")
    else:
        print("Metadata: Not Found")
        
    print(f"\nTotal Collection Count: {db_client.get_collection_count()}")
    
    # Save output to file for commit
    os.makedirs("./outputs", exist_ok=True)
    with open("./outputs/vector_db_test_output.txt", "w") as f:
        f.write("--- Readback Output ---\n")
        f.write(f"ID: {result['ids'][0]}\n")
        f.write(f"Vector Length: {vector_length}\n")
        f.write(f"Text: {result['documents'][0]}\n")
        f.write(f"Metadata:\n{metadata_str}\n")
        f.write(f"Total Collection Count: {db_client.get_collection_count()}\n")

    print("\nOutput saved to ./outputs/vector_db_test_output.txt")

if __name__ == "__main__":
    main()
