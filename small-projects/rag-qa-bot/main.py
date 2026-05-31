"""RAG Q&A Bot - FastAPI application with document Q&A endpoint."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

load_dotenv()

# Global store instances
_store = None
_retriever = None


def get_store():
    global _store
    if _store is None:
        from ingest import DocumentStore
        _store = DocumentStore()
    return _store


def get_retriever():
    global _retriever
    if _retriever is None:
        from retriever import HybridRetriever
        _retriever = HybridRetriever()
    return _retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize models on startup."""
    print("🚀 Initializing RAG Q&A Bot...")
    get_store()
    print("✅ Ready!")
    yield


app = FastAPI(title="RAG Q&A Bot", version="1.0.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    alpha: float = 0.5  # 0=pure BM25, 1=pure dense


class Source(BaseModel):
    text: str
    source: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    model: str


@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """Upload and ingest a document (PDF, MD, TXT)."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".md", ".txt"):
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    # Save uploaded file
    upload_dir = Path("./uploads")
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    try:
        store = get_store()
        result = store.ingest_file(str(file_path))
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")


@app.post("/ask", response_model=AskResponse)
async def ask_question(req: AskRequest):
    """Ask a question and get an answer with sources."""
    retriever = get_retriever()
    results = retriever.search(req.question, top_k=req.top_k, alpha=req.alpha)

    if not results:
        return AskResponse(
            answer="No documents found. Please ingest some documents first.",
            sources=[],
            model="none"
        )

    # Build context from retrieved chunks
    context = "\n\n---\n\n".join(r["text"] for r in results[:3])

    # Generate answer
    answer = _generate_answer(req.question, context)
    model = os.getenv("LLM_MODEL", "local-extractive")

    sources = [Source(text=r["text"][:300], source=r["source"], score=r["score"]) for r in results]
    return AskResponse(answer=answer, sources=sources, model=model)


def _generate_answer(question: str, context: str) -> str:
    """Generate answer using OpenAI or fallback to extractive mode."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "sk-your-key-here":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Answer based on the provided context. If the context doesn't contain the answer, say so."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ],
                max_tokens=500,
                temperature=0.1,
            )
            return response.choices[0].message.content or "No response generated."
        except Exception as e:
            return f"[OpenAI error: {e}] Fallback: Based on the retrieved context, here are relevant excerpts:\n\n{context[:500]}"

    # Fallback: extractive answer (no LLM needed)
    return f"[Local mode - no OPENAI_API_KEY set] Based on retrieved documents:\n\n{context[:500]}"


@app.get("/stats")
async def stats():
    """Get collection statistics."""
    store = get_store()
    return {"document_count": store.doc_count}


@app.get("/")
async def root():
    return {
        "name": "RAG Q&A Bot",
        "endpoints": {
            "POST /ingest": "Upload a document (PDF/MD/TXT)",
            "POST /ask": "Ask a question",
            "GET /stats": "Collection statistics",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
