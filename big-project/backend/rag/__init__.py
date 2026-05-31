"""
AI创作工坊 - RAG (Retrieval-Augmented Generation) System

This package implements a complete RAG pipeline:
- embeddings.py: Text embedding models
- vectorstore.py: Vector database integration (ChromaDB)
- retriever.py: Hybrid retrieval (dense + sparse)
- chain.py: Full RAG chain with reranking

The RAG pipeline: Document → Chunk → Embed → Store → Retrieve → Rerank → Generate
"""
