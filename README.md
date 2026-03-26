# MyDocsMCP: MCP Server for PDF Collections

This project is a **Model Context Protocol (MCP) Server** that enables semantic search (local RAG) over a collection of PDF documents. It uses the **FastMCP** framework, the **ChromaDB** vector database, and local embedding models from **Sentence Transformers**.

## Architecture
- **Semantic Search:** 100% local (offline) RAG (Retrieval-Augmented Generation).
- **Embeddings:** `paraphrase-multilingual-mpnet-base-v2` (supports Portuguese).
- **Vector DB:** Persistent ChromaDB.
- **Watcher:** Monitors new PDFs in the `./data/pdfs` folder and indexes them automatically via `watchdog`.

---

## How to Use

### 1. Data Preparation
Place your PDFs in the `./data/pdfs/` folder. If you want to organize them by disciplines, create subfolders:
```text
data/pdfs/
  ├── Generative-AI/
  │   └── lecture1.pdf
  └── Machine-Learning/
      └── fundamentals.pdf
```
The subfolder name will be used as the `discipline` metadata.

### 2. Running via Docker (Recommended)

Docker ensures an isolated environment with all system dependencies (like the `libmupdf` library).

```bash
# Build the image (downloads the embeddings model during the build)
docker build -t mydocs-mcp .

# Run the container (mounting the PDFs and database volumes)
docker run -i --rm \
  -v "$(pwd)/data/pdfs:/data/pdfs:ro" \
  -v "mydocs-chroma:/data/chroma_db" \
  mydocs-mcp
```

### 3. Claude Desktop Configuration

To use the server in Claude Desktop, add the configuration below to your `claude_desktop_config.json` file:

**macOS Path:** `~/Library/Application Support/Claude/claude_desktop_config.json`

#### Using Docker (more stable):
```json
{
  "mcpServers": {
    "mydocsmcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/Users/YOUR_USER/Path/To/MyDocsMCP/data/pdfs:/data/pdfs:ro",
        "-v", "mydocs-chroma:/data/chroma_db",
        "mydocs-mcp:latest"
      ]
    }
  }
}
```

#### Using uv (directly on the system):
```json
{
  "mcpServers": {
    "mydocsmcp": {
      "command": "uv",
      "args": [
        "--directory", "/Users/YOUR_USER/Path/To/MyDocsMCP",
        "run", "python", "src/server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/YOUR_USER/Path/To/MyDocsMCP",
        "PDF_DIR": "/Users/YOUR_USER/Path/To/MyDocsMCP/data/pdfs"
      }
    }
  }
}
```

---

## Exposed Tools

- `search_documents(query, top_k=5, discipline=None)`: Semantic search in the collection.
- `list_documents(discipline=None)`: Lists indexed PDFs.
- `cross_topic_search(query, disciplines)`: Cross-topic search across multiple disciplines.
- `get_index_stats()`: Vector database statistics.
- `ingest_new_documents(path=None, force_reindex=False)`: Forces manual re-ingestion.

---

## Local Development (Python)

If you wish to run locally without Docker, use the **uv** package manager:

```bash
# Install dependencies
uv sync

# Run the server (with PYTHONPATH configured)
PYTHONPATH=. uv run python src/server.py
```

### Running Tests
```bash
uv run pytest
```

---

## Technologies Used
- [FastMCP](https://github.com/jlowin/fastmcp)
- [uv](https://github.com/astral-sh/uv)
- [ChromaDB](https://www.trychroma.com/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Sentence-Transformers](https://www.sbert.net/)
- [Watchdog](https://github.com/gorakhargosh/python-watchdog)