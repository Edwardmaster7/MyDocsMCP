import pytest
from src.ingestion.embedder import LocalEmbedder
import numpy as np

def test_embed_texts():
    embedder = LocalEmbedder(model_name="all-MiniLM-L6-v2")
    
    texts = ["O rato roeu a roupa", "O gato comeu o rato"]
    embeddings = embedder.embed(texts)
    
    assert len(embeddings) == 2
    assert isinstance(embeddings, list)
    # The length depends on the model, but usually >= 384 for these small ones
    assert len(embeddings[0]) > 0 
    assert isinstance(embeddings[0][0], float)