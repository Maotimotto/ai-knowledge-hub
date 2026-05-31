"""
AI创作工坊 - Hybrid Retriever

Implements retrieval strategies for the RAG pipeline:
- Dense retrieval: Semantic search via embeddings
- Sparse retrieval: Keyword-based search (BM25-style)
- Hybrid: Combines both with weighted scoring

Key concepts:
- Dense retrieval captures semantic meaning
- Sparse retrieval catches exact keyword matches
- Hybrid combines strengths of both approaches
- Reciprocal Rank Fusion (RRF) merges result lists
"""

from typing import Any, Optional

from observability.logger import get_logger
from rag.embeddings import EmbeddingModel
from rag.vectorstore import VectorStore

logger = get_logger(__name__)


class Retriever:
    """
    Hybrid retriever combining dense and sparse search.

    The retrieval pipeline:
    1. Embed the query (dense) and tokenize (sparse)
    2. Search vector store for semantic matches
    3. Search keyword index for exact matches
    4. Merge results using Reciprocal Rank Fusion
    5. Return top-k combined results
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        # In-memory keyword index (simplified BM25)
        self._keyword_index: dict[str, list[dict]] = {}  # term -> [{doc_id, doc, metadata}]

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
        collection_name: Optional[str] = None,
    ) -> list[dict]:
        """
        Execute hybrid retrieval.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters
            collection_name: Override collection

        Returns:
            List of results sorted by relevance score
        """
        # Dense retrieval
        dense_results = await self._dense_retrieve(query, top_k * 2, filters, collection_name)

        # Sparse retrieval (from keyword index)
        sparse_results = self._sparse_retrieve(query, top_k * 2)

        # Merge with Reciprocal Rank Fusion
        merged = self._reciprocal_rank_fusion(
            dense_results, sparse_results, top_k
        )

        logger.info(
            f"Hybrid retrieval for '{query[:50]}...': "
            f"{len(dense_results)} dense + {len(sparse_results)} sparse → {len(merged)} results"
        )

        return merged

    async def _dense_retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[dict],
        collection_name: Optional[str],
    ) -> list[dict]:
        """Semantic search using embeddings."""
        try:
            query_embedding = await self.embedding_model.embed_text(query)
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                where=filters,
                collection_name=collection_name,
            )
            return results
        except Exception as e:
            logger.error(f"Dense retrieval failed: {e}")
            return []

    def _sparse_retrieve(self, query: str, top_k: int) -> list[dict]:
        """
        Keyword-based retrieval using BM25-like scoring.
        Simple implementation: term frequency scoring.
        """
        query_terms = set(query.lower().split())
        scores: dict[str, float] = {}  # doc_id -> score
        doc_map: dict[str, dict] = {}  # doc_id -> doc info

        for term in query_terms:
            if term in self._keyword_index:
                for entry in self._keyword_index[term]:
                    doc_id = entry["doc_id"]
                    # Term frequency scoring (simplified BM25)
                    scores[doc_id] = scores.get(doc_id, 0) + 1.0
                    doc_map[doc_id] = entry

        # Sort by score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for doc_id, score in sorted_docs:
            entry = doc_map[doc_id]
            results.append({
                "content": entry["content"],
                "score": score / max(len(query_terms), 1),  # Normalize
                "metadata": entry.get("metadata", {}),
                "id": doc_id,
            })

        return results

    def index_document(self, doc_id: str, content: str, metadata: Optional[dict] = None):
        """Add a document to the keyword index."""
        terms = content.lower().split()
        seen_terms = set()
        for term in terms:
            term = term.strip(".,!?;:'\"()[]{}")
            if term and term not in seen_terms:
                seen_terms.add(term)
                if term not in self._keyword_index:
                    self._keyword_index[term] = []
                self._keyword_index[term].append({
                    "doc_id": doc_id,
                    "content": content,
                    "metadata": metadata or {},
                })

    def _reciprocal_rank_fusion(
        self,
        dense_results: list[dict],
        sparse_results: list[dict],
        top_k: int,
        k: int = 60,
    ) -> list[dict]:
        """
        Merge two result lists using Reciprocal Rank Fusion (RRF).

        RRF score = Σ 1 / (k + rank_i) for each ranking list
        where k is a smoothing constant (default 60).

        This balances dense (semantic) and sparse (keyword) retrieval.
        """
        scores: dict[str, float] = {}
        content_map: dict[str, dict] = {}

        # Score dense results
        for rank, result in enumerate(dense_results):
            doc_id = result.get("id", result.get("content", "")[:50])
            scores[doc_id] = scores.get(doc_id, 0) + self.dense_weight / (k + rank + 1)
            content_map[doc_id] = result

        # Score sparse results
        for rank, result in enumerate(sparse_results):
            doc_id = result.get("id", result.get("content", "")[:50])
            scores[doc_id] = scores.get(doc_id, 0) + self.sparse_weight / (k + rank + 1)
            if doc_id not in content_map:
                content_map[doc_id] = result

        # Sort by RRF score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]

        merged = []
        for doc_id in sorted_ids:
            entry = content_map[doc_id].copy()
            entry["rrf_score"] = scores[doc_id]
            merged.append(entry)

        return merged


class Reranker:
    """
    Cross-encoder reranker for improving retrieval quality.

    After initial retrieval, a reranker re-scores results using
    a more expensive but more accurate model.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
                logger.info(f"Loaded reranker: {self.model_name}")
            except ImportError:
                logger.warning("sentence-transformers not available for reranking")
                self._model = "fallback"

    async def rerank(
        self, query: str, documents: list[dict], top_k: int = 5
    ) -> list[dict]:
        """
        Rerank documents by relevance to the query.

        Uses a cross-encoder that jointly encodes (query, document) pairs
        for more accurate relevance scoring than bi-encoders.
        """
        if not documents:
            return []

        self._load_model()

        if self._model == "fallback":
            # No reranking available — return original order
            return documents[:top_k]

        # Score each (query, document) pair
        pairs = [(query, doc.get("content", "")) for doc in documents]
        scores = self._model.predict(pairs)

        # Attach scores and sort
        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)

        reranked = sorted(documents, key=lambda x: x.get("rerank_score", 0), reverse=True)
        return reranked[:top_k]
