# FIAP PDF MCP Server Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a robust and scalable MCP Server that exposes semantic search and navigation tools over a collection of postgraduate PDF documents.

**Architecture:** A local Retrieval-Augmented Generation (RAG) pipeline using a vector database (ChromaDB), exposed as an MCP Server via standard input/output (stdio). It uses `watchdog` for incremental updates and `fastmcp` to expose the tools to LLM clients.

**Tech Stack:** Python, FastMCP, PyMuPDF, sentence-transformers, ChromaDB, watchdog, Node.js (for npx wrapper), Docker.

---

## Chunk 1: Project Scaffold

### Task 1: Create Project Structure and Configuration Files

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `package.json`
- Create: `bin/run.js`

- [ ] **Step 1: Initialize project with git and uv**
Run: `git init`
Run: `uv init --name MyDocsMCP`
Run: `uv add fastmcp pymupdf sentence-transformers chromadb watchdog langchain-text-splitters numpy`
Run: `uv add --group dev pytest ruff`

- [ ] **Step 2: Create `.env.example`**
Add the required environment variables: `PDF_DIR`, `CHROMA_DIR`, `METADATA_DIR`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `LOG_LEVEL`.

- [ ] **Step 3: Create `package.json`**
Configure the Node.js wrapper for npx support.

- [ ] **Step 4: Create `bin/run.js`**
Write the wrapper script to execute the Python MCP server with stdio inheritance.

- [ ] **Step 5: Commit Scaffold**
Run: `git add pyproject.toml .env.example package.json bin/run.js`
Run: `git commit -m "chore: scaffold project structure and configs"`

## Chunk 2: Ingestion Pipeline - Core Components

### Task 2: Implement PDF Extractor

**Files:**
- Create: `src/ingestion/extractor.py`
- Create: `tests/test_ingestion.py`

- [ ] **Step 1: Write test for PDFExtractor**
- [ ] **Step 2: Run test to verify it fails**
Run: `uv run pytest tests/test_ingestion.py -v`
- [ ] **Step 3: Implement `PDFExtractor`**
Use `fitz` (PyMuPDF) to extract text and basic metadata per page.
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**
Run: `git add src/ingestion/extractor.py tests/test_ingestion.py`
Run: `git commit -m "feat: implement PDF text and metadata extractor"`

### Task 3: Implement Text Chunker

**Files:**
- Create: `src/ingestion/chunker.py`

- [ ] **Step 1: Write test for ParentChildChunker**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `ParentChildChunker`**
Use Langchain's RecursiveCharacterTextSplitter for parent and child chunks.
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**
Run: `git add src/ingestion/chunker.py`
Run: `git commit -m "feat: implement parent-child chunking"`

### Task 4: Implement Local Embedder

**Files:**
- Create: `src/ingestion/embedder.py`

- [ ] **Step 1: Write test for LocalEmbedder**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `LocalEmbedder`**
Use `sentence-transformers` for embedding text chunks.
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**
Run: `git add src/ingestion/embedder.py`
Run: `git commit -m "feat: implement local embedding model"`

## Chunk 3: Ingestion Orchestration

### Task 5: Implement Ingestion Pipeline

**Files:**
- Create: `src/ingestion/pipeline.py`

- [ ] **Step 1: Write test for IngestionPipeline**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `IngestionPipeline`**
Wire the extractor, chunker, and embedder. Add ChromaDB integration and basic file hashing to avoid re-ingestion.
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**
Run: `git add src/ingestion/pipeline.py`
Run: `git commit -m "feat: implement ingestion pipeline"`

## Chunk 4: Retrieval and FastMCP Server

### Task 6: Implement Semantic Searcher

**Files:**
- Create: `src/retrieval/searcher.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write test for SemanticSearcher**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `SemanticSearcher`**
Query ChromaDB and format results. Implement tool functions like list_documents, cross_search, get_stats.
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**
Run: `git add src/retrieval/searcher.py tests/test_tools.py`
Run: `git commit -m "feat: implement semantic searcher and tools"`

### Task 7: Implement Watchdog and FastMCP Server

**Files:**
- Create: `src/watcher.py`
- Create: `src/server.py`

- [ ] **Step 1: Implement `start_watcher`**
Use `watchdog` to detect new or modified PDFs and trigger `pipeline.ingest()`.
- [ ] **Step 2: Implement FastMCP Server**
Define the MCP tools (`search_documents`, `list_documents`, `cross_topic_search`, `get_index_stats`, `ingest_new_documents`) and lifespan hook.
- [ ] **Step 3: Test MCP Server locally**
- [ ] **Step 4: Commit**
Run: `git add src/watcher.py src/server.py`
Run: `git commit -m "feat: implement fastmcp server and watchdog"`

## Chunk 5: Containerization

### Task 8: Docker and Docker Compose

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create `Dockerfile`**
Base it on python:3.12-slim. Install libmupdf-dev. Download the embedding model during build. Setup stdio entrypoint.
- [ ] **Step 2: Create `docker-compose.yml`**
Define the `my-docs-mcp` service with correct volume mounts and env vars.
- [ ] **Step 3: Test Docker build**
Run: `docker build -t my-docs-mcp:latest .`
- [ ] **Step 4: Commit**
Run: `git add Dockerfile docker-compose.yml`
Run: `git commit -m "feat: add docker containerization"`