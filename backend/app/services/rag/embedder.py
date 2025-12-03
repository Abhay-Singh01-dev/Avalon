"""
Embedding Service for Project RAG

Generates embeddings for text chunks using LM Studio's embedding endpoint.
Stores embeddings in MongoDB for efficient retrieval.

IMPORTANT: This service is part of the RAG pipeline which is DISABLED by default.
RAG features require larger models (≥14B/70B) to work safely in healthcare context.
"""

import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """
    Generates and stores embeddings for document chunks.
    Uses LM Studio's OpenAI-compatible embedding endpoint.
    """
    
    EMBEDDINGS_COLLECTION = "project_embeddings"
    
    def __init__(
        self,
        embedding_url: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """
        Initialize the embedder.
        
        Args:
            embedding_url: LM Studio embedding endpoint URL
            embedding_model: Embedding model name
        """
        self.embedding_url = embedding_url or settings.LMSTUDIO_EMBEDDING_URL
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL
        self._db = None
    
    def _get_db(self):
        """Lazy load database connection."""
        if self._db is None:
            from app.db.mongo import get_database
            self._db = get_database()
        return self._db
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats, or None if failed
        """
        if not text or not text.strip():
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.embedding_url,
                    json={
                        "model": self.embedding_model,
                        "input": text
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Embedding API error: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                
                # OpenAI-compatible format
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["embedding"]
                
                logger.error(f"Unexpected embedding response format: {data}")
                return None
                
        except httpx.ConnectError:
            logger.error(f"Could not connect to embedding service at {self.embedding_url}")
            return None
        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            return None
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to embed at once
            
        Returns:
            List of embedding vectors (None for failed embeddings)
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        self.embedding_url,
                        json={
                            "model": self.embedding_model,
                            "input": batch
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Batch embedding error: {response.status_code}")
                        embeddings.extend([None] * len(batch))
                        continue
                    
                    data = response.json()
                    
                    if "data" in data:
                        # Sort by index to ensure correct order
                        sorted_data = sorted(data["data"], key=lambda x: x.get("index", 0))
                        for item in sorted_data:
                            embeddings.append(item.get("embedding"))
                    else:
                        embeddings.extend([None] * len(batch))
                        
            except Exception as e:
                logger.error(f"Batch embedding error: {str(e)}")
                embeddings.extend([None] * len(batch))
        
        return embeddings
    
    async def embed_and_store_chunks(
        self,
        project_id: str,
        doc_id: str,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate embeddings for chunks and store in MongoDB.
        
        Args:
            project_id: Project ID
            doc_id: Document ID
            chunks: List of chunk dictionaries
            
        Returns:
            Result dictionary with success status and counts
        """
        if not chunks:
            return {
                "success": True,
                "embedded_count": 0,
                "failed_count": 0,
                "message": "No chunks to embed"
            }
        
        db = self._get_db()
        collection = db[self.EMBEDDINGS_COLLECTION]
        
        # Delete existing embeddings for this document
        await collection.delete_many({
            "project_id": project_id,
            "doc_id": doc_id
        })
        
        # Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.generate_embeddings_batch(texts)
        
        # Store embeddings
        embedded_count = 0
        failed_count = 0
        
        for chunk, embedding in zip(chunks, embeddings):
            if embedding is None:
                failed_count += 1
                continue
            
            embedding_doc = {
                "project_id": project_id,
                "doc_id": doc_id,
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "embedding": embedding,
                "chunk_index": chunk.get("chunk_index", 0),
                "metadata": chunk.get("metadata", {}),
                "created_at": datetime.utcnow()
            }
            
            try:
                await collection.insert_one(embedding_doc)
                embedded_count += 1
            except Exception as e:
                logger.error(f"Failed to store embedding: {str(e)}")
                failed_count += 1
        
        logger.info(f"Embedded {embedded_count} chunks for doc {doc_id}, {failed_count} failed")
        
        return {
            "success": failed_count == 0,
            "embedded_count": embedded_count,
            "failed_count": failed_count,
            "message": f"Embedded {embedded_count} chunks" if failed_count == 0 
                       else f"Embedded {embedded_count} chunks, {failed_count} failed"
        }
    
    async def get_project_embedding_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Get embedding statistics for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Statistics dictionary
        """
        db = self._get_db()
        collection = db[self.EMBEDDINGS_COLLECTION]
        
        # Count total embeddings
        total_count = await collection.count_documents({"project_id": project_id})
        
        # Get unique document count
        pipeline = [
            {"$match": {"project_id": project_id}},
            {"$group": {"_id": "$doc_id"}},
            {"$count": "doc_count"}
        ]
        result = await collection.aggregate(pipeline).to_list(1)
        doc_count = result[0]["doc_count"] if result else 0
        
        return {
            "project_id": project_id,
            "total_embeddings": total_count,
            "document_count": doc_count,
            "embedding_model": self.embedding_model
        }
    
    async def delete_document_embeddings(self, project_id: str, doc_id: str) -> int:
        """
        Delete all embeddings for a document.
        
        Args:
            project_id: Project ID
            doc_id: Document ID
            
        Returns:
            Number of deleted embeddings
        """
        db = self._get_db()
        collection = db[self.EMBEDDINGS_COLLECTION]
        
        result = await collection.delete_many({
            "project_id": project_id,
            "doc_id": doc_id
        })
        
        return result.deleted_count
    
    async def delete_project_embeddings(self, project_id: str) -> int:
        """
        Delete all embeddings for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Number of deleted embeddings
        """
        db = self._get_db()
        collection = db[self.EMBEDDINGS_COLLECTION]
        
        result = await collection.delete_many({"project_id": project_id})
        
        return result.deleted_count
