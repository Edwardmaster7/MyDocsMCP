FROM python:3.13-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para o uv e PyMuPDF
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala o uv globalmente na imagem e garante que o path está certo
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copia os arquivos de lock e projeto
COPY pyproject.toml uv.lock ./

# Instala as dependências de produção via uv 
RUN uv sync --no-dev

# Configura o PYTHONPATH
ENV PYTHONPATH=/app

# Download do modelo de embeddings durante o build para não baixar em runtime
RUN uv run python -c "from sentence_transformers import SentenceTransformer; \
               SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')"

# Copia o source code
COPY src/ ./src/


# Volumes para persistência de dados
VOLUME ["/data/pdfs", "/data/chroma_db", "/data/metadata"]

# O MCP em stdio mode lê do stdin e escreve pro stdout
CMD ["uv", "run", "python", "src/server.py"]