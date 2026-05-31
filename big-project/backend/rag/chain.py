"""
AI创作工坊 - RAG Chain

Complete RAG pipeline that chains together:
1. Document loading and chunking
2. Embedding and storage
3. Query processing and retrieval
4. Reranking
5. Answer generation with citations

This is the main entry point for RAG operations.
"""

import json
import time
import uuid
from typing import Any, Optional

from observability.logger import get_logger
from rag.embeddings import EmbeddingModel, get_embedding_model
from rag.vectorstore import VectorStore
from rag.retriever import Retriever, Reranker
from inference.llm_client import LLMClient

logger = get_logger(__name__)


class TextChunker:
    """
    Document chunking strategies for RAG.

    Splits long documents into overlapping chunks for embedding.
    Chunk size and overlap affect retrieval quality:
    - Too small: loses context
    - Too large: dilutes relevance
    - Good defaults: 500-1000 tokens, 50-100 token overlap
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> list[dict]:
        """
        Split text into overlapping chunks.

        Strategy: Recursive character splitting
        1. Try to split by paragraphs (\n\n)
        2. If chunk is still too large, split by sentences
        3. If still too large, split by words
        """
        if not text.strip():
            return []

        chunks = []
        # First, split by paragraphs
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size, finalize current chunk
            if current_chunk and len(current_chunk) + len(para) > self.chunk_size:
                chunks.append(self._make_chunk(current_chunk, metadata, len(chunks)))
                # Keep overlap from end of previous chunk
                overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap else ""
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk = (current_chunk + "\n\n" + para).strip()

            # If a single paragraph is too large, split by sentences
            while len(current_chunk) > self.chunk_size * 1.5:
                split_point = self._find_split_point(current_chunk)
                chunks.append(self._make_chunk(current_chunk[:split_point], metadata, len(chunks)))
                current_chunk = current_chunk[split_point - self.chunk_overlap:]

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(self._make_chunk(current_chunk, metadata, len(chunks)))

        return chunks

    def _find_split_point(self, text: str) -> int:
        """Find the best split point within the chunk size limit."""
        # Try sentence boundary
        for sep in [". ", "! ", "? ", "\n"]:
            idx = text.rfind(sep, 0, self.chunk_size)
            if idx > self.chunk_size * 0.5:
                return idx + len(sep)
        # Fallback: word boundary
        idx = text.rfind(" ", 0, self.chunk_size)
        if idx > 0:
            return idx + 1
        return self.chunk_size

    def _make_chunk(self, text: str, metadata: Optional[dict], index: int) -> dict:
        """Create a chunk with metadata."""
        chunk_id = str(uuid.uuid4())[:8]
        chunk_metadata = {
            "chunk_id": chunk_id,
            "chunk_index": index,
            "char_count": len(text),
        }
        if metadata:
            chunk_metadata.update(metadata)

        return {
            "id": chunk_id,
            "content": text.strip(),
            "metadata": chunk_metadata,
        }

    def chunk_document(self, document: dict) -> list[dict]:
        """
        Chunk a structured document.

        Args:
            document: {"content": str, "source": str, "title": str, ...}
        """
        content = document.get("content", "")
        metadata = {
            "source": document.get("source", "unknown"),
            "title": document.get("title", ""),
        }
        return self.chunk_text(content, metadata)


class RAGChain:
    """
    Complete RAG (Retrieval-Augmented Generation) chain.

    Pipeline:
    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Query   │───→│ Retrieve │───→│ Rerank   │───→│ Generate │
    │ Process  │    │ (Hybrid) │    │ (Cross-  │    │ (LLM +   │
    │          │    │          │    │  Encoder)│    │  Context) │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘

    Usage:
        chain = RAGChain(llm_client, vector_store, embedding_model)
        answer = await chain.query("What is RAG?")
    """

    def __init__(
        self,
        llm_client: LLMClient,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        reranker: Optional[Reranker] = None,
        chunker: Optional[TextChunker] = None,
    ):
        self.llm = llm_client
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.retriever = Retriever(vector_store, embedding_model)
        self.reranker = reranker or Reranker()
        self.chunker = chunker or TextChunker()

    async def ingest(
        self,
        documents: list[dict],
        collection_name: Optional[str] = None,
    ) -> dict:
        """
        Ingest documents into the RAG pipeline.

        Steps:
        1. Chunk documents into smaller pieces
        2. Generate embeddings for each chunk
        3. Store in vector database
        4. Index for keyword search

        Args:
            documents: List of {"content": str, "source": str, ...}
            collection_name: Target collection

        Returns:
            Ingestion statistics
        """
        start = time.perf_counter()
        total_chunks = 0

        for doc in documents:
            # Chunk
            chunks = self.chunker.chunk_document(doc)
            if not chunks:
                continue

            # Embed
            texts = [c["content"] for c in chunks]
            embeddings = await self.embedding_model.embed_batch(texts)

            # Store in vector DB
            ids = [c["id"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            await self.vector_store.add_documents(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
                collection_name=collection_name,
            )

            # Index for keyword search
            for chunk in chunks:
                self.retriever.index_document(
                    chunk["id"], chunk["content"], chunk["metadata"]
                )

            total_chunks += len(chunks)

        duration = time.perf_counter() - start
        logger.info(f"Ingested {len(documents)} documents → {total_chunks} chunks in {duration:.2f}s")

        return {
            "documents_processed": len(documents),
            "chunks_created": total_chunks,
            "duration_seconds": round(duration, 2),
        }

    async def query(
        self,
        question: str,
        top_k: int = 5,
        collection_name: Optional[str] = None,
        use_reranker: bool = True,
        include_sources: bool = True,
    ) -> dict:
        """
        Execute a RAG query: retrieve → rerank → generate.

        Args:
            question: User's question
            top_k: Number of documents to retrieve
            collection_name: Override collection
            use_reranker: Whether to rerank results
            include_sources: Include source documents in response

        Returns:
            Answer with citations and metadata
        """
        start = time.perf_counter()

        # Step 1: Retrieve
        retrieved = await self.retriever.retrieve(
            query=question, top_k=top_k * 2, collection_name=collection_name
        )

        # Step 2: Rerank
        if use_reranker and retrieved:
            reranked = await self.reranker.rerank(question, retrieved, top_k=top_k)
        else:
            reranked = retrieved[:top_k]

        # Step 3: Generate answer
        context = self._build_context(reranked)
        answer = await self._generate_answer(question, context)

        duration = time.perf_counter() - start

        result = {
            "answer": answer,
            "question": question,
            "documents_used": len(reranked),
            "duration_seconds": round(duration, 2),
        }

        if include_sources:
            result["sources"] = [
                {
                    "content": doc.get("content", "")[:300],
                    "metadata": doc.get("metadata", {}),
                    "score": doc.get("rrf_score", doc.get("rerank_score", 0)),
                }
                for doc in reranked
            ]

        return result

    def _build_context(self, documents: list[dict]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", "unknown")
            context_parts.append(f"[Source {i}] ({source})\n{content}")
        return "\n\n---\n\n".join(context_parts)

    async def _generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using the LLM with retrieved context."""
        prompt = f"""Answer the following question using ONLY the provided context. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Instructions:
- Be accurate and specific
- Cite sources using [Source N] notation
- If information conflicts between sources, note the discrepancy
- If you cannot answer from the context, say "I don't have enough information to answer this question."

Answer:"""

        response = await self.llm.generate(
            prompt=prompt,
            system="You are a helpful research assistant. Answer questions accurately using the provided context. Always cite your sources.",
            temperature=0.2,
            max_tokens=1500,
        )

        return response.content
