"""
MongoDB-Backed Vector & Document Embedding Store for RULER Platform.

Replaces ChromaDB and external database engines with a unified MongoDB vector store:
- Persists high-dimensional vector embeddings, chunks, and metadata in MongoDB.
- Computes exact cosine similarity and rank scores.
- Provides fallback in-memory collection cache if MongoDB is offline.
"""

import os
import math
import json
import logging
from typing import List, Dict, Any, Optional

try:
    from database import db_client
except ImportError:
    try:
        from src.database import db_client
    except ImportError:
        db_client = None


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
    if not vec_a or not vec_b:
        return 1.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    sim = dot / (norm_a * norm_b)
    return max(0.0, 1.0 - sim)


class MongoVectorCollection:
    """
    MongoDB collection wrapper supporting vector embedding addition,
    cosine similarity querying, metadata filtering, and retrieval.
    """

    def __init__(self, collection_name: str = "document_chunks"):
        self.collection_name = collection_name
        self.logger = setup_logger()
        # In-memory buffer fallback
        self._memory_records: List[Dict[str, Any]] = []

    def _get_mongo_coll(self):
        if db_client is not None and db_client.is_connected and db_client.db is not None:
            return db_client.db[self.collection_name]
        return None

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        coll = self._get_mongo_coll()
        records_to_insert = []

        for cid, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            rec = {
                "id": cid,
                "embedding": emb,
                "document": doc,
                "metadata": meta
            }
            records_to_insert.append(rec)
            # Update memory fallback
            self._memory_records = [r for r in self._memory_records if r["id"] != cid]
            self._memory_records.append(rec)

        if coll is not None:
            try:
                for r in records_to_insert:
                    coll.update_one({"id": r["id"]}, {"$set": r}, upsert=True)
                self.logger.info(f"Persisted {len(records_to_insert)} vector records into MongoDB '{self.collection_name}'.")
            except Exception as e:
                self.logger.warning(f"Failed to persist to MongoDB, cached in-memory: {e}")

    def count(self) -> int:
        coll = self._get_mongo_coll()
        if coll is not None:
            try:
                return coll.count_documents({})
            except Exception:
                pass
        return len(self._memory_records)

    def get(self, ids: Optional[List[str]] = None, include: Optional[List[str]] = None) -> Dict[str, Any]:
        coll = self._get_mongo_coll()
        records = []

        if coll is not None:
            try:
                query = {"id": {"$in": ids}} if ids else {}
                cursor = coll.find(query, {"_id": 0})
                records = list(cursor)
            except Exception:
                records = []

        if not records:
            records = [r for r in self._memory_records if (ids is None or r["id"] in ids)]

        return {
            "ids": [r["id"] for r in records],
            "embeddings": [r.get("embedding", []) for r in records],
            "documents": [r.get("document", "") for r in records],
            "metadatas": [r.get("metadata", {}) for r in records],
        }

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        include: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        coll = self._get_mongo_coll()
        all_records = []

        if coll is not None:
            try:
                cursor = coll.find({}, {"_id": 0})
                all_records = list(cursor)
            except Exception:
                all_records = []

        if not all_records:
            all_records = self._memory_records

        all_doc_results = []
        all_meta_results = []
        all_dist_results = []
        all_id_results = []

        for q_emb in query_embeddings:
            scored = []
            for r in all_records:
                if where:
                    match = True
                    for k, v in where.items():
                        if r.get("metadata", {}).get(k) != v:
                            match = False
                            break
                    if not match:
                        continue
                dist = cosine_distance(q_emb, r.get("embedding", []))
                scored.append((dist, r))

            scored.sort(key=lambda x: x[0])
            top_k = scored[:n_results]

            all_dist_results.append([x[0] for x in top_k])
            all_doc_results.append([x[1].get("document", "") for x in top_k])
            all_meta_results.append([x[1].get("metadata", {}) for x in top_k])
            all_id_results.append([x[1].get("id", "") for x in top_k])

        return {
            "ids": all_id_results,
            "documents": all_doc_results,
            "metadatas": all_meta_results,
            "distances": all_dist_results
        }


class VectorDBClient:
    """
    Unified MongoDB Vector Database Client.
    Provides vector persistence and retrieval exclusively via MongoDB.
    """

    def __init__(self, db_path: Optional[str] = None, collection_name: str = "document_chunks"):
        self.logger = setup_logger()
        self.collection_name = collection_name
        self.db_path = db_path
        self.client = db_client
        self.collection = MongoVectorCollection(collection_name)
        self.logger.info(f"Initialized MongoDB Vector Store collection: '{self.collection_name}'")

    def add_records(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        self.logger.info(f"Adding {len(ids)} records to MongoDB vector collection '{self.collection_name}'...")
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
        return {
            "id": result["ids"][0] if result["ids"] else None,
            "embedding": result["embeddings"][0] if result["embeddings"] else None,
            "document": result["documents"][0] if result["documents"] else None,
            "metadata": result["metadatas"][0] if result["metadatas"] else None,
        }

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        self.logger.info(f"Executing MongoDB vector search for top {top_k} results...")
        query_res = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=metadata_filter
        )

        results = []
        if query_res["ids"] and query_res["ids"][0]:
            for cid, doc, meta, dist in zip(
                query_res["ids"][0],
                query_res["documents"][0],
                query_res["metadatas"][0],
                query_res["distances"][0]
            ):
                results.append({
                    "id": cid,
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                    "similarity": round(1.0 - dist, 4)
                })

        return results

    def get_collection_count(self) -> int:
        return self.collection.count()
