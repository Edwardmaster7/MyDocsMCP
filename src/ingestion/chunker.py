import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ParentChildChunker:
    def __init__(self, parent_chunk_size=1000, parent_overlap=0, child_chunk_size=200, child_overlap=50):
        # Usamos caracteres para estimar o tamanho dos chunks
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size, 
            chunk_overlap=parent_overlap
        )
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size, 
            chunk_overlap=child_overlap
        )

    def chunk(self, pages: list[dict]) -> tuple[list[dict], list[dict]]:
        parent_chunks = []
        child_chunks = []
        
        for page in pages:
            # Primeiro criamos os chunks maiores (contexto)
            parents = self.parent_splitter.split_text(page["text"])
            
            for p_text in parents:
                parent_id = str(uuid.uuid4())
                parent_chunks.append({
                    "id": parent_id,
                    "text": p_text,
                    "page": page["page"],
                    "filename": page["filename"]
                })
                
                # E então, dividimos esse parent em children menores (para busca precisa)
                children = self.child_splitter.split_text(p_text)
                for c_text in children:
                    child_chunks.append({
                        "id": str(uuid.uuid4()),
                        "parent_id": parent_id,
                        "text": c_text,
                        "page": page["page"],
                        "filename": page["filename"]
                    })
                    
        return parent_chunks, child_chunks