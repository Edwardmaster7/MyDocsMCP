import pytest
import os
import tempfile
import chromadb
from src.retrieval.searcher import SemanticSearcher
from unittest.mock import MagicMock

@pytest.fixture
def mock_searcher(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("CHROMA_DIR", temp_dir)
    monkeypatch.setenv("METADATA_DIR", temp_dir)
    
    # Inicia o chromadb dummy
    chroma = chromadb.PersistentClient(path=temp_dir)
    col = chroma.get_or_create_collection("fiap_pdfs")
    
    # Popula com alguns dados fakes para o teste de search
    col.upsert(
        ids=["fake_1", "fake_2"],
        embeddings=[[0.1]*384, [0.2]*384],
        documents=["RAG é Retrieval Augmented Generation", "LLMs são muito bons em RAG"],
        metadatas=[{"filename": "doc1.pdf", "discipline": "ai", "page": 1, "parent_id": "1"}, 
                   {"filename": "doc2.pdf", "discipline": "ai", "page": 2, "parent_id": "2"}]
    )
    
    searcher = SemanticSearcher()
    # Mocking o embedder que o searcher usa
    searcher.embedder.embed = MagicMock(return_value=[[0.1]*384])
    
    return searcher

@pytest.mark.asyncio
async def test_semantic_search(mock_searcher):
    results = await mock_searcher.search("RAG e LLM", top_k=2)
    
    assert len(results) == 2
    assert "RAG é Retrieval Augmented Generation" in [r["text"] for r in results]
    assert "ai" in [r["metadata"]["discipline"] for r in results]