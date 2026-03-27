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

### 2. Extremely Simple Configuration (Claude / Gemini Desktop)

To use the server, add the configuration below to your agent's JSON file (`claude_desktop_config.json` or Gemini's `settings.json`).

**Claude Path (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Gemini Path (macOS):** `~/.gemini/settings.json`

The server automatically resolves all data folders (`pdfs`, `metadata`, `chroma_db`) based on the project root. You only need to provide the absolute path where you cloned the repository:

```json
{
  "mcpServers": {
    "mydocsmcp": {
      "command": "uv",
      "args": [
        "--directory", "/Absolute/Path/To/Your/MyDocsMCP",
        "run",
        "mydocs-mcp"
      ]
    }
  }
}
```

**That's it!** No additional environment variables (`PYTHONPATH`, `PDF_DIR`, etc.) are required. The setup "Just Works"™.

---

## Exposed Tools

- `search_documents(query, top_k=5, discipline=None)`: Semantic search in the collection.
- `list_documents(discipline=None)`: Lists indexed PDFs.
- `cross_topic_search(query, disciplines)`: Cross-topic search across multiple disciplines.
- `get_index_stats()`: Vector database statistics.
- `ingest_new_documents(path=None, force_reindex=False)`: Forces manual re-ingestion.

---

## Local Development (Python)

We use the **uv** package manager:

```bash
# Install dependencies
uv sync

# Run the server
uv run mydocs-mcp
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
