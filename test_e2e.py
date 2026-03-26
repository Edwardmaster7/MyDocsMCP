import asyncio
from src.ingestion.pipeline import IngestionPipeline
from src.retrieval.searcher import SemanticSearcher

async def run_e2e():
    print("\n--- INICIANDO INGESTÃO DOS PDFs ---")
    pipeline = IngestionPipeline()
    result = pipeline.ingest()
    print(f"Resultado Ingestão: {result['new']} novos PDFs indexados, {result['skipped']} ignorados, {result['errors']} erros.")

    print("\n--- TESTANDO A BUSCA (RAG) ---")
    searcher = SemanticSearcher()
    
    stats = await searcher.get_stats()
    print(f"\n{stats}")
    
    print("\n--- LISTAGEM DE DOCUMENTOS ---")
    docs = await searcher.list_documents()
    print(docs)
    
    print("\n--- CONSULTA SEMÂNTICA 1: 'Como criar uma API com Flask' ---")
    query1 = "Como criar uma API com Flask?"
    res1 = await searcher.search(query1, top_k=2)
    print(f"Resultados:\n{searcher.format_results(res1)}")
    
    print("\n--- CONSULTA SEMÂNTICA 2: 'Qual a diferença entre regressão linear e logística' ---")
    query2 = "Qual a diferença entre regressão linear e regressão logística?"
    res2 = await searcher.search(query2, top_k=2)
    print(f"Resultados:\n{searcher.format_results(res2)}")

if __name__ == "__main__":
    # Suprime os avisos do huggingface token
    import warnings
    warnings.filterwarnings("ignore")
    asyncio.run(run_e2e())
