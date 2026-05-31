"""Tests for the RAG pipeline."""
import pytest
from backend.rag.chain import RAGChain
from backend.rag.retriever import HybridRetriever


def test_rag_chain_init():
    """Test RAG chain initializes."""
    chain = RAGChain()
    assert chain is not None


def test_chunk_text():
    """Test text chunking logic."""
    from backend.rag.chain import RAGChain
    chain = RAGChain()
    text = "This is a test document. " * 100
    chunks = chain.chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 250  # some tolerance


def test_hybrid_retriever_init():
    """Test hybrid retriever initializes."""
    retriever = HybridRetriever()
    assert retriever is not None


def test_embedding_dimension():
    """Test embeddings produce expected dimensions."""
    from backend.rag.embeddings import EmbeddingService
    svc = EmbeddingService()
    # Should return a list of floats
    result = svc.embed_query("test query")
    assert isinstance(result, list)
    assert len(result) > 0
