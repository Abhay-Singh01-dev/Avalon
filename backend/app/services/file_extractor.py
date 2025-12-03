import os
import fitz  # PyMuPDF
from docx import Document
from typing import Optional, List, Union
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class FileExtractor:
    """Extracts text from various document formats with robust error handling."""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain'
    }
    
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
    
    @classmethod
    def is_supported_file(cls, filename: str) -> bool:
        """Check if the file extension is supported."""
        ext = Path(filename).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS
    
    @classmethod
    async def validate_file(cls, file_path: str) -> None:
        """Validate file size and existence."""
        if not os.path.exists(file_path):
            raise ValueError("File does not exist")
            
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("File is empty")
        if file_size > cls.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds {cls.MAX_FILE_SIZE/1024/1024}MB limit")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
            
        # Remove null bytes and control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', text)
        
        # Normalize whitespace and clean up
        text = ' '.join(text.split())
        
        return text.strip()
    
    @classmethod
    async def extract_text(cls, file_path: str) -> str:
        """
        Extract text from a file based on its extension.
        
        Args:
            file_path: Path to the file to extract text from
            
        Returns:
            Extracted and cleaned text content
            
        Raises:
            ValueError: If file is not supported or extraction fails
        """
        await cls.validate_file(file_path)
        ext = Path(file_path).suffix.lower()
        
        try:
            if ext == '.pdf':
                return await cls._extract_pdf(file_path)
            elif ext == '.docx':
                return await cls._extract_docx(file_path)
            elif ext == '.txt':
                return await cls._extract_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from file: {str(e)}")
    
    @staticmethod
    async def _extract_pdf(file_path: str) -> str:
        """Extract text from PDF using PyMuPDF (fitz)."""
        try:
            text = []
            with fitz.open(file_path) as doc:
                for page in doc:
                    text.append(page.get_text())
            return FileExtractor.clean_text("\n".join(text))
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise ValueError("Invalid or corrupted PDF file")
    
    @staticmethod
    async def _extract_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            return FileExtractor.clean_text("\n".join([p.text for p in doc.paragraphs]))
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise ValueError("Invalid or corrupted DOCX file")
    
    @staticmethod
    async def _extract_txt(file_path: str) -> str:
        """Extract text from a plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return FileExtractor.clean_text(f.read())
        except Exception as e:
            logger.error(f"Text file extraction failed: {str(e)}")
            raise ValueError("Failed to read text file")
