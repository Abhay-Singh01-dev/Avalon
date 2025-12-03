"""
Text Chunking Service for Project RAG

Splits extracted text into manageable chunks for embedding.
Uses 300-400 token segments with configurable overlap.

IMPORTANT: This service is part of the RAG pipeline which is DISABLED by default.
RAG features require larger models (≥14B/70B) to work safely in healthcare context.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Splits text into chunks suitable for embedding and retrieval.
    
    Default configuration:
    - Chunk size: 350 tokens (~1400 characters)
    - Overlap: 50 tokens (~200 characters)
    """
    
    # Approximate characters per token (for English text)
    CHARS_PER_TOKEN = 4
    
    def __init__(
        self,
        chunk_size: int = 350,
        chunk_overlap: int = 50,
        project_files_dir: str = "project_files"
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            project_files_dir: Directory for storing chunk files
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.char_chunk_size = chunk_size * self.CHARS_PER_TOKEN
        self.char_overlap = chunk_overlap * self.CHARS_PER_TOKEN
        self.project_files_dir = Path(project_files_dir)
    
    def chunk_text(
        self,
        text: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Full text to chunk
            doc_id: Document ID for reference
            metadata: Optional document metadata
            
        Returns:
            List of chunk dictionaries with:
                - chunk_id: Unique chunk identifier
                - doc_id: Parent document ID
                - text: Chunk text content
                - start_char: Start position in original text
                - end_char: End position in original text
                - metadata: Additional metadata
        """
        if not text or not text.strip():
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Find the end of this chunk
            end = start + self.char_chunk_size
            
            # If we're not at the end, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence boundaries within the last 20% of the chunk
                search_start = start + int(self.char_chunk_size * 0.8)
                search_text = text[search_start:end]
                
                # Find last sentence boundary
                boundary = self._find_sentence_boundary(search_text)
                if boundary > 0:
                    end = search_start + boundary
            else:
                end = len(text)
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = {
                    "chunk_id": f"{doc_id}_chunk_{chunk_index}",
                    "doc_id": doc_id,
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "chunk_index": chunk_index,
                    "metadata": metadata or {}
                }
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position, accounting for overlap
            start = end - self.char_overlap
            
            # Ensure we make progress
            if start <= chunks[-1]["start_char"] if chunks else 0:
                start = end
        
        logger.info(f"Created {len(chunks)} chunks from document {doc_id}")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for chunking."""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove very long sequences of special characters
        text = re.sub(r'[_\-=]{10,}', ' ', text)
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text.strip()
    
    def _find_sentence_boundary(self, text: str) -> int:
        """
        Find the last sentence boundary in text.
        Returns position after the boundary, or 0 if not found.
        """
        # Look for sentence-ending punctuation followed by space or end
        patterns = [
            r'\.\s+',   # Period followed by space
            r'\?\s+',   # Question mark followed by space
            r'!\s+',    # Exclamation followed by space
            r'\n\n',    # Paragraph break
            r'\n',      # Line break
        ]
        
        last_boundary = 0
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                if match.end() > last_boundary:
                    last_boundary = match.end()
        
        return last_boundary
    
    def save_chunks(
        self,
        project_id: str,
        doc_id: str,
        chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Save chunks to a JSONL file for the project.
        
        Args:
            project_id: Project ID
            doc_id: Document ID
            chunks: List of chunk dictionaries
            
        Returns:
            Path to the saved chunks file
        """
        project_dir = self.project_files_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        chunks_file = project_dir / f"{doc_id}_chunks.jsonl"
        
        with open(chunks_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(chunks)} chunks to {chunks_file}")
        return str(chunks_file)
    
    def load_chunks(self, project_id: str, doc_id: str) -> List[Dict[str, Any]]:
        """
        Load chunks from a JSONL file.
        
        Args:
            project_id: Project ID
            doc_id: Document ID
            
        Returns:
            List of chunk dictionaries
        """
        chunks_file = self.project_files_dir / project_id / f"{doc_id}_chunks.jsonl"
        
        if not chunks_file.exists():
            return []
        
        chunks = []
        with open(chunks_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
        
        return chunks
    
    def get_all_project_chunks(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of all chunk dictionaries for the project
        """
        project_dir = self.project_files_dir / project_id
        
        if not project_dir.exists():
            return []
        
        all_chunks = []
        for chunks_file in project_dir.glob("*_chunks.jsonl"):
            with open(chunks_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        all_chunks.append(json.loads(line))
        
        return all_chunks
