from pathlib import Path
import fitz  # PyMuPDF

class PDFExtractor:
    def extract(self, file_path: Path) -> list[dict]:
        """
        Extrai o texto e metadados básicos de cada página de um PDF.
        """
        pages_data = []
        doc = fitz.open(file_path)
        
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            
            # Se a página tiver texto útil, guardamos com os metadados
            if text:
                pages_data.append({
                    "text": text,
                    "page": i + 1,  # human readable index
                    "filename": file_path.name
                })
                
        doc.close()
        return pages_data