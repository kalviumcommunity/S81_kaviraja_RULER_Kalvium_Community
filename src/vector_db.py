import os
import json
import logging
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional

def setup_logger():
    logger = logging.getLogger("VectorDB")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

class VectorDBClient:
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "document_chunks"):
        self.logger = setup_logger()
        self.db_path = db_path
        self.collection_name = collection_name
        
        self.logger.info(f"Initializing ChromaDB at path: {self.db_path}")
        self.client = chromadb.PersistentClient(path=self.db_path, settings=Settings(anonymized_telemetry=False))
        
        self.logger.info(f"Creating/getting collection: {self.collection_name}")
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )
        
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
