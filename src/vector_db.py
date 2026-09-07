import os
import math
import json
import logging
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


def setup_logger():
    logger = logging.getLogger("VectorDB")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def cosine_distance(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine distance (1 - cosine_similarity)."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    sim = dot / (norm_a * norm_b)
    return max(0.0, 1.0 - sim)


class InMemoryCollection:
    """In-memory collection fallback mimicking ChromaDB collection interface."""
    def __init__(self, name: str):
        self.name = name
        self.records: List[Dict[str, Any]] = []

    def add(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]]):
        for cid, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            self.records.append({
                "id": cid,
                "embedding": emb,
                "document": doc,
                "metadata": meta
            })

    def count(self) -> int:
        return len(self.records)

    def get(self, ids: Optional[List[str]] = None, include: Optional[List[str]] = None) -> Dict[str, Any]:
        filtered = [r for r in self.records if (ids is None or r["id"] in ids)]
        return {
            "ids": [r["id"] for r in filtered],
            "embeddings": [r["embedding"] for r in filtered],
            "documents": [r["document"] for r in filtered],
            "metadatas": [r["metadata"] for r in filtered],
        }

    def query(self, query_embeddings: List[List[float]], n_results: int = 5, include: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        all_doc_results = []
        all_meta_results = []
        all_dist_results = []
        all_id_results = []

        for q_emb in query_embeddings:
            scored = []
            for r in self.records:
                if where:
                    match = True
                    for k, v in where.items():
                        if r["metadata"].get(k) != v:
                            match = False
                            break
                    if not match:
                        continue
                dist = cosine_distance(q_emb, r["embedding"])
                scored.append((dist, r))

            scored.sort(key=lambda x: x[0])
            top_k = scored[:n_results]

            all_dist_results.append([x[0] for x in top_k])
            all_doc_results.append([x[1]["document"] for x in top_k])
            all_meta_results.append([x[1]["metadata"] for x in top_k])
            all_id_results.append([x[1]["id"] for x in top_k])

        return {
            "ids": all_id_results,
            "documents": all_doc_results,
            "metadatas": all_meta_results,
            "distances": all_dist_results
        }


class VectorDBClient:
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "document_chunks"):
        self.logger = setup_logger()
        self.db_path = db_path
        self.collection_name = collection_name
        self._is_in_memory = not HAS_CHROMADB
        
        if HAS_CHROMADB:
            try:
                self.logger.info(f"Initializing ChromaDB at path: {self.db_path}")
                self.client = chromadb.PersistentClient(path=self.db_path, settings=Settings(anonymized_telemetry=False))
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                self.logger.warning(f"ChromaDB initialization failed ({e}), using in-memory vector store.")
                self._is_in_memory = True
                self.client = None
                self.collection = InMemoryCollection(collection_name)
        else:
            self.logger.info(f"ChromaDB not installed, using fast in-memory vector collection: {self.collection_name}")
            self.client = None
            self.collection = InMemoryCollection(collection_name)
        
    def add_records(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]]):
        self.logger.info(f"Adding {len(ids)} records to collection...")
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        self.logger.info("Records added successfully.")
        
    def get_record(self, record_id: str) -> Dict[str, Any]:
        self.logger.info(f"Retrieving record ID: {record_id}")
        result = self.collection.get(
            ids=[record_id],
            include=["embeddings", "documents", "metadatas"]
        )
        return result

    def get_collection_count(self) -> int:
        return self.collection.count()

    def search(self, query_embeddings: List[List[float]], n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.logger.info(f"Searching for top {n_results} matches...")
        kwargs = {
            "query_embeddings": query_embeddings,
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        if where:
            kwargs["where"] = where
            
        results = self.collection.query(**kwargs)
        return results
