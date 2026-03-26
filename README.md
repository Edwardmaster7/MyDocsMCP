# MyDocsMCP: MCP Server para Acervo de PDFs

Este projeto é um **Model Context Protocol (MCP) Server** que permite realizar buscas semânticas (RAG local) sobre acervos de documentos PDF. Ele utiliza o framework **FastMCP**, o banco de vetores **ChromaDB** e modelos de embeddings locais do **Sentence Transformers**.

## Arquitetura
- **Busca Semântica:** RAG (Retrieval-Augmented Generation) 100% local (offline).
- **Embeddings:** `paraphrase-multilingual-mpnet-base-v2` (suporte a Português).
- **Vector DB:** ChromaDB persistente.
- **Watcher:** Monitora novos PDFs na pasta `./data/pdfs` e indexa-os automaticamente via `watchdog`.

---

## Como Usar

### 1. Preparação dos Dados
Coloque seus PDFs na pasta `./data/pdfs/`. Se quiser organizar por disciplinas, crie subpastas:
```text
data/pdfs/
  ├── IA-Generativa/
  │   └── aula1.pdf
  └── Machine-Learning/
      └── fundamentals.pdf
```
O nome da subpasta será usado como metadado `discipline`.

### 2. Rodando via Docker (Recomendado)

O Docker garante um ambiente isolado com todas as dependências do sistema (como a biblioteca `libmupdf`).

```bash
# Build da imagem (baixa o modelo de embeddings no build)
docker build -t mydocs-mcp .

# Rodando o container (montando os volumes de PDFs e banco de dados)
docker run -i --rm \
  -v "$(pwd)/data/pdfs:/data/pdfs:ro" \
  -v "mydocs-chroma:/data/chroma_db" \
  mydocs-mcp
```

### 3. Configuração no Claude Desktop

Para utilizar o servidor no Claude Desktop, adicione a configuração abaixo no seu arquivo `claude_desktop_config.json`:

**Caminho no macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

#### Usando Docker (mais estável):
```json
{
  "mcpServers": {
    "mydocsmcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/Users/SEU_USUARIO/Caminho/Para/MyDocsMCP/data/pdfs:/data/pdfs:ro",
        "-v", "mydocs-chroma:/data/chroma_db",
        "mydocs-mcp:latest"
      ]
    }
  }
}
```

#### Usando uv (diretamente no sistema):
```json
{
  "mcpServers": {
    "mydocsmcp": {
      "command": "uv",
      "args": [
        "--directory", "/Users/SEU_USUARIO/Caminho/Para/MyDocsMCP",
        "run", "python", "src/server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/SEU_USUARIO/Caminho/Para/MyDocsMCP",
        "PDF_DIR": "/Users/SEU_USUARIO/Caminho/Para/MyDocsMCP/data/pdfs"
      }
    }
  }
}
```

---

## Ferramentas Expostas (Tools)

- `search_documents(query, top_k=5, discipline=None)`: Busca semântica no acervo.
- `list_documents(discipline=None)`: Lista PDFs indexados.
- `cross_topic_search(query, disciplines)`: Busca transversal em múltiplos temas.
- `get_index_stats()`: Estatísticas do banco de vetores.
- `ingest_new_documents(path=None, force_reindex=False)`: Força re-ingestão manual.

---

## Desenvolvimento Local (Python)

Se desejar rodar localmente sem Docker, utilize o gerenciador de pacotes **uv**:

```bash
# Instalar dependências
uv sync

# Rodar o servidor (com PYTHONPATH configurado)
PYTHONPATH=. uv run python src/server.py
```

### Rodando Testes
```bash
uv run pytest
```

---

## Tecnologias Utilizadas
- [FastMCP](https://github.com/jlowin/fastmcp)
- [uv](https://github.com/astral-sh/uv)
- [ChromaDB](https://www.trychroma.com/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Sentence-Transformers](https://www.sbert.net/)
- [Watchdog](https://github.com/gorakhargosh/python-watchdog)
