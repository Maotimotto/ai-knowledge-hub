# RAG Q&A Bot (RAG知识问答)

A document Q&A bot demonstrating the **Retrieval-Augmented Generation (RAG)** pipeline — the most widely-used pattern in production AI applications.

## What It Does

Upload documents (PDF, Markdown, TXT), ask questions in natural language, and get answers with cited sources. Uses hybrid search combining keyword (BM25) and semantic (dense embedding) retrieval for best results.

## Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Document     │    │   Chunker    │    │  Embedder    │
│  Loader       │───▶│  (500 chars) │───▶│ (MiniLM)     │
│  PDF/MD/TXT   │    │  + overlap   │    │              │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                        ┌──────▼───────┐
                                        │  ChromaDB    │
                                        │  Vector Store│
                                        └──────┬───────┘
                                               │
┌──────────────┐    ┌──────────────┐    ┌──────▼───────┐
│  FastAPI      │◀──│  LLM Answer  │◀──│  Hybrid      │
│  /ask         │    │  Generator   │    │  Retriever   │
│  Endpoint     │    │  (OpenAI)    │    │  BM25+Dense  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Setup

```bash
cd rag-qa-bot
pip install -r requirements.txt
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY (optional - works without it)
```

## Run

```bash
python main.py
# API available at http://localhost:8001
```

## Demo Scenarios

### 1. Ingest a document
```bash
curl -X POST http://localhost:8001/ingest \
  -F "file=@your_document.pdf"
```

### 2. Ask a question
```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?", "top_k": 3}'
```

### 3. Try hybrid search tuning
```bash
# Pure keyword search
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "neural networks", "alpha": 0.0}'

# Pure semantic search
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "how do brain-inspired systems work", "alpha": 1.0}'
```

## What You Learn

- **RAG Pipeline**: Load → Chunk → Embed → Store → Retrieve → Generate
- **Hybrid Search**: Combining BM25 (keyword) with dense embeddings
- **Vector Databases**: ChromaDB for similarity search
- **Chunking Strategy**: Overlapping chunks preserve context
- **Source Attribution**: Always cite where answers come from

## Commercial Applications

| Use Case | Description | Market |
|----------|-------------|--------|
| Customer Support | Auto-answer from product docs | $15B+ market |
| Internal Knowledge Base | Search company wikis/policies | Every enterprise |
| Legal Research | Query case law and contracts | $1B+ market |
| Medical QA | Clinical guidelines lookup | Healthcare IT |
| Technical Docs | Developer documentation search | DevTools |

## Key Design Decisions

1. **Hybrid search** over pure vector — BM25 catches exact terms, embeddings catch semantics
2. **Overlapping chunks** — prevents losing context at boundaries
3. **Local fallback** — works without OpenAI API key (extractive mode)
4. **Cosine similarity** — best for normalized embeddings
