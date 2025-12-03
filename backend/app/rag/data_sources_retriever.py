"""
Data Source Retriever

Performs semantic search on embedded data source chunks.
Supports:
- Category-specific retrieval
- Source-specific retrieval  
- Automatic category detection from query
- Hybrid keyword + semantic search
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from app.config import settings
from app.db.mongo import get_database
from .data_sources_embedder import DataSourceEmbedder, HAS_SENTENCE_TRANSFORMERS
from .data_sources_ingest import CATEGORY_KEYWORDS

logger = logging.getLogger(__name__)


class DataSourceRetriever:
    """
    Retrieves relevant chunks from data sources using semantic search.
    """
    
    def __init__(self):
        self.embedder = DataSourceEmbedder()
        self.top_k = settings.DATA_SOURCE_TOP_K
        self.enabled = settings.DATA_SOURCE_RAG_ENABLED
        
    def detect_query_categories(self, query: str) -> List[str]:
        """
        Detect relevant categories from the query text.
        
        Args:
            query: User query text
            
        Returns:
            List of detected category names
        """
        query_lower = query.lower()
        detected = []
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if category not in detected:
                        detected.append(category)
                    break
        
        return detected
    
    def detect_source_restriction(self, query: str) -> Optional[str]:
        """
        Detect if user is requesting a specific data source.
        
        Patterns:
        - "use only my X data"
        - "from X data source"
        - "using X source"
        
        Args:
            query: User query text
            
        Returns:
            Source name if detected, None otherwise
        """
        patterns = [
            r"use only (?:my )?(.+?) data(?: source)?",
            r"from (?:my )?(.+?) data(?: source)?",
            r"using (?:my )?(.+?) source",
            r"in (?:my )?(.+?) data(?: source)?",
            r"from (.+?) source only",
        ]
        
        query_lower = query.lower()
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                source_name = match.group(1).strip()
                return source_name
        
        return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        source_id: Optional[str] = None,
        source_name: Optional[str] = None,
        top_k: Optional[int] = None,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using semantic search.
        
        Args:
            query: User query text
            category: Optional category filter
            source_id: Optional source ID filter
            source_name: Optional source name filter
            top_k: Number of results to return (default from settings)
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of relevant chunks with similarity scores
        """
        if not self.enabled:
            logger.debug("Data Source RAG is disabled")
            return []
        
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not available")
            return []
        
        top_k = top_k or self.top_k
        
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)
        
        if not query_embedding:
            return []
        
        # Build MongoDB filter
        db = get_database()
        collection = db.data_sources_embeddings
        
        filter_query = {}
        
        if category:
            filter_query["category"] = category.lower().replace(" ", "_")
        
        if source_id:
            filter_query["source_id"] = source_id
        
        if source_name:
            # Case-insensitive source name match
            filter_query["source_name"] = {"$regex": f"^{re.escape(source_name)}$", "$options": "i"}
        
        # Fetch all matching chunks (we'll sort by similarity in Python)
        # For production, consider using MongoDB Atlas Vector Search
        chunks = []
        async for doc in collection.find(filter_query):
            if doc.get("embedding"):
                similarity = self.cosine_similarity(query_embedding, doc["embedding"])
                if similarity >= min_similarity:
                    chunks.append({
                        "chunk_id": doc["_id"],
                        "text": doc["text"],
                        "source_id": doc["source_id"],
                        "source_name": doc["source_name"],
                        "category": doc["category"],
                        "file_id": doc["file_id"],
                        "similarity": float(similarity),
                        "metadata": doc.get("metadata", {})
                    })
        
        # Sort by similarity and return top_k
        chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return chunks[:top_k]
    
    async def retrieve_with_auto_detection(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve chunks with automatic category and source detection.
        
        Args:
            query: User query text
            top_k: Number of results to return
            
        Returns:
            Dict with chunks, detected categories, and source restrictions
        """
        if not self.enabled:
            return {
                "chunks": [],
                "categories": [],
                "source_restriction": None,
                "rag_enabled": False
            }
        
        # Detect source restriction
        source_restriction = self.detect_source_restriction(query)
        
        # Detect categories from query
        detected_categories = self.detect_query_categories(query)
        
        chunks = []
        
        if source_restriction:
            # User wants specific source only
            chunks = await self.retrieve(
                query=query,
                source_name=source_restriction,
                top_k=top_k
            )
        elif detected_categories:
            # Retrieve from detected categories
            for category in detected_categories:
                category_chunks = await self.retrieve(
                    query=query,
                    category=category,
                    top_k=top_k
                )
                chunks.extend(category_chunks)
            
            # Re-sort and limit
            chunks.sort(key=lambda x: x["similarity"], reverse=True)
            chunks = chunks[:top_k or self.top_k]
        else:
            # General retrieval across all sources
            chunks = await self.retrieve(query=query, top_k=top_k)
        
        return {
            "chunks": chunks,
            "categories": detected_categories,
            "source_restriction": source_restriction,
            "rag_enabled": True
        }
    
    def format_chunks_for_prompt(
        self,
        chunks: List[Dict[str, Any]],
        max_chars: int = 3000
    ) -> str:
        """
        Format retrieved chunks for inclusion in LLM prompt.
        Optimized for Mistral 7B - uses bullet points and compressed format.
        
        Args:
            chunks: List of retrieved chunks
            max_chars: Maximum characters to include
            
        Returns:
            Formatted string for prompt injection
        """
        if not chunks:
            return ""
        
        lines = ["DATA SOURCE EXTRACT:"]
        current_chars = len(lines[0])
        
        # Group by source for cleaner formatting
        by_source = {}
        for chunk in chunks:
            source = chunk["source_name"]
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(chunk)
        
        for source_name, source_chunks in by_source.items():
            source_header = f"\n[Source: {source_name}]"
            
            if current_chars + len(source_header) > max_chars:
                break
            
            lines.append(source_header)
            current_chars += len(source_header)
            
            for chunk in source_chunks:
                # Compress chunk text
                text = chunk["text"][:500] if len(chunk["text"]) > 500 else chunk["text"]
                text = text.replace("\n", " ").strip()
                
                bullet = f"- {text}"
                
                if current_chars + len(bullet) > max_chars:
                    lines.append("- [Additional data truncated for context window]")
                    break
                
                lines.append(bullet)
                current_chars += len(bullet) + 1
        
        return "\n".join(lines)
    
    def format_source_indicator(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Create a user-facing indicator of which data sources were used.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            Formatted indicator string
        """
        if not chunks:
            return ""
        
        sources = set(chunk["source_name"] for chunk in chunks)
        categories = set(chunk["category"] for chunk in chunks)
        
        source_list = ", ".join(sorted(sources))
        
        return f"📄 Using uploaded data source: {source_list}"
    
    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        source_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Public search API for data sources.
        
        Args:
            query: Search query
            category: Optional category filter
            source_id: Optional source filter
            top_k: Number of results
            
        Returns:
            List of matching chunks with metadata
        """
        return await self.retrieve(
            query=query,
            category=category,
            source_id=source_id,
            top_k=top_k,
            min_similarity=0.2  # Lower threshold for search
        )
    
    async def get_sources_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all data sources with their file counts.
        
        Returns:
            List of source summaries
        """
        db = get_database()
        
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "source_id": "$source_id",
                        "source_name": "$source_name"
                    },
                    "chunk_count": {"$sum": 1},
                    "categories": {"$addToSet": "$category"},
                    "last_updated": {"$max": "$updated_at"}
                }
            },
            {"$sort": {"_id.source_name": 1}}
        ]
        
        sources = []
        async for doc in db.data_sources_embeddings.aggregate(pipeline):
            sources.append({
                "source_id": doc["_id"]["source_id"],
                "source_name": doc["_id"]["source_name"],
                "chunk_count": doc["chunk_count"],
                "categories": doc["categories"],
                "last_updated": doc["last_updated"].isoformat() if doc["last_updated"] else None
            })
        
        return sources
    
    async def get_source_files(self, source_id: str) -> List[Dict[str, Any]]:
        """
        Get files for a specific data source.
        
        Args:
            source_id: Data source ID
            
        Returns:
            List of file metadata
        """
        db = get_database()
        
        files = []
        async for doc in db.data_sources_files.find({"source_id": source_id}):
            files.append({
                "file_id": doc["_id"],
                "file_name": doc["file_name"],
                "category": doc["category"],
                "chunk_count": doc["chunk_count"],
                "indexed": doc.get("indexed", True),
                "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
                "metadata": doc.get("metadata", {})
            })
        
        return files


# Singleton instance
data_source_retriever = DataSourceRetriever()


def get_rag_context_for_query(query: str) -> Tuple[str, str, bool]:
    """
    Synchronous wrapper for getting RAG context.
    Used by chat pipeline.
    
    Returns:
        Tuple of (context_text, source_indicator, was_used)
    """
    import asyncio
    
    if not settings.DATA_SOURCE_RAG_ENABLED:
        return "", "", False
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        data_source_retriever.retrieve_with_auto_detection(query)
    )
    
    if not result["chunks"]:
        return "", "", False
    
    context = data_source_retriever.format_chunks_for_prompt(result["chunks"])
    indicator = data_source_retriever.format_source_indicator(result["chunks"])
    
    return context, indicator, True
