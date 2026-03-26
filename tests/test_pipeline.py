import pytest
import os
import tempfile
import fitz
from pathlib import Path
from unittest.mock import MagicMock
from src.ingestion.pipeline import IngestionPipeline

@pytest.fixture
def mock_pipeline(monkeypatch):
    # Mock Chroma e Env vars
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("PDF_DIR", temp_dir)
    monkeypatch.setenv("CHROMA_DIR", temp_dir)
    
    pipeline = IngestionPipeline()
    # Mocking os componentes pesados para evitar instanciar embeddings no teste
    def mock_embed(texts):
        return [[0.1] * 384] * len(texts)
    pipeline.embedder.embed = MagicMock(side_effect=mock_embed)
    return pipeline, temp_dir

def test_pipeline_ingestion(mock_pipeline):
    pipeline, temp_dir = mock_pipeline
    
    # Criar um PDF temporário
    pdf_path = Path(temp_dir) / "test_module" / "test.pdf"
    pdf_path.parent.mkdir(parents=True)
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Conteúdo valioso para o RAG. " * 50)
    doc.save(str(pdf_path))
    doc.close()
    
    # Rodar ingestão
    result = pipeline.ingest()
    
    assert result["new"] == 1
    assert result["skipped"] == 0
    assert result["errors"] == 0
    
    # Tentar rodar de novo (deve dar skip)
    result_skip = pipeline.ingest()
    assert result_skip["new"] == 0
    assert result_skip["skipped"] == 1
    
    # Limpar
    os.remove(pdf_path)