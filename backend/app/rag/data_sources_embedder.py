"""
Data Source Embedder

Generates vector embeddings for data source chunks using sentence-transformers.
Uses all-MiniLM-L6-v2 model which runs efficiently on CPU.

Stores embeddings and metadata in MongoDB for retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from app.config import settings
from app.db.mongo import get_database

logger = logging.getLogger(__name__)

# Try to import sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed. Run: pip install sentence-transformers")


class DataSourceEmbedder:
    """
    Generates embeddings for data source chunks using sentence-transformers.
    Stores embeddings in MongoDB for efficient retrieval.
    """
    
    _model = None  # Class-level model for lazy loading
    
    def __init__(self):
        self.model_name = settings.SENTENCE_TRANSFORMER_MODEL
        self.enabled = settings.DATA_SOURCE_RAG_ENABLED
        
    @classmethod
    def get_model(cls):
        """Lazy load the sentence transformer model."""
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
        
        if cls._model is None:
            logger.info(f"Loading sentence-transformer model: {settings.SENTENCE_TRANSFORMER_MODEL}")
            cls._model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
            logger.info("Sentence-transformer model loaded successfully")
        
        return cls._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not available, returning empty embedding")
            return []
        
        model = self.get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not available, returning empty embeddings")
            return [[] for _ in texts]
        
        if not texts:
            return []
        
        model = self.get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return [emb.tolist() for emb in embeddings]
    
    async def store_chunk_with_embedding(
        self,
        chunk: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Store a chunk with its embedding in MongoDB.
        
        Args:
            chunk: Chunk dictionary with text and metadata
            embedding: Pre-computed embedding (generated if not provided)
            
        Returns:
            Stored document with ID
        """
        if embedding is None:
            embedding = self.generate_embedding(chunk["text"])
        
        db = get_database()
        collection = db.data_sources_embeddings
        
        document = {
            "_id": chunk["chunk_id"],
            "text": chunk["text"],
            "embedding": embedding,
            "source_id": chunk["source_id"],
            "source_name": chunk["source_name"],
            "category": chunk["category"],
            "file_id": chunk["file_id"],
            "upload_date": chunk["upload_date"],
            "chunk_index": chunk["chunk_index"],
            "metadata": chunk.get("metadata", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Upsert to handle re-indexing
        await collection.replace_one(
            {"_id": chunk["chunk_id"]},
            document,
            upsert=True
        )
        
        return document
    
    async def store_chunks_batch(
        self,
        chunks: List[Dict[str, Any]],
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Store multiple chunks with embeddings in batch.
        
        Args:
            chunks: List of chunk dictionaries
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            Summary of stored chunks
        """
        if not chunks:
            return {"stored": 0, "errors": 0}
        
        # Generate embeddings in batch for efficiency
        if generate_embeddings:
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.generate_embeddings_batch(texts)
        else:
            embeddings = [[] for _ in chunks]
        
        db = get_database()
        collection = db.data_sources_embeddings
        
        stored = 0
        errors = 0
        
        for chunk, embedding in zip(chunks, embeddings):
            try:
                document = {
                    "_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "embedding": embedding,
                    "source_id": chunk["source_id"],
                    "source_name": chunk["source_name"],
                    "category": chunk["category"],
                    "file_id": chunk["file_id"],
                    "upload_date": chunk["upload_date"],
                    "chunk_index": chunk["chunk_index"],
                    "metadata": chunk.get("metadata", {}),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                await collection.replace_one(
                    {"_id": chunk["chunk_id"]},
                    document,
                    upsert=True
                )
                stored += 1
                
            except Exception as e:
                logger.error(f"Error storing chunk {chunk.get('chunk_id')}: {str(e)}")
                errors += 1
        
        logger.info(f"Stored {stored} chunks, {errors} errors")
        return {"stored": stored, "errors": errors}
    
    async def store_file_metadata(
        self,
        file_id: str,
        source_id: str,
        source_name: str,
        category: str,
        file_name: str,
        file_path: str,
        chunk_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store file metadata in MongoDB.
        
        Args:
            file_id: Unique file identifier
            source_id: Data source ID
            source_name: Data source name
            category: Detected or assigned category
            file_name: Original file name
            file_path: Path to stored file
            chunk_count: Number of chunks created
            metadata: Additional file metadata
            
        Returns:
            Stored file document
        """
        db = get_database()
        collection = db.data_sources_files
        
        document = {
            "_id": file_id,
            "source_id": source_id,
            "source_name": source_name,
            "category": category,
            "file_name": file_name,
            "file_path": file_path,
            "chunk_count": chunk_count,
            "metadata": metadata or {},
            "indexed": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await collection.replace_one(
            {"_id": file_id},
            document,
            upsert=True
        )
        
        return document
    
    async def delete_file_embeddings(self, file_id: str) -> int:
        """
        Delete all embeddings for a specific file.
        
        Args:
            file_id: The file ID to delete embeddings for
            
        Returns:
            Number of deleted embeddings
        """
        db = get_database()
        
        # Delete embeddings
        result = await db.data_sources_embeddings.delete_many({"file_id": file_id})
        
        # Delete file metadata
        await db.data_sources_files.delete_one({"_id": file_id})
        
        logger.info(f"Deleted {result.deleted_count} embeddings for file {file_id}")
        return result.deleted_count
    
    async def delete_source_embeddings(self, source_id: str) -> int:
        """
        Delete all embeddings for a specific data source.
        
        Args:
            source_id: The source ID to delete embeddings for
            
        Returns:
            Number of deleted embeddings
        """
        db = get_database()
        
        # Delete embeddings
        result = await db.data_sources_embeddings.delete_many({"source_id": source_id})
        
        # Delete file metadata
        await db.data_sources_files.delete_many({"source_id": source_id})
        
        logger.info(f"Deleted {result.deleted_count} embeddings for source {source_id}")
        return result.deleted_count
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the embedding index.
        
        Returns:
            Dict with index statistics
        """
        db = get_database()
        
        total_chunks = await db.data_sources_embeddings.count_documents({})
        total_files = await db.data_sources_files.count_documents({})
        
        # Get category breakdown
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        categories = {}
        async for doc in db.data_sources_embeddings.aggregate(pipeline):
            categories[doc["_id"]] = doc["count"]
        
        # Get source breakdown
        source_pipeline = [
            {"$group": {"_id": "$source_name", "count": {"$sum": 1}}}
        ]
        sources = {}
        async for doc in db.data_sources_embeddings.aggregate(source_pipeline):
            sources[doc["_id"]] = doc["count"]
        
        # Get last updated
        last_doc = await db.data_sources_embeddings.find_one(
            {},
            sort=[("updated_at", -1)]
        )
        last_updated = last_doc["updated_at"].isoformat() if last_doc else None
        
        return {
            "total_chunks": total_chunks,
            "total_files": total_files,
            "categories": categories,
            "sources": sources,
            "last_updated": last_updated,
            "model": self.model_name,
            "enabled": self.enabled
        }


# Singleton instance
data_source_embedder = DataSourceEmbedder()
