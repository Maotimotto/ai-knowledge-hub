"""Document ingestion pipeline: load → chunk → embed → store in ChromaDB."""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer


def load_document(file_path: str) -> str:
    """Load text from PDF, Markdown, or TXT files."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise RuntimeError("PyPDF2 required for PDF: pip install PyPDF2")
    elif suffix in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        if current_len + len(sent) > chunk_size and current:
            chunks.append(" ".join(current))
            # Keep overlap
            while current_len > overlap and current:
                removed = current.pop(0)
                current_len -= len(removed)
        current.append(sent)
        current_len += len(sent)

    if current:
        chunks.append(" ".join(current))
    return [c.strip() for c in chunks if c.strip()]


def compute_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


class DocumentStore:
    """Manages document ingestion and storage in ChromaDB."""

    def __init__(self, db_path: str = "./chroma_db", model_name: Optional[str] = None):
        model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedder = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )

    def ingest_file(self, file_path: str) -> dict:
        """Ingest a single file: load, chunk, embed, store."""
        text = load_document(file_path)
        chunks = chunk_text(text)
        if not chunks:
            return {"file": file_path, "chunks": 0, "error": "No text extracted"}

        embeddings = self.embedder.encode(chunks).tolist()
        source = Path(file_path).name
        ids = [f"{compute_hash(c)[:12]}_{i}" for i, c in enumerate(chunks)]
        metadatas = [{"source": source, "chunk_idx": i} for i in range(len(chunks))]

        self.collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return {"file": file_path, "chunks": len(chunks), "source": source}

    def ingest_directory(self, dir_path: str) -> list[dict]:
        """Ingest all supported files from a directory."""
        results = []
        for ext in ("*.pdf", "*.md", "*.txt"):
            for fpath in Path(dir_path).glob(ext):
                results.append(self.ingest_file(str(fpath)))
        return results

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Dense vector search."""
        embedding = self.embedder.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append({"text": doc, "source": meta["source"], "score": 1 - dist})
        return hits

    @property
    def doc_count(self) -> int:
        return self.collection.count()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <file_or_directory>")
        sys.exit(1)
    store = DocumentStore()
    target = sys.argv[1]
    if os.path.isdir(target):
        results = store.ingest_directory(target)
    else:
        results = [store.ingest_file(target)]
    for r in results:
        print(f"  ✓ {r.get('file', '?')}: {r.get('chunks', 0)} chunks")
    print(f"Total documents in store: {store.doc_count}")
