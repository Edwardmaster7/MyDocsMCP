import pytest
import os
from pathlib import Path
import tempfile
import fitz
from src.ingestion.extractor import PDFExtractor

@pytest.fixture
def sample_pdf():
    # Cria um PDF temporário para teste
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Teste de extração de texto.")
    
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Página dois.")
    
    doc.save(path)
    doc.close()
    
    yield Path(path)
    
    # Cleanup
    os.remove(path)

def test_extract_pdf_pages(sample_pdf):
    extractor = PDFExtractor()
    pages = extractor.extract(sample_pdf)
    
    assert len(pages) == 2
    assert "Teste de extração de texto." in pages[0]["text"]
    assert "Página dois." in pages[1]["text"]
    assert pages[0]["page"] == 1
    assert pages[1]["page"] == 2
    assert pages[0]["filename"] == sample_pdf.name