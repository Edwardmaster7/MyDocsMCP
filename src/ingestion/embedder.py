import os
from sentence_transformers import SentenceTransformer

class LocalEmbedder:
    def __init__(self, model_name: str = None):
        # Fallback to a lighter model for tests or if not specified
        name = model_name or os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2")
        self.model = SentenceTransformer(name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Gera embeddings para uma lista de textos.
        Retorna uma lista de listas de floats (Chromadb format).
        """
        # encode retorna um numpy array de embeddings (shape: [num_texts, embedding_dim])
        embeddings_np = self.model.encode(texts)
        
        # Converte para list of lists of floats para maior compatibilidade (ex: com pydantic/chroma)
        return embeddings_np.tolist()