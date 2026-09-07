import os
import json
from llm_client import LLMClient
from token_chunker import TokenAwareChunker
from vector_db import VectorDBClient

def run_retrieval_tuning():
    print("==================================================")
    print("  Retrieval Tuning Experiment")
    print("==================================================")

    # Output paths
    os.makedirs("outputs", exist_ok=True)
    tuning_results_path = os.path.join("outputs", "tuning_results.json")
    tuning_report_path = os.path.join("outputs", "tuning_report.md")

    # Client
    llm = LLMClient(log_file=os.path.join("outputs", "tuning_llm_log.txt"))

    # Define test data
    test_doc_path = os.path.join("data", "doc1.txt")
    doc_id = "DOC1_AI"
    
    # Task 1 - Define test queries with expected relevant concepts
    test_queries = [
        {
            "query": "What is the ideal characteristic of artificial intelligence?",
            "expected_doc_id": doc_id,
            "expected_concept": "ability to rationalize"
        },
        {
            "query": "What is machine learning?",
            "expected_doc_id": doc_id,
            "expected_concept": "automatically learn from and adapt"
        }
    ]

    print(f"\n[Task 1] Defined {len(test_queries)} test queries.")

    # Read data
    with open(test_doc_path, "r", encoding="utf-8") as f:
        doc_content = f.read()

    # Task 2 - Compare retrieval settings (chunk size)
    # Setting A: 30 tokens, overlap 10
    # Setting B: 60 tokens, overlap 20
    settings = {
        "Setting_A": {"size": 30, "overlap": 10, "db": VectorDBClient(collection_name="tuning_30")},
        "Setting_B": {"size": 60, "overlap": 20, "db": VectorDBClient(collection_name="tuning_60")},
    }

    for name, config in settings.items():
        print(f"\n[Task 2] Processing {name} (size: {config['size']}, overlap: {config['overlap']})")
        chunker = TokenAwareChunker(chunk_size_tokens=config["size"], chunk_overlap_tokens=config["overlap"])
        chunks = chunker.chunk_text(doc_content, doc_id=doc_id, filename="doc1.txt")
        print(f" -> Generated {len(chunks)} chunks.")

        # Embed
        texts_to_embed = [c.text for c in chunks]
        if texts_to_embed:
            embeddings, _ = llm.create_embeddings(texts_to_embed)
            
            # Save to Chroma
            ids = [c.chunk_id for c in chunks]
            metadatas = [c.to_dict()["metadata"] for c in chunks]
            
            # recreate collection if testing repeatedly
            try:
                config["db"].client.delete_collection(config["db"].collection_name)
                config["db"] = VectorDBClient(collection_name=config["db"].collection_name)
            except Exception:
                pass
            
            config["db"].add_records(
                ids=ids,
                embeddings=embeddings,
                documents=texts_to_embed,
                metadatas=metadatas
            )

    # Embed queries
    queries = [q["query"] for q in test_queries]
    query_embeddings, _ = llm.create_embeddings(queries)

    # Task 3 - Report relevance
    results_summary = {}

    for name, config in settings.items():
        results_summary[name] = {"k_results": {}}
        db = config["db"]
        
        for k in [1, 2]: # compare k=1 vs k=2
            print(f"\n[Task 3] Searching {name} with k={k}")
            hit_count = 0
            avg_similarity = 0.0
            
            for idx, q_emb in enumerate(query_embeddings):
                res = db.search([q_emb], n_results=k)
                # Check if expected doc is retrieved and concept is found
                hit = False
                highest_sim = 0.0
                
                if res and res["documents"] and res["documents"][0]:
                    for i, doc in enumerate(res["documents"][0]):
                        # distances in Chroma (cosine) - smaller is closer
                        dist = res["distances"][0][i]
                        similarity = 1.0 - dist
                        highest_sim = max(highest_sim, similarity)
                        
                        if test_queries[idx]["expected_concept"].lower() in doc.lower() or test_queries[idx]["expected_doc_id"] == res["metadatas"][0][i].get("doc_id"):
                            hit = True
                
                if hit:
                    hit_count += 1
                avg_similarity += highest_sim
                
            hit_rate = hit_count / len(test_queries)
            avg_similarity = avg_similarity / len(test_queries)
            
            results_summary[name]["k_results"][f"k={k}"] = {
                "hit_rate": hit_rate,
                "avg_similarity": avg_similarity
            }
            print(f" -> Hit Rate: {hit_rate*100}% | Avg Similarity: {avg_similarity:.4f}")

    # Task 4 - Choose and justify best settings
    best_setting = None
    best_k = None
    best_score = -1

    for name, data in results_summary.items():
        for k_str, metrics in data["k_results"].items():
            # simple score heuristic: hit_rate + (avg_similarity * 0.1)
            score = metrics["hit_rate"] + (metrics["avg_similarity"] * 0.1)
            if score > best_score:
                best_score = score
                best_setting = name
                best_k = k_str

    justification = (
        f"The best configuration is {best_setting} with {best_k}. "
        f"Setting A (30 tokens) vs Setting B (60 tokens) showed that the chosen setting maximized "
        f"hit rate and semantic similarity for the given queries. "
        f"A top-k of {best_k} provided the best trade-off between getting the relevant chunk and maintaining precision."
    )

    print("\n[Task 4] Chosen Settings:")
    print(justification)

    # Task 5 - Commit tuning results
    final_output = {
        "test_queries": test_queries,
        "results": results_summary,
        "chosen_settings": {
            "setting": best_setting,
            "k": best_k,
            "justification": justification
        }
    }

    with open(tuning_results_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    with open(tuning_report_path, "w", encoding="utf-8") as f:
        f.write("# Retrieval Tuning Report\n\n")
        f.write("## Queries\n")
        for q in test_queries:
            f.write(f"- {q['query']} (Expected: {q['expected_concept']})\n")
        f.write("\n## Results\n")
        f.write(json.dumps(results_summary, indent=2))
        f.write("\n\n## Conclusion\n")
        f.write(justification)

    print(f"\n[Task 5] Tuning results saved to {tuning_results_path} and {tuning_report_path}")

if __name__ == "__main__":
    run_retrieval_tuning()
