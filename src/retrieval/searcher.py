import os
import chromadb
from src.ingestion.embedder import LocalEmbedder
from src.config import CHROMA_DIR, log_stderr

class SemanticSearcher:
    def __init__(self):
        self.chroma_dir = str(CHROMA_DIR)
        
        try:
            self.chroma = chromadb.PersistentClient(path=self.chroma_dir)
            self.collection = self.chroma.get_or_create_collection("fiap_pdfs")
        except Exception as e:
            log_stderr(f"Warning: Could not initialize ChromaDB at {self.chroma_dir}: {e}")
            self.collection = None
            
        self.embedder = LocalEmbedder()

    async def search(self, query: str, top_k: int = 5, filter_discipline: str = None) -> list[dict]:
        if not self.collection:
            return [{"text": "Error: Database not initialized", "metadata": {}}]

        try:
            query_embedding = self.embedder.embed([query])[0]
            
            where_clause = None
            if filter_discipline:
                where_clause = {"discipline": filter_discipline}
                
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause
            )
            
            formatted_results = []
            if results and results['documents'] and results['documents'][0]:
                for doc, meta, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
                    formatted_results.append({
                        "text": doc,
                        "metadata": meta,
                        "score": 1 - distance # Approx similarity from distance
                    })
            return formatted_results
            
        except Exception as e:
            return [{"text": f"Error during search: {e}", "metadata": {}}]

    def format_results(self, results: list[dict]) -> str:
        if not results:
            return "No documents found matching the query."
            
        formatted = []
        for i, res in enumerate(results):
            meta = res.get('metadata', {})
            filename = meta.get('filename', 'Unknown File')
            page = meta.get('page', '?')
            discipline = meta.get('discipline', 'Unknown Discipline')
            
            # Use parent_text if available for larger context, fallback to child text
            text = meta.get('parent_text')
            if not text:
                text = res.get('text', '')
            
            formatted.append(f"--- Result {i+1} ---\nFile: {filename} (Page {page}) - Discipline: {discipline}\nContent:\n{text}\n")
            
        return "\n".join(formatted)

    async def list_documents(self, discipline: str = None) -> str:
        if not self.collection:
             return "Database not initialized"
             
        where_clause = {"discipline": discipline} if discipline else None
        
        # We fetch all unique filenames. To do this efficiently we just need the metadatas.
        # Note: A real implementation might use the sqlite db for this, as it's faster.
        # For simplicity, we query a subset of Chroma DB.
        try:
             results = self.collection.get(where=where_clause, include=["metadatas"])
             if not results or not results['metadatas']:
                 return "No documents indexed yet."
                 
             unique_docs = set()
             for meta in results['metadatas']:
                  if meta and 'filename' in meta:
                       unique_docs.add(f"{meta.get('discipline', '?')}/{meta['filename']}")
                       
             if not unique_docs:
                 return "No documents found."
                 
             return "Indexed Documents:\n" + "\n".join(sorted(unique_docs))
             
        except Exception as e:
            return f"Error listing documents: {e}"

    async def cross_search(self, query: str, disciplines: list[str], top_k_per_discipline: int = 3) -> str:
        if not self.collection:
             return "Database not initialized"
             
        results_str = []
        for disc in disciplines:
             results_str.append(f"=== Results for {disc} ===")
             res = await self.search(query, top_k=top_k_per_discipline, filter_discipline=disc)
             results_str.append(self.format_results(res))
             
        return "\n".join(results_str)

    async def get_stats(self) -> str:
        if not self.collection:
             return "Database not initialized"
        count = self.collection.count()
        return f"Index Statistics:\nTotal Chunks Indexed: {count}"