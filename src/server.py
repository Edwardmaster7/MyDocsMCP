from fastmcp import FastMCP
from src.retrieval.searcher import SemanticSearcher
from src.ingestion.pipeline import IngestionPipeline
from src.watcher import start_watcher
from src.config import log_stderr
import asyncio
import os

mcp = FastMCP("MyDocs MCP")

searcher = SemanticSearcher()
pipeline = IngestionPipeline()

@mcp.tool()
async def search_documents(query: str, top_k: int = 5, discipline: str = None) -> str:
    """
    Busca semanticamente no acervo de PDFs.
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
    # Se rodar via MCP context, não podemos bloquear o thread assíncrono muito tempo, 
    # mas para esse caso, rodamos de forma síncrona/blocking no FastMCP thread pool
    result = pipeline.ingest(base_path=path, force=force_reindex)
    return f"Ingestão concluída: {result['new']} novos, {result['skipped']} ignorados, {result['errors']} erros."


# --- Lifespan and server execution ---
# Currently FastMCP has some differences in its lifecycle management
# For Python > 3.11 we just run the app context. If we want a background task,
# it's usually better to manage it outside if FastMCP doesn't expose lifespan hooks directly.
# However we'll assume a standard async setup for the server.

def main():
    import threading
    
    # We run the ingestion initially
    log_stderr("Running initial ingestion...")
    pipeline.ingest()
    
    # Run watcher in a separate thread so FastMCP event loop isn't blocked
    def run_watcher():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_watcher(pipeline))
        finally:
             loop.close()
            
    t = threading.Thread(target=run_watcher, daemon=True)
    t.start()
    
    # Run the server
    log_stderr("Starting MCP server...")
    mcp.run()

if __name__ == "__main__":
    main()