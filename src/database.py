"""
MongoDB Database Client and Schema Definitions for RULER Regulatory AI Platform.

Provides collections, schemas, and persistence for:
1. `users`: User profiles, credentials, department, and activity timestamps.
2. `queries`: Conversational queries, grounded answers, confidence, latency, tokens, and sources.
3. `feedback`: User satisfaction ratings, compliance officer assessment notes, and category tags.
4. `documents`: Ingested regulatory policies, categories, file metadata, and vectorization status.
5. `chunks`: Partitioned document chunks, token spans, section headers, and character offsets.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None

logger = logging.getLogger("RulerDB")


# -------------------------------------------------------------
# 1. SCHEMA DEFINITIONS / DATA MODELS
# -------------------------------------------------------------

@dataclass
class UserRecord:
    """Schema for users collection."""
    email: str
    full_name: str
    role: str = "Compliance Officer"  # 'Compliance Officer', 'Risk Specialist', 'Administrator'
    department: str = "Banking Regulatory Compliance"
    password_hash: Optional[str] = None
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QueryRecord:
    """Schema for queries / conversational telemetry collection."""
    question: str
    answer: str
    status: str = "success"  # 'success', 'refusal', 'fallback', 'error'
    confidence: str = "high"
    is_grounded: bool = True
    user_email: Optional[str] = None
    session_id: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_generated: int = 0
    latency_ms: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackRecord:
    """Schema for user feedback and officer notes collection."""
    question: str
    answer: str
    rating: str  # 'helpful', 'needs_revision', 'flagged'
    rating_score: int = 1  # 1 for positive, -1 for negative
    thoughts: Optional[str] = ""
    category: str = "General Compliance"
    notes: Optional[str] = ""
    user_email: Optional[str] = None
    query_id: Optional[str] = None
    tokens_generated: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentRecord:
    """Schema for ingested documents collection."""
    doc_id: str
    filename: str
    category: str = "Institutional Regulation"
    file_type: str = ".txt"
    file_size_bytes: int = 0
    character_count: int = 0
    token_count: int = 0
    chunk_count: int = 0
    uploaded_by: str = "Administrator"
    status: str = "indexed"  # 'indexed', 'processing', 'failed'
    source_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChunkRecord:
    """Schema for document chunks collection."""
    chunk_id: str
    doc_id: str
    filename: str
    text: str
    section: Optional[str] = "General"
    page_number: int = 1
    chunk_index: int = 1
    total_chunks: int = 1
    token_count: int = 0
    start_char: int = 0
    end_char: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# -------------------------------------------------------------
# 2. MONGODB CLIENT MANAGER
# -------------------------------------------------------------

class MongoDBClient:
    """
    Production-grade MongoDB Client with automatic fallback and in-memory cache.
    Connects to local MongoDB, MongoDB Atlas, or Docker instances.
    """

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        db_name: Optional[str] = None,
        timeout_ms: int = 2500
    ):
        self.mongo_uri = (
            mongo_uri
            or os.getenv("MONGO_URI")
            or os.getenv("MONGODB_URI")
            or "mongodb://localhost:27017"
        )
        self.db_name = db_name or os.getenv("MONGO_DB_NAME") or "ruler_rag_db"
        self.timeout_ms = timeout_ms
        self.client: Optional[MongoClient] = None
        self.db = None
        self.is_connected = False

        # In-memory fallback buffers if MongoDB is not running locally
        self._memory_queries: List[Dict[str, Any]] = []
        self._memory_feedback: List[Dict[str, Any]] = []
        self._memory_docs: List[Dict[str, Any]] = []
        self._memory_users: Dict[str, Dict[str, Any]] = {}

        self.connect()

    def connect(self) -> bool:
        """Attempts connection to MongoDB instance with timeout."""
        if not PYMONGO_AVAILABLE:
            logger.warning("PyMongo is not installed. Running in memory fallback mode.")
            self.is_connected = False
            return False

        try:
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=self.timeout_ms,
                connectTimeoutMS=self.timeout_ms,
            )
            # Verify connectivity via ping
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.is_connected = True
            self._ensure_indexes()
            logger.info(f"Connected to MongoDB database '{self.db_name}' at {self.mongo_uri}")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            logger.warning(f"MongoDB connection to {self.mongo_uri} unreached ({e}). Using in-memory fallback store.")
            self.is_connected = False
            self.client = None
            self.db = None
            return False

    def _ensure_indexes(self):
        """Creates indexes on key collections."""
        if not self.is_connected or self.db is None:
            return
        try:
            # Users
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            # Documents
            self.db.documents.create_index([("doc_id", ASCENDING)], unique=True)
            # Chunks
            self.db.chunks.create_index([("chunk_id", ASCENDING)], unique=True)
            self.db.chunks.create_index([("doc_id", ASCENDING)])
            # Queries & Feedback
            self.db.queries.create_index([("created_at", DESCENDING)])
            self.db.feedback.create_index([("created_at", DESCENDING)])
        except Exception as e:
            logger.warning(f"Failed to initialize MongoDB indexes: {e}")

    # ---------------------------------------------------------
    # QUERIES COLLECTION
    # ---------------------------------------------------------
    def save_query(self, query_data: Union[QueryRecord, Dict[str, Any]]) -> Dict[str, Any]:
        """Saves a conversational RAG query record."""
        doc = query_data.to_dict() if isinstance(query_data, QueryRecord) else dict(query_data)
        if "created_at" not in doc:
            doc["created_at"] = datetime.now(timezone.utc).isoformat()

        if self.is_connected and self.db is not None:
            try:
                res = self.db.queries.insert_one(doc)
                doc["_id"] = str(res.inserted_id)
                return doc
            except Exception as e:
                logger.error(f"Failed to insert query into MongoDB: {e}")

        self._memory_queries.append(doc)
        return doc

    def get_queries(
        self,
        limit: int = 50,
        skip: int = 0,
        user_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves chronological query records, optionally filtered by user_email."""
        query_filter = {}
        if user_email:
            query_filter["user_email"] = user_email.strip().lower()

        if self.is_connected and self.db is not None:
            try:
                cursor = (
                    self.db.queries.find(query_filter, {"_id": 0})
                    .sort("created_at", DESCENDING)
                    .skip(skip)
                    .limit(limit)
                )
                return list(cursor)
            except Exception as e:
                logger.error(f"Failed to fetch queries from MongoDB: {e}")

        # In-memory fallback filtering
        filtered = self._memory_queries
        if user_email:
            target_email = user_email.strip().lower()
            filtered = [
                q for q in self._memory_queries
                if (q.get("user_email") or "").strip().lower() == target_email
            ]

        return list(reversed(filtered))[skip: skip + limit]

    # ---------------------------------------------------------
    # FEEDBACK COLLECTION
    # ---------------------------------------------------------
    def save_feedback(self, feedback_data: Union[FeedbackRecord, Dict[str, Any]]) -> Dict[str, Any]:
        """Saves user feedback / officer review record."""
        doc = feedback_data.to_dict() if isinstance(feedback_data, FeedbackRecord) else dict(feedback_data)
        if "created_at" not in doc:
            doc["created_at"] = datetime.now(timezone.utc).isoformat()

        if self.is_connected and self.db is not None:
            try:
                res = self.db.feedback.insert_one(doc)
                doc["_id"] = str(res.inserted_id)
                return doc
            except Exception as e:
                logger.error(f"Failed to insert feedback into MongoDB: {e}")

        self._memory_feedback.append(doc)
        return doc

    def get_feedbacks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves submitted user feedback records."""
        if self.is_connected and self.db is not None:
            try:
                cursor = self.db.feedback.find({}, {"_id": 0}).sort("created_at", DESCENDING).limit(limit)
                return list(cursor)
            except Exception as e:
                logger.error(f"Failed to fetch feedback from MongoDB: {e}")

        return list(reversed(self._memory_feedback))[:limit]

    # ---------------------------------------------------------
    # DOCUMENTS & CHUNKS COLLECTION
    # ---------------------------------------------------------
    def save_document(
        self,
        doc_data: Union[DocumentRecord, Dict[str, Any]],
        chunks: Optional[List[Union[ChunkRecord, Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """Saves document metadata and associated chunks."""
        doc = doc_data.to_dict() if isinstance(doc_data, DocumentRecord) else dict(doc_data)
        if "created_at" not in doc:
            doc["created_at"] = datetime.now(timezone.utc).isoformat()

        if self.is_connected and self.db is not None:
            try:
                self.db.documents.update_one({"doc_id": doc["doc_id"]}, {"$set": doc}, upsert=True)
                if chunks:
                    chunk_docs = [
                        c.to_dict() if isinstance(c, ChunkRecord) else dict(c) for c in chunks
                    ]
                    for cd in chunk_docs:
                        self.db.chunks.update_one({"chunk_id": cd["chunk_id"]}, {"$set": cd}, upsert=True)
                return doc
            except Exception as e:
                logger.error(f"Failed to save document to MongoDB: {e}")

        # In-memory buffer
        existing = next((d for d in self._memory_docs if d.get("doc_id") == doc["doc_id"]), None)
        if existing:
            existing.update(doc)
        else:
            self._memory_docs.append(doc)
        return doc

    def get_documents(self) -> List[Dict[str, Any]]:
        """Retrieves list of all registered documents."""
        if self.is_connected and self.db is not None:
            try:
                cursor = self.db.documents.find({}, {"_id": 0}).sort("created_at", DESCENDING)
                return list(cursor)
            except Exception as e:
                logger.error(f"Failed to fetch documents from MongoDB: {e}")

        return self._memory_docs

    # ---------------------------------------------------------
    # USERS COLLECTION
    # ---------------------------------------------------------
    def save_user(self, user_data: Union[UserRecord, Dict[str, Any]]) -> Dict[str, Any]:
        """Registers or updates user profile."""
        doc = user_data.to_dict() if isinstance(user_data, UserRecord) else dict(user_data)
        email = doc.get("email", "").lower().strip()
        doc["email"] = email

        if self.is_connected and self.db is not None:
            try:
                self.db.users.update_one({"email": email}, {"$set": doc}, upsert=True)
                return doc
            except Exception as e:
                logger.error(f"Failed to save user to MongoDB: {e}")

        self._memory_users[email] = doc
        return doc

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Finds user by email address."""
        email_clean = (email or "").lower().strip()
        if self.is_connected and self.db is not None:
            try:
                return self.db.users.find_one({"email": email_clean}, {"_id": 0})
            except Exception as e:
                logger.error(f"Failed to find user in MongoDB: {e}")

        return self._memory_users.get(email_clean)

    # ---------------------------------------------------------
    # HEALTH & STATS
    # ---------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """Returns database connectivity and collection statistics."""
        stats = {
            "is_connected": self.is_connected,
            "database_type": "MongoDB",
            "database_name": self.db_name,
            "mongo_uri_configured": bool(self.mongo_uri),
            "driver_installed": PYMONGO_AVAILABLE,
        }

        if self.is_connected and self.db is not None:
            try:
                stats["collections"] = {
                    "users_count": self.db.users.count_documents({}),
                    "queries_count": self.db.queries.count_documents({}),
                    "feedback_count": self.db.feedback.count_documents({}),
                    "documents_count": self.db.documents.count_documents({}),
                    "chunks_count": self.db.chunks.count_documents({}),
                }
            except Exception:
                stats["collections"] = {}
        else:
            stats["collections"] = {
                "users_count": len(self._memory_users),
                "queries_count": len(self._memory_queries),
                "feedback_count": len(self._memory_feedback),
                "documents_count": len(self._memory_docs),
                "chunks_count": 0,
                "mode": "in_memory_fallback"
            }

        return stats


# Global Singleton Client Instance
db_client = MongoDBClient()


# -------------------------------------------------------------
# 3. MODULE-LEVEL CONVENIENCE HELPERS
# -------------------------------------------------------------
def get_db_status() -> Dict[str, Any]:
    """Returns database connectivity and collection statistics."""
    return db_client.get_status()


def insert_query_log(
    question: str,
    answer: str,
    sources: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    status: str = "success",
    confidence: str = "high",
    user_email: Optional[str] = None,
    session_id: Optional[str] = None,
    tokens_generated: int = 0,
    latency_ms: float = 0.0,
) -> str:
    """Inserts a query log record into MongoDB and returns the created record or query ID."""
    rec = QueryRecord(
        question=question,
        answer=answer,
        status=status,
        confidence=confidence,
        user_email=user_email,
        session_id=session_id,
        sources=sources or [],
        metadata=metadata or {},
        tokens_generated=tokens_generated,
        latency_ms=latency_ms,
    )
    saved = db_client.save_query(rec)
    return saved.get("_id", saved.get("created_at", "query_logged"))


def list_recent_queries(
    limit: int = 50,
    skip: int = 0,
    user_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lists recent queries stored in MongoDB, optionally filtered by user_email."""
    return db_client.get_queries(limit=limit, skip=skip, user_email=user_email)


def insert_feedback(
    query_id_or_question: str,
    rating_score: int,
    thoughts: str = "",
    answer: str = "",
    category: str = "General Compliance",
    notes: str = "",
    user_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Inserts a feedback record into MongoDB."""
    rating_label = "helpful" if rating_score > 0 else "needs_revision"
    rec = FeedbackRecord(
        question=query_id_or_question,
        answer=answer,
        rating=rating_label,
        rating_score=rating_score,
        thoughts=thoughts,
        category=category,
        notes=notes,
        user_email=user_email,
        query_id=query_id_or_question,
    )
    return db_client.save_feedback(rec)


def list_recent_feedback(limit: int = 100) -> List[Dict[str, Any]]:
    """Lists recent feedback records stored in MongoDB."""
    return db_client.get_feedbacks(limit=limit)


def save_document_record(
    doc_id: str,
    filename: str,
    category: str = "Institutional Regulation",
    file_type: str = ".txt",
    file_size_bytes: int = 0,
    chunk_count: int = 0,
    chunks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Saves document and chunk metadata in MongoDB."""
    doc = DocumentRecord(
        doc_id=doc_id,
        filename=filename,
        category=category,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        chunk_count=chunk_count,
    )
    return db_client.save_document(doc, chunks=chunks)


def list_documents() -> List[Dict[str, Any]]:
    """Lists documents stored in MongoDB."""
    return db_client.get_documents()
