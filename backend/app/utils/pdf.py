from typing import IO, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def extract_text_from_pdf(file: IO[bytes]) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file: File-like object containing PDF data
        
    Returns:
        Extracted text from the PDF
    """
    try:
        # Using PyMuPDF (fitz) for better performance and accuracy
        import fitz  # PyMuPDF
        
        text = ""
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()
    except ImportError:
        logger.warning("PyMuPDF not installed. Falling back to slower PyPDF2.")
        from PyPDF2 import PdfReader
        
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Could not extract text from PDF: {e}")

async def get_pdf_metadata(file: IO[bytes]) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file.
    
    Args:
        file: File-like object containing PDF data
        
    Returns:
        Dictionary containing PDF metadata
    """
    try:
        import fitz  # PyMuPDF
        
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            metadata = doc.metadata
            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creation_date"),
                "modification_date": metadata.get("mod_date"),
                "page_count": len(doc),
            }
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {e}")
        return {}
