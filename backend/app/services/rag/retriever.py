"""
Retrieval Service for Project RAG

Retrieves relevant chunks from project documents based on query similarity.
Uses cosine similarity for vector search.

⚠️ IMPORTANT: This service is DISABLED by default via ENABLE_PROJECT_RAG flag.
RAG features require larger models (≥14B/70B) to work safely in healthcare context.

When ENABLE_PROJECT_RAG is False:
- retrieve_project_chunks() returns empty list
- No RAG context is added to prompts
- Existing agents work normally without RAG

To enable RAG:
1. Install a larger model (≥14B parameters)
2. Set ENABLE_PROJECT_RAG=true in .env
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class ProjectRetriever:
    """
    Retrieves relevant document chunks for a query within a project.
    
    SAFETY: All retrieval is gated by ENABLE_PROJECT_RAG feature flag.
    When disabled, returns empty results to prevent hallucinations
    from random documents in healthcare context.
    """
    
    EMBEDDINGS_COLLECTION = "project_embeddings"
    
    def __init__(self, top_k: Optional[int] = None):
        """
        Initialize the retriever.
        
        Args:
            top_k: Number of top chunks to retrieve (default from settings)
        """
        self.top_k = top_k or settings.RAG_TOP_K
        self._db = None
        self._embedder = None
    
    def _get_db(self):
        """Lazy load database connection."""
        if self._db is None:
            from app.db.mongo import get_database
            self._db = get_database()
        return self._db
    
    def _get_embedder(self):
        """Lazy load embedder."""
        if self._embedder is None:
            from app.services.rag.embedder import Embedder
            self._embedder = Embedder()
        return self._embedder
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    async def retrieve_project_chunks(
        self,
        project_id: str,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query from project documents.
        
        ⚠️ FEATURE FLAG CHECK:
        If ENABLE_PROJECT_RAG is False, returns empty list immediately.
        This is a safety measure to prevent hallucinations from RAG
        when using smaller models that cannot handle context well.
        
        Args:
            project_id: Project ID to search within
            query: User query to find relevant chunks for
            top_k: Number of top results to return (default: self.top_k)
            
        Returns:
            List of relevant chunks with similarity scores.
            Empty list if RAG is disabled or no matches found.
        """
        # ⚠️ FEATURE FLAG CHECK - DO NOT REMOVE
        if not settings.ENABLE_PROJECT_RAG:
            logger.debug(
                f"RAG retrieval skipped for project {project_id}: "
                "ENABLE_PROJECT_RAG is False"
            )
            return []
        
        if not project_id or not query:
            return []
        
        k = top_k or self.top_k
        
        try:
            # Generate query embedding
            embedder = self._get_embedder()
            query_embedding = await embedder.generate_embedding(query)
            
            if query_embedding is None:
                logger.warning(f"Failed to generate query embedding for: {query[:50]}...")
                return []
            
            # Retrieve all embeddings for the project
            db = self._get_db()
            collection = db[self.EMBEDDINGS_COLLECTION]
            
            cursor = collection.find({"project_id": project_id})
            
            # Calculate similarities
            scored_chunks = []
            async for doc in cursor:
                if "embedding" not in doc:
                    continue
                
                similarity = self.cosine_similarity(query_embedding, doc["embedding"])
                
                scored_chunks.append({
                    "chunk_id": doc.get("chunk_id"),
                    "doc_id": doc.get("doc_id"),
                    "text": doc.get("text", ""),
                    "similarity": similarity,
                    "chunk_index": doc.get("chunk_index", 0),
                    "metadata": doc.get("metadata", {})
                })
            
            # Sort by similarity and take top k
            scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            top_chunks = scored_chunks[:k]
            
            # Filter out low similarity results (threshold: 0.5)
            filtered_chunks = [c for c in top_chunks if c["similarity"] >= 0.5]
            
            logger.info(
                f"Retrieved {len(filtered_chunks)} chunks for query in project {project_id}"
            )
            
            return filtered_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}")
            return []
    
    async def retrieve_with_context(
        self,
        project_id: str,
        query: str,
        top_k: Optional[int] = None,
        include_source_info: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve chunks and format as context for LLM prompt.
        
        Args:
            project_id: Project ID
            query: User query
            top_k: Number of results
            include_source_info: Include source document info
            
        Returns:
            Dictionary with:
                - context_text: Formatted context string for prompt
                - chunks: Raw chunk data
                - rag_enabled: Whether RAG is active
        """
        # Check feature flag
        if not settings.ENABLE_PROJECT_RAG:
            return {
                "context_text": "",
                "chunks": [],
                "rag_enabled": False,
                "message": "Project RAG is disabled. Requires larger model (≥14B)."
            }
        
        chunks = await self.retrieve_project_chunks(project_id, query, top_k)
        
        if not chunks:
            return {
                "context_text": "",
                "chunks": [],
                "rag_enabled": True,
                "message": "No relevant project documents found."
            }
        
        # Format context for prompt
        context_parts = ["PROJECT_CONTEXT (from uploaded documents):"]
        
        for i, chunk in enumerate(chunks, 1):
            if include_source_info:
                context_parts.append(
                    f"\n[Document {i}] (similarity: {chunk['similarity']:.2f}):\n"
                    f"{chunk['text']}"
                )
            else:
                context_parts.append(f"\n{chunk['text']}")
        
        context_text = "\n".join(context_parts)
        
        return {
            "context_text": context_text,
            "chunks": chunks,
            "rag_enabled": True,
            "message": f"Retrieved {len(chunks)} relevant document chunks."
        }
    
    async def check_project_has_documents(self, project_id: str) -> Dict[str, Any]:
        """
        Check if a project has indexed documents.
        
        Args:
            project_id: Project ID
            
        Returns:
            Status dictionary
        """
        db = self._get_db()
        collection = db[self.EMBEDDINGS_COLLECTION]
        
        count = await collection.count_documents({"project_id": project_id})
        
        return {
            "project_id": project_id,
            "has_documents": count > 0,
            "embedding_count": count,
            "rag_enabled": settings.ENABLE_PROJECT_RAG
        }


def get_rag_status() -> Dict[str, Any]:
    """
    Get current RAG system status including all feature flags.
    
    Returns:
        Dictionary with feature flag status and explanations
    """
    return {
        "project_rag": {
            "enabled": settings.ENABLE_PROJECT_RAG,
            "description": "Project-level document RAG retrieval",
            "requirement": "Requires ≥14B parameter model"
        },
        "link_fetch": {
            "enabled": settings.ENABLE_LINK_FETCH,
            "description": "Fetch and index linked web content",
            "requirement": "Requires ≥14B parameter model"
        },
        "web_scraping": {
            "enabled": settings.ENABLE_WEB_SCRAPING,
            "description": "General web scraping capabilities",
            "requirement": "Requires ≥14B parameter model"
        },
        "current_model": settings.LMSTUDIO_MODEL_NAME,
        "safe_for_healthcare": not settings.ENABLE_PROJECT_RAG,
        "message": (
            "RAG features are disabled for safety. "
            "Current model (Mistral 7B) cannot safely handle RAG context. "
            "Enable after installing larger models (≥14B/70B)."
        ) if not settings.ENABLE_PROJECT_RAG else "RAG features are enabled."
    }
