import pytest
from src.ingestion.chunker import ParentChildChunker

def test_parent_child_chunking():
    chunker = ParentChildChunker(parent_chunk_size=1000, child_chunk_size=200)
    
    pages = [
        {
            "text": "A " * 500,  # Simulate long text
            "page": 1,
            "filename": "test.pdf"
        }
    ]
    
    parent_chunks, child_chunks = chunker.chunk(pages)
    
    assert len(parent_chunks) > 0
    assert len(child_chunks) > 0
    
    # Check linkage
    assert "parent_id" in child_chunks[0]
    assert child_chunks[0]["parent_id"] == parent_chunks[0]["id"]
    
    # Check inherited metadata
    assert child_chunks[0]["page"] == 1
    assert child_chunks[0]["filename"] == "test.pdf"
    
    # Basic size sanity
    assert len(child_chunks[0]["text"]) <= 200 * 5 # char estimation