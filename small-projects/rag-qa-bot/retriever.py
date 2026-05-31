"""Hybrid retriever combining BM25 (sparse) and dense vector search."""

from typing import Optional

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import chromadb


class HybridRetriever:
    """Combines BM25 keyword search with dense embedding search."""

    def __init__(self, db_path: str = "./chroma_db", model_name: Optional[str] = None):
        import os
        model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedder = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="documents")
        self._bm25: Optional[BM25Okapi] = None
        self._corpus: list[str] = []
        self._metadatas: list[dict] = []
        self._build_bm25_index()

    def _build_bm25_index(self) -> None:
        """Build BM25 index from all stored documents."""
        if self.collection.count() == 0:
            return
        all_docs = self.collection.get(include=["documents", "metadatas"])
        self._corpus = all_docs["documents"]
        self._metadatas = all_docs["metadatas"]
        tokenized = [doc.lower().split() for doc in self._corpus]
        self._bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 5, alpha: float = 0.5) -> list[dict]:
        """
        Hybrid search combining BM25 and dense retrieval.
        alpha: weight for dense search (1-alpha for BM25).
        """
        if not self._corpus:
            return []

        # BM25 search
        bm25_scores = [0.0] * len(self._corpus)
        if self._bm25 is not None:
            scores = self._bm25.get_scores(query.lower().split())
            bm25_scores = scores.tolist()

        # Normalize BM25 scores
        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        if max_bm25 > 0:
            bm25_scores = [s / max_bm25 for s in bm25_scores]

        # Dense search
        embedding = self.embedder.encode([query]).tolist()
        dense_results = self.collection.query(
            query_embeddings=embedding,
            n_results=min(top_k * 2, len(self._corpus)),
            include=["documents", "metadatas", "distances"]
        )

        # Build dense score map
        dense_scores: dict[str, float] = {}
        for doc, dist in zip(dense_results["documents"][0], dense_results["distances"][0]):
            dense_scores[doc] = max(0, 1 - dist)

        # Combine scores
        combined: list[dict] = []
        for i, (doc, meta) in enumerate(zip(self._corpus, self._metadatas)):
            ds = dense_scores.get(doc, 0.0)
            bs = bm25_scores[i] if i < len(bm25_scores) else 0.0
            combined_score = alpha * ds + (1 - alpha) * bs
            combined.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "score": round(combined_score, 4),
                "dense_score": round(ds, 4),
                "bm25_score": round(bs, 4),
            })

        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]


if __name__ == "__main__":
    retriever = HybridRetriever()
    query = "What is retrieval augmented generation?"
    results = retriever.search(query, top_k=3)
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] Score: {r['score']} (dense={r['dense_score']}, bm25={r['bm25_score']})")
        print(f"    Source: {r['source']}")
        print(f"    Text: {r['text'][:200]}...")
