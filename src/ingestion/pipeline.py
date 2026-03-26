import hashlib
import sqlite3
import os
from pathlib import Path
import chromadb
from src.ingestion.extractor import PDFExtractor
from src.ingestion.chunker import ParentChildChunker
from src.ingestion.embedder import LocalEmbedder

class IngestionPipeline:
    def __init__(self):
        self.pdf_dir = Path(os.environ.get("PDF_DIR", "./data/pdfs"))
        self.chroma_dir = os.environ.get("CHROMA_DIR", "./data/chroma_db")
        self.metadata_dir = Path(os.environ.get("METADATA_DIR", "./data/metadata"))
        
        # Ensure directories exist
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        Path(self.chroma_dir).mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.chroma = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.chroma.get_or_create_collection("fiap_pdfs")
        
        self.extractor = PDFExtractor()
        self.chunker = ParentChildChunker()
        self.embedder = LocalEmbedder()
        
        self._init_metadata_db()

    def _init_metadata_db(self):
        self.db_path = self.metadata_dir / "ingestion.db"
        self.conn = sqlite3.connect(str(self.db_path))
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS indexed_files (
                file_hash TEXT PRIMARY KEY,
                filepath TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def _file_hash(self, path: Path) -> str:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _already_indexed(self, fhash: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM indexed_files WHERE file_hash = ?', (fhash,))
        return cursor.fetchone() is not None

    def _register_indexed(self, path: Path, fhash: str):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO indexed_files (file_hash, filepath) VALUES (?, ?)', 
                      (fhash, str(path)))
        self.conn.commit()

    def ingest(self, base_path=None, force=False):
        root = Path(base_path) if base_path else self.pdf_dir
        new, skipped, errors = 0, 0, 0
        
        # We process files one by one to keep memory footprint low
        for pdf in root.rglob("*.pdf"):
            try:
                fhash = self._file_hash(pdf)
                # O nome da pasta imediatamente acima do PDF é tratado como 'disciplina'
                discipline = pdf.parent.name
                
                if not force and self._already_indexed(fhash):
                    skipped += 1
                    continue
                
                # Extract text
                pages = self.extractor.extract(pdf)
                if not pages:
                    print(f"Warning: No text extracted from {pdf.name}")
                    skipped += 1
                    continue

                # Chunk text
                parent_chunks, child_chunks = self.chunker.chunk(pages)
                
                # Se não houver chunks, pula o arquivo
                if not child_chunks:
                     skipped += 1
                     continue

                # Embed child chunks for semantic search
                texts_to_embed = [c["text"] for c in child_chunks]
                embeddings = self.embedder.embed(texts_to_embed)
                
                # Upsert to ChromaDB
                self._batch_upsert(child_chunks, embeddings, pdf, discipline, fhash)
                
                # Mark as indexed
                self._register_indexed(pdf, fhash)
                new += 1
                
            except Exception as e:
                errors += 1
                print(f"Error processing {pdf}: {e}", flush=True)
                
        return {"new": new, "skipped": skipped, "errors": errors}

    def _batch_upsert(self, chunks, embeddings, pdf: Path, discipline: str, fhash: str, batch_size=500):
        # We use child chunks as the main unit of retrieval
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_embs = embeddings[i:i+batch_size]
            
            # Formating ids: <file_hash>_<chunk_index>
            ids = [f"{fhash}_{j}" for j in range(i, i+len(batch_chunks))]
            documents = [c["text"] for c in batch_chunks]
            
            # The metadata carries the link back to the parent and the file info
            metadatas = [{
                "filename": pdf.name,
                "discipline": discipline,
                "page": c.get("page", 0),
                "doc_hash": fhash,
                "parent_id": c.get("parent_id", "")
            } for c in batch_chunks]
            
            self.collection.upsert(
                ids=ids,
                embeddings=batch_embs,
                documents=documents,
                metadatas=metadatas
            )