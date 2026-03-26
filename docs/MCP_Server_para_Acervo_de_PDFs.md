# MCP Server para Acervo de PDFs

## Visão Geral e Arquitetura

Este documento propõe uma arquitetura robusta e escalável para um **MCP Server** que expõe ferramentas de busca semântica e navegação sobre um acervo de PDFs da pós-graduação, distribuídos em pastas por disciplina/módulo. O servidor é disponibilizado tanto via **Docker** (ambiente isolado, produção) quanto via **npx** (execução direta pelo Node, ideal para integração rápida com clientes MCP como Claude Desktop, Cursor e VS Code).

A escolha arquitetural central é: **RAG pipeline local com busca semântica via vector database**, exposto como MCP Server com transporte stdio. Isso significa que o LLM recebe ferramentas que consultam o índice de embeddings — obtendo respostas contextuais, não apenas trechos brutos — sem depender de nenhuma API externa paga.[^1][^2][^3]

---

## Por Que Esta Abordagem?

A alternativa mais simples — deixar o LLM ler PDFs raw — não escala. Com dezenas ou centenas de PDFs, o contexto do LLM fica saturado. A alternativa correta é um **pipeline RAG** (Retrieval-Augmented Generation), onde:[^1]

1. PDFs são pré-processados e divididos em *chunks* de texto
2. Cada chunk é transformado em um vetor numérico (embedding) que captura o significado semântico
3. Esses vetores são armazenados em um *vector database*
4. Quando o LLM chama uma tool, o sistema busca os chunks semanticamente mais relevantes e os retorna como contexto[^4]

Isso contrasta com busca por palavra-chave (Ctrl+F), que retorna apenas correspondências exatas. Busca semântica entende intenção e contexto: uma query sobre "redes neurais convolucionais" pode retornar chunks que falam de "CNNs" ou "filtros em camadas de convolução", mesmo sem as palavras exatas.[^4]

---

## Stack Tecnológica Recomendada

### Linguagem e Framework MCP

**Python com FastMCP** é a escolha recomendada. Razões:[^5][^6]

- FastMCP é o framework líder para construção de MCP servers em Python, com decorators simples (`@mcp.tool()`, `@mcp.resource()`)
- Integra nativamente com toda a pilha de data science: `sentence-transformers`, `PyMuPDF`, `ChromaDB`
- Suporte a transporte `stdio` (necessário para Docker MCP e npx)[^7][^2]
- Publicação via PyPI (equivalente ao npm para Python, viabilizando `uvx` — análogo ao npx)

### Extração de PDF

**PyMuPDF (fitz)** para extração de texto — rápido, suporta PDFs complexos com colunas, e retorna metadados como número de página, para que cada chunk saiba sua origem exata.[^5]

### Embeddings: Local vs. API

| Opção                       | Modelo                                         | Custo            | Privacidade            | Qualidade      |
| ----------------------------- | ---------------------------------------------- | ---------------- | ---------------------- | -------------- |
| **Local (recomendado)** | `all-MiniLM-L6-v2` via sentence-transformers | Zero             | Total                  | Boa para PT/EN |
| Local avançado               | `paraphrase-multilingual-mpnet-base-v2`      | Zero             | Total                  | Melhor para PT |
| OpenAI API                    | `text-embedding-3-small`                     | ~$0.02/1M tokens | Dados saem da máquina | Excelente      |

Para um acervo académico privado como PDFs da FIAP, **embeddings locais com sentence-transformers são a escolha correta**. Todo processamento acontece na máquina, zero custo, sem necessidade de chaves de API externas. O modelo `paraphrase-multilingual-mpnet-base-v2` tem suporte nativo a Português.[^3][^8]

### Vector Database: ChromaDB

**ChromaDB** é a escolha ideal para este caso de uso:[^9][^10]

- Roda **embedded** dentro do próprio container Docker (sem servidor separado)
- Persiste índices em disco (volume Docker montado)
- Suporte nativo a Python, LangChain, LlamaIndex
- HNSW indexing garante query time constante (~3ms) independente do número de documentos[^11]
- A reescrita em Rust em 2025 entregou 4x mais velocidade nas operações de escrita e query[^9]

Qdrant seria preferível apenas se houvesse requisito de escala enterprise (bilhões de vetores, múltiplos nós). Para um acervo pessoal/educacional, ChromaDB é suficiente e muito mais simples.[^12][^10]

---

## Arquitetura de Pastas do Projeto

```
my-docs-mcp/
├── Dockerfile
├── docker-compose.yml
├── package.json              # Para npx (wrapper Node que chama o Python)
├── bin/
│   └── run.js                # Entrypoint npx
├── src/
│   ├── server.py             # FastMCP server — tools e resources
│   ├── ingestion/
│   │   ├── pipeline.py       # Orquestra ingestão de PDFs
│   │   ├── extractor.py      # PyMuPDF: extrai texto + metadados
│   │   ├── chunker.py        # Parent-child chunking strategy
│   │   └── embedder.py       # sentence-transformers local
│   ├── retrieval/
│   │   ├── searcher.py       # Busca semântica + keyword no ChromaDB
│   │   └── reranker.py       # Re-ranking opcional dos resultados
│   ├── watcher.py            # watchdog: detecta novos PDFs e reindexa
│   └── config.py             # Configurações via env vars
├── data/
│   ├── pdfs/                 # << VOLUME MONTADO — seus PDFs aqui
│   │   ├── fase-1-fundamentos/
│   │   ├── fase-2-ml/
│   │   └── fase-3-deep-learning/
│   └── chroma_db/            # << VOLUME MONTADO — índice persistido
├── tests/
│   ├── test_ingestion.py
│   └── test_tools.py
├── pyproject.toml
└── .env.example
```

---

## As Tools MCP Expostas ao LLM

O servidor expõe um conjunto de ferramentas que o LLM pode chamar autonomamente:

### Tool 1: `search_documents`

```
Descrição: Busca semântica no acervo completo. Retorna os chunks mais relevantes
           com metadados de origem (arquivo, página, disciplina).
Parâmetros:
  - query: string        # Pergunta ou tema a buscar
  - top_k: int = 5       # Número de resultados
  - discipline: str|None # Filtro opcional por pasta/disciplina
  - min_score: float     # Threshold de similaridade (0-1)
```

### Tool 2: `list_documents`

```
Descrição: Lista todos os PDFs indexados, organizados por disciplina/pasta.
           Retorna metadados: nome, data de ingestão, número de páginas, chunks.
Parâmetros:
  - discipline: str|None  # Filtra por pasta específica
```

### Tool 3: `get_document_summary`

```
Descrição: Retorna um resumo gerado do documento (primeiros N chunks) ou
           busca chunks de uma seção específica de um PDF.
Parâmetros:
  - filename: string      # Nome do arquivo PDF
  - section: str|None     # Seção específica (ex: "introdução", "conclusão")
```

### Tool 4: `cross_topic_search`

```
Descrição: Busca um tema transversalmente em múltiplas disciplinas.
           Útil para conectar conceitos entre módulos do curso.
Parâmetros:
  - query: string
  - disciplines: list[str] # Lista de pastas a consultar
  - top_k_per_discipline: int = 3
```

### Tool 5: `ingest_new_documents`

```
Descrição: Força re-ingestão de PDFs novos ou modificados na pasta data/pdfs/.
           Detecta via hash MD5 — não reindexa arquivos já processados.
Parâmetros:
  - path: str|None        # Pasta específica ou todas se None
  - force_reindex: bool   # Reprocessar mesmo arquivos já indexados
```

### Tool 6: `get_index_stats`

```
Descrição: Retorna estatísticas do índice: total de documentos, chunks,
           última atualização, distribuição por disciplina.
```

---

## Pipeline de Ingestão: Chunking Strategy

A qualidade da busca depende da estratégia de *chunking*. A abordagem recomendada é **Parent-Child Chunking**:[^13]

- **Parent chunks**: Blocos grandes (800-1200 tokens) que preservam contexto completo de seções
- **Child chunks**: Blocos pequenos (150-300 tokens) usados para busca vetorial precisa
- Quando um child chunk é encontrado na busca, o **parent** correspondente é retornado ao LLM — garantindo contexto rico sem ruído

Cada chunk carrega metadados essenciais:

```json
{
  "doc_id": "hash_md5_do_pdf",
  "filename": "aula-03-redes-neurais.pdf",
  "discipline": "fase-2-ml",
  "page_number": 12,
  "chunk_index": 7,
  "parent_chunk_id": "abc123",
  "text": "...",
  "ingested_at": "2026-03-26T10:00:00Z"
}
```

---

## Sistema de Atualização Incremental (Watcher)

Este é o componente crítico para um acervo em crescimento. O `watcher.py` usa a biblioteca **watchdog** para monitorar a pasta `data/pdfs/` em tempo real:[^14]

```
Fluxo quando um novo PDF é adicionado:
1. watchdog detecta evento FileCreated / FileModified
2. Calcula MD5 hash do arquivo
3. Consulta tabela de metadados: arquivo já foi indexado com este hash?
   - SIM: ignora (skip)
   - NÃO: dispara pipeline de ingestão assíncrono
4. Pipeline: extração → chunking → embedding → upsert no ChromaDB
5. Atualiza tabela de metadados (SQLite leve, embutido)
6. Log de conclusão com estatísticas
```

Isso garante que adicionar novos PDFs ao longo do semestre é transparente — basta copiar o arquivo na pasta correta e o índice se atualiza automaticamente, sem precisar reiniciar o servidor.[^15]

---

## Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema para PyMuPDF
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Download do modelo de embeddings no build (não em runtime)
RUN python -c "from sentence_transformers import SentenceTransformer; \
               SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')"

COPY src/ ./src/

# Volumes para dados persistentes
VOLUME ["/data/pdfs", "/data/chroma_db"]

# Transporte stdio — obrigatório para MCP via Docker
CMD ["python", "-m", "src.server"]
```

**Nota crítica**: o modelo de embeddings é baixado durante o `docker build`, não em runtime. Isso evita latência na primeira query e garante que o container funcione offline.[^7]

---

## docker-compose.yml

```yaml
version: '3.9'

services:
  my-docs-mcp:
    build: .
    image: my-docs-mcp:latest
    stdin_open: true      # necessário para transporte stdio
    tty: false
    volumes:
      - ./data/pdfs:/data/pdfs:ro          # PDFs (read-only no container)
      - chroma_db:/data/chroma_db          # Índice vetorial persistido
      - sqlite_meta:/data/metadata         # Metadados de ingestão
    environment:
      - PDF_DIR=/data/pdfs
      - CHROMA_DIR=/data/chroma_db
      - METADATA_DIR=/data/metadata
      - EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
      - CHUNK_SIZE=300
      - CHUNK_OVERLAP=50
      - LOG_LEVEL=INFO
    restart: unless-stopped

volumes:
  chroma_db:
  sqlite_meta:
```

---

## Configuração npx (Wrapper Node.js)

Para clientes que preferem `npx` (como Claude Desktop), um wrapper Node leve chama o servidor Python:[^2]

### `package.json`

```json
{
  "name": "fiap-pdf-mcp",
  "version": "1.0.0",
  "description": "MCP server para acervo de PDFs da pós-tech FIAP",
  "bin": {
    "fiap-pdf-mcp": "./bin/run.js"
  },
  "scripts": {
    "start": "node bin/run.js"
  },
  "dependencies": {}
}
```

### `bin/run.js`

```javascript
#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

const serverPath = path.join(__dirname, '..', 'src', 'server.py');
const pdfDir = process.env.PDF_DIR || path.join(__dirname, '..', 'data', 'pdfs');

const proc = spawn('python', [serverPath], {
  env: { ...process.env, PDF_DIR: pdfDir },
  stdio: 'inherit'   // passa stdin/stdout direto — protocolo MCP stdio
});

proc.on('exit', (code) => process.exit(code));
```

### Configuração no `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fiap-pdf-mcp": {
      "command": "npx",
      "args": ["fiap-pdf-mcp"],
      "env": {
        "PDF_DIR": "/Users/eduardo/Documents/fiap/pdfs"
      }
    }
  }
}
```

**Ou via Docker no mesmo config:**

```json
{
  "mcpServers": {
    "fiap-pdf-mcp-docker": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/Users/eduardo/Documents/fiap/pdfs:/data/pdfs:ro",
        "-v", "fiap-chroma:/data/chroma_db",
        "my-docs-mcp:latest"
      ]
    }
  }
}
```

---

## Código-Fonte: Implementação核心 do Servidor

### `src/server.py` — FastMCP server principal

```python
from fastmcp import FastMCP
from src.retrieval.searcher import SemanticSearcher
from src.ingestion.pipeline import IngestionPipeline
from src.watcher import start_watcher
import asyncio, os

mcp = FastMCP("FIAP PDF Knowledge Base")
searcher = SemanticSearcher()
pipeline = IngestionPipeline()

@mcp.tool()
async def search_documents(query: str, top_k: int = 5, discipline: str = None) -> str:
    """
    Busca semanticamente no acervo de PDFs da pós-tech FIAP.
    Retorna trechos relevantes com referência ao documento e página.
  
    Args:
        query: Pergunta ou tema a pesquisar
        top_k: Número de resultados (padrão: 5)
        discipline: Filtrar por disciplina/pasta específica (opcional)
    """
    results = await searcher.search(query, top_k=top_k, filter_discipline=discipline)
    return searcher.format_results(results)

@mcp.tool()
async def list_documents(discipline: str = None) -> str:
    """Lista todos os PDFs indexados, opcionalmente filtrado por disciplina."""
    return await searcher.list_documents(discipline=discipline)

@mcp.tool()
async def cross_topic_search(query: str, disciplines: list[str], top_k_per_discipline: int = 3) -> str:
    """
    Busca transversal de um tema em múltiplas disciplinas.
    Útil para conectar conceitos entre diferentes módulos do curso.
    """
    return await searcher.cross_search(query, disciplines, top_k_per_discipline)

@mcp.tool()
async def get_index_stats() -> str:
    """Retorna estatísticas do índice: total de documentos, chunks, última atualização."""
    return await searcher.get_stats()

@mcp.tool()
async def ingest_new_documents(path: str = None, force_reindex: bool = False) -> str:
    """
    Força re-ingestão de PDFs novos ou modificados.
    Normalmente automático via watcher, mas pode ser chamado manualmente.
    """
    result = await pipeline.ingest(base_path=path, force=force_reindex)
    return f"Ingestão concluída: {result['new']} novos, {result['skipped']} ignorados, {result['errors']} erros."

# Ingestão inicial ao iniciar + watcher em background
@mcp.lifespan()
async def lifespan():
    await pipeline.ingest()          # indexa PDFs ainda não processados
    asyncio.create_task(start_watcher(pipeline))   # watcher em background
    yield

if __name__ == "__main__":
    mcp.run()
```

### `src/ingestion/pipeline.py` — Ingestão com ingestão incremental

```python
import hashlib, sqlite3, os
from pathlib import Path
from src.ingestion.extractor import PDFExtractor
from src.ingestion.chunker import ParentChildChunker
from src.ingestion.embedder import LocalEmbedder
import chromadb

class IngestionPipeline:
    def __init__(self):
        self.pdf_dir = Path(os.environ["PDF_DIR"])
        self.chroma = chromadb.PersistentClient(path=os.environ["CHROMA_DIR"])
        self.collection = self.chroma.get_or_create_collection("fiap_pdfs")
        self.extractor = PDFExtractor()
        self.chunker = ParentChildChunker()
        self.embedder = LocalEmbedder()
        self._init_metadata_db()

    def _file_hash(self, path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()

    async def ingest(self, base_path=None, force=False):
        root = Path(base_path) if base_path else self.pdf_dir
        new, skipped, errors = 0, 0, 0
      
        for pdf in root.rglob("*.pdf"):
            try:
                fhash = self._file_hash(pdf)
                discipline = pdf.parent.name
              
                if not force and self._already_indexed(fhash):
                    skipped += 1
                    continue
              
                # Pipeline: extração → chunking → embedding → upsert
                pages = self.extractor.extract(pdf)
                parent_chunks, child_chunks = self.chunker.chunk(pages)
                embeddings = self.embedder.embed([c["text"] for c in child_chunks])
              
                # Upsert no ChromaDB em batches de 500
                self._batch_upsert(child_chunks, embeddings, pdf, discipline, fhash)
                self._register_indexed(pdf, fhash)
                new += 1
            except Exception as e:
                errors += 1
                print(f"Erro ao processar {pdf}: {e}", flush=True)
      
        return {"new": new, "skipped": skipped, "errors": errors}

    def _batch_upsert(self, chunks, embeddings, pdf, discipline, fhash, batch_size=500):
        """Insere em batches para evitar problemas de memória com muitos PDFs."""
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_embs = embeddings[i:i+batch_size]
            self.collection.upsert(
                ids=[f"{fhash}_{j}" for j in range(i, i+len(batch_chunks))],
                embeddings=batch_embs,
                documents=[c["text"] for c in batch_chunks],
                metadatas=[{
                    "filename": pdf.name,
                    "discipline": discipline,
                    "page": c["page"],
                    "doc_hash": fhash
                } for c in batch_chunks]
            )
```

---

## Escalabilidade: Preparando para Muitos PDFs

O acervo vai crescer ao longo do curso. A arquitetura foi desenhada para escalar sem refatoração:[^16][^11]

| Cenário       | PDFs      | Chunks estimados | Estratégia                                                    |
| -------------- | --------- | ---------------- | -------------------------------------------------------------- |
| Fase inicial   | ~20 PDFs  | ~5.000 chunks    | ChromaDB embedded, funciona out-of-the-box                     |
| Meio do curso  | ~80 PDFs  | ~20.000 chunks   | Mesma stack — ChromaDB HNSW é constante em latência         |
| Curso completo | ~200 PDFs | ~50.000 chunks   | Mesma stack — adicionar filtros por disciplina para precisão |
| Escala futura  | 500+ PDFs | 100k+ chunks     | Migrar para Qdrant com Docker separado (drop-in replacement)   |

**Práticas obrigatórias para muitos PDFs:**

1. **Batch inserts**: nunca inserir chunks um a um — usar lotes de 500[^11]
2. **Hash-based deduplication**: nunca reprocessar arquivos já indexados[^15]
3. **Filtros de metadados**: ao buscar, usar `where={"discipline": "fase-2-ml"}` reduz o espaço de busca
4. **Modelo de embeddings fixo**: trocar o modelo exige re-indexar tudo — escolha um e mantenha[^13]
5. **Backup do volume chroma_db**: é o ativo mais valioso — o índice de todo o trabalho

---

## Fluxo Completo do Agente de IA para Implementação

Este plano pode ser executado por um agente de IA (como Claude Code) em etapas ordenadas:

### Fase 1 — Scaffold do Projeto

```
1. Criar estrutura de pastas conforme especificado
2. Gerar pyproject.toml com dependências:
   fastmcp, pymupdf, sentence-transformers, chromadb, watchdog, sqlite3
3. Criar .env.example com todas as variáveis de configuração
4. Gerar package.json e bin/run.js para suporte npx
```

### Fase 2 — Pipeline de Ingestão

```
5. Implementar extractor.py: PyMuPDF extrai texto por página + metadados
6. Implementar chunker.py: parent-child chunking com RecursiveCharacterTextSplitter
7. Implementar embedder.py: SentenceTransformer local, batch encode
8. Implementar pipeline.py: orquestra as etapas + SQLite para tracking
9. Testes unitários: test_ingestion.py com PDFs de fixture pequenos
```

### Fase 3 — Servidor MCP

```
10. Implementar searcher.py: ChromaDB similarity_search + formatação de resultados
11. Implementar server.py: FastMCP com todas as tools e lifespan
12. Implementar watcher.py: watchdog FileSystemEventHandler → pipeline.ingest()
13. Testes de integração: iniciar server, ingerir PDF de teste, chamar tools
```

### Fase 4 — Containerização

```
14. Dockerfile: build multi-stage, download de modelo no build, não runtime
15. docker-compose.yml: volumes para pdfs e chroma_db, env vars
16. Testar: docker build → docker run -i → conectar MCP Inspector
17. Configurar claude_desktop_config.json com o container
```

### Fase 5 — Publicação npx

```
18. Testar wrapper Node: npx fiap-pdf-mcp invoca src/server.py corretamente
19. Adicionar ao PATH local ou publicar no npm registry (opcional)
20. Documentar uso no README.md
```

---

## Dependências Python (`pyproject.toml`)

```toml
[project]
name = "fiap-pdf-mcp"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    "fastmcp>=0.9",
    "pymupdf>=1.24",                           # extração de PDF
    "sentence-transformers>=3.0",              # embeddings locais
    "chromadb>=0.5",                           # vector database
    "watchdog>=4.0",                           # file system watcher
    "langchain-text-splitters>=0.2",           # RecursiveCharacterTextSplitter
    "numpy>=1.26",
]

[project.scripts]
fiap-pdf-mcp = "src.server:main"
```

---

## Considerações de Segurança e Operação

**Segurança do volume**: o volume `./data/pdfs` é montado como **read-only** no container (`ro`). O servidor MCP só lê PDFs, nunca modifica. Isso previne que um LLM mal instruído sobrescreva seus arquivos.[^17]

**Transporte stdio**: todo MCP via Docker deve usar transporte `stdio`. O container recebe `-i` (interactive stdin) e os dados fluem pelo stdin/stdout — não há porta HTTP exposta, o que elimina uma superfície de ataque.[^7]

**Metadados SQLite**: o banco de tracking de arquivos indexados fica num volume separado (`sqlite_meta`). Isso permite recriar o container sem perder o registro de o que já foi indexado.

**Modelo offline**: após o primeiro `docker build`, o servidor funciona completamente offline — nenhum dado dos seus PDFs sai da máquina.[^8][^3]

---

## Resumo das Decisões Arquiteturais

| Decisão              | Escolha                                   | Justificativa                                       |
| --------------------- | ----------------------------------------- | --------------------------------------------------- |
| Framework MCP         | FastMCP (Python)                          | Mais maduro, melhor ecossistema data science[^5]    |
| Extração PDF        | PyMuPDF                                   | Mais rápido e robusto que pdfplumber/pypdf2        |
| Embeddings            | sentence-transformers local               | Zero custo, privacidade total, multilíngue[^3][^8] |
| Modelo embedding      | `paraphrase-multilingual-mpnet-base-v2` | Suporte nativo ao Português                        |
| Vector DB             | ChromaDB persistent                       | Simples, embutido, escalável até 100k+ chunks[^9] |
| Chunking              | Parent-child                              | Melhor precisão + contexto rico[^13]               |
| Ingestão incremental | Hash MD5 + SQLite                         | Eficiente, sem reprocessamento desnecessário[^15]  |
| Watcher               | watchdog Python                           | Detecção em tempo real de novos PDFs[^14]         |
| Transporte            | stdio                                     | Padrão MCP para Docker[^7][^2]                     |
| Segurança volume     | read-only mount                           | LLM nunca modifica seus arquivos[^17]               |

---

## References

1. [Does MCP Kill Vector Search?](https://www.llamaindex.ai/blog/does-mcp-kill-vector-search) - Our thesis is that agents will still need preprocessing and indexing layers for rapid semantic looku...
2. [How to Build a Custom MCP Server with TypeScript](https://www.freecodecamp.org/news/how-to-build-a-custom-mcp-server-with-typescript-a-handbook-for-developers/) - This handbook explains how it works with real-world analogies, and shows you how to build a custom M...
3. [[Tool] Servidor MCP pequeno para RAG local baseado em ...](https://www.reddit.com/r/LocalLLaMA/comments/1pcbwnd/tool_tiny_mcp_server_for_local_faissbased_rag_no/) - Não, não é um wrapper para OpenAI – todo embedding + busca acontece localmente com FAISS + sentence-...
4. [A Deep Dive into the PDF Search MCP Server by Stano](https://skywork.ai/skypage/en/unlocking-pdfs-ai-era/1977640522127835136) - In this deep dive, we'll explore its architecture, walk through a hands-on guide, compare it to the ...
5. [How to Build MCP Servers in Python: Complete FastMCP ...](https://www.firecrawl.dev/blog/fastmcp-tutorial-building-mcp-servers-python) - This tutorial covers everything from setup to deployment, enabling you to build production-ready MCP...
6. [Building and deploying a Python MCP server with ...](https://circleci.com/blog/building-and-deploying-a-python-mcp-server-with-fastmcp/) - In this tutorial, you will learn to build a document parsing server that enables MCP hosts to unders...
7. [Top 5 MCP Server Best Practices](https://www.docker.com/blog/mcp-server-best-practices/) - Design secure, scalable MCP servers using these 5 best practices. Learn how to test, package, and op...
8. [Generating text embeddings locally using sentence-transformers](https://saeedesmaili.com/how-to-use-sentencetransformers-to-generate-text-embeddings-locally/) - In this post, I'll share my experience using the sentence-transformers library for this purpose and ...
9. [Chroma DB Vs Qdrant - Key Differences](https://airbyte.com/data-engineering-resources/chroma-db-vs-qdrant) - While Qdrant offers enterprise-grade production capabilities with advanced filtering and horizontal ...
10. [Chroma vs Qdrant: Best Vector Database for Local Development](https://zenvanriel.nl/ai-engineer-blog/chroma-vs-qdrant-local-development/) - Consistent scaling model. Qdrant's architecture scales the same way from development to production. ...
11. [Introduction to Vector Databases using ChromaDB - Dataquest](https://www.dataquest.io/blog/introduction-to-vector-databases-using-chromadb/) - Learn when brute-force breaks, how vector databases speed up semantic search, and how to build fast ...
12. [ChromaDB vs Qdrant: Which Vector Database is Right for ...](https://www.waterflai.ai/blog/chromadb-vs-qdrant-which-vector-database-is-right-for-you/) - A comprehensive comparison of performance, scalability, and features to help you select the best vec...
13. [MCP Documentation Server](https://mcpservers.org/servers/andrea9293/mcp-documentation-server) - Documents are stored in an embedded Orama vector database with hybrid search (full-text + vector), i...
14. [graphy-watch](https://lib.rs/crates/graphy-watch) - Watches a project directory for file changes and incrementally re-indexes only the affected files. U...
15. [iflow-mcp/qdrant-mcp-server](https://www.npmjs.com/package/@iflow-mcp%2Fqdrant-mcp-server) - Incremental Updates: Only re-index changed files for fast updates; Smart Ignore Patterns: Respects ....
16. [Issues with large PDF file retrieval in ChromaDB vector database](https://community.latenode.com/t/issues-with-large-pdf-file-retrieval-in-chromadb-vector-database/34438) - It seems like Chroma's vector database isn't initializing properly with many files, although no erro...
17. [Volumes | Docker Docs](https://docs.docker.com/reference/compose-file/volumes/) - Compose offers a neutral way for services to mount volumes, and configuration parameters to allocate...
