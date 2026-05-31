"""
AI创作工坊 - Vector Store Integration

Provides vector database integration for the RAG pipeline.
Supports ChromaDB (primary) and Qdrant (alternative).

Key concepts:
- Vector stores persist embeddings alongside documents
- Similarity search finds semantically relevant content
- Metadata filtering narrows search scope
- Collections organize documents by topic/tenant
"""

import time
import uuid
from typing import Any, Optional

from observability.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    ChromaDB-backed vector store for RAG.

    Features:
    - Collection-based organization (per-tenant, per-topic)
    - Metadata filtering (by source, date, category)
    - Similarity search with scores
    - Batch operations for efficiency
    """

    def __init__(self, host: str = "localhost", port: int = 8100, collection_name: str = "default"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy-initialize ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                self._client = chromadb.HttpClient(host=self.host, port=self.port)
                logger.info(f"Connected to ChromaDB at {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"ChromaDB connection failed: {e}. Using in-memory store.")
                import chromadb
                self._client = chromadb.Client()
        return self._client

    def _get_collection(self, name: Optional[str] = None):
        """Get or create a collection."""
        client = self._get_client()
        collection_name = name or self.collection_name
        if self._collection is None or collection_name != self.collection_name:
            self._collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )
            self.collection_name = collection_name
        return self._collection

    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
        collection_name: Optional[str] = None,
    ) -> list[str]:
        """
        Add documents with embeddings to the vector store.

        Args:
            documents: List of text documents
            embeddings: List of embedding vectors
            metadatas: Optional metadata for each document
            ids: Optional document IDs (auto-generated if not provided)
            collection_name: Override collection name

        Returns:
            List of document IDs
        """
        collection = self._get_collection(collection_name)

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        if metadatas is None:
            metadatas = [{"added_at": time.time()} for _ in documents]

        # Ensure metadata values are ChromaDB-compatible types
        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            clean_metadatas.append(clean_meta)

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=clean_metadatas,
            ids=ids,
        )

        logger.info(f"Added {len(documents)} documents to collection '{self.collection_name}'")
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: Optional[dict] = None,
        collection_name: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            where: Metadata filter (e.g., {"source": "wiki"})
            collection_name: Override collection name

        Returns:
            List of results with content, score, and metadata
        """
        collection = self._get_collection(collection_name)

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        # Format results
        formatted = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "score": 1 - results["distances"][0][i] if results.get("distances") else 0.0,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "id": results["ids"][0][i] if results.get("ids") else None,
                })

        return formatted

    async def delete(
        self,
        ids: Optional[list[str]] = None,
        where: Optional[dict] = None,
        collection_name: Optional[str] = None,
    ) -> int:
        """Delete documents by ID or filter."""
        collection = self._get_collection(collection_name)
        kwargs = {}
        if ids:
            kwargs["ids"] = ids
        if where:
            kwargs["where"] = where
        if kwargs:
            collection.delete(**kwargs)
            return len(ids) if ids else 0
        return 0

    async def count(self, collection_name: Optional[str] = None) -> int:
        """Count documents in a collection."""
        collection = self._get_collection(collection_name)
        return collection.count()

    async def list_collections(self) -> list[str]:
        """List all collections."""
        client = self._get_client()
        collections = client.list_collections()
        return [c.name for c in collections]
