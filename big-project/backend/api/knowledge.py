"""
AI创作工坊 - Knowledge / RAG API Router

Endpoints for RAG Q&A, document ingestion, and collection management.
"""

import json
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from inference.llm_client import LLMClient
from rag.chain import RAGChain, TextChunker
from rag.embeddings import get_embedding_model
from rag.vectorstore import VectorStore
from models.schemas import (
    KnowledgeQuery, KnowledgeAnswer, IngestRequest, IngestResponse,
    CollectionInfo,
)
from security.auth import UserContext, get_current_user
from security.guardrails import guardrails
from observability.logger import get_logger

logger = get_logger(__name__)
router = APIManager = None

_rag_chain: RAGChain | None = None


def _get_rag_chain() -> RAGChain:
    """Lazy-initialize the RAG chain."""
    global _rag_chain
    if _rag_chain is None:
        llm = LLMClient()
        embedding_model = get_embedding_model()
        vector_store = VectorStore()
        _rag_chain = RAGChain(llm_client=llm, vector_store=vector_store, embedding_model=embedding_model)
    return _rag_chain


@router.post(
    "/ask",
    response_model=KnowledgeAnswer,
    summary="Ask a question using RAG",
)
async def ask_question(
    query: KnowledgeQuery,
    user: UserContext = Depends(get_current_user),
) -> KnowledgeAnswer:
    """
    Ask a question and get an answer with source citations.
    Uses RAG pipeline: retrieve → rerank → generate.
    """
    is_safe, safe_question = guardrails.safe_process(query.question)
    if not is_safe:
        raise HTTPException(status_code=400, detail="Question failed safety checks")

    chain = _get_rag_chain()

    try:
        result = await chain.query(
            question=safe_question,
            top_k=query.top_k,
            collection_name=query.collection,
            use_reranker=query.use_reranker,
        )
    except Exception as e:
        logger.error(f"RAG query failed: {e}", extra={"user_id": user.user_id}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    return KnowledgeAnswer(
        answer=result["answer"],
        sources=result.get("sources", []),
        question=query.question,
        documents_used=result["documents_used"],
        duration_seconds=result["duration_seconds"],
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest a document",
)
async def ingest_document(
    request: IngestRequest,
    user: UserContext = Depends(get_current_user),
) -> IngestResponse:
    """
    Ingest a document into the knowledge base.
    Chunks the text, generates embeddings, and stores in vector DB.
    """
    chain = _get_rag_chain()

    document = {
        "content": request.content,
        "source": request.source,
        "title": request.title or "Untitled",
    }

    try:
        result = await chain.ingest(
            documents=[document],
            collection_name=request.collection,
        )
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}", extra={"user_id": user.user_id}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return IngestResponse(
        documents_processed=result["documents_processed"],
        chunks_created=result["chunks_created"],
        duration_seconds=result["duration_seconds"],
    )


@router.get(
    "/collections",
    response_model=list[CollectionInfo],
    summary="List knowledge collections",
)
async def list_collections(
    user: UserContext = Depends(get_current_user),
) -> list[CollectionInfo]:
    """List all available knowledge base collections."""
    chain = _get_rag_chain()

    try:
        collections = await chain.vector_store.list_collections()
        return [
            CollectionInfo(name=c["name"], document_count=c.get("count", 0))
            for c in collections
        ]
    except Exception as e:
        logger.warning(f"Failed to list collections: {e}")
        return []
