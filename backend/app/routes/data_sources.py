"""
Data Sources API Routes

Provides endpoints for:
- Uploading files to data sources
- Listing data sources and files
- Searching indexed content
- Managing and rebuilding indexes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import os
import uuid
import shutil
import logging

from app.config import settings
from app.db.mongo import get_database
from app.rag.data_sources_ingest import data_source_ingester
from app.rag.data_sources_embedder import data_source_embedder
from app.rag.data_sources_retriever import data_source_retriever

router = APIRouter(prefix="/api/data_sources", tags=["data_sources"])
logger = logging.getLogger(__name__)

# Ensure data sources directory exists
DATA_SOURCES_DIR = Path(settings.DATA_SOURCES_DIR)
DATA_SOURCES_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md', '.csv', '.json'}


@router.get("/status")
async def get_rag_status():
    """
    Get Data Source RAG status and statistics.
    """
    try:
        stats = await data_source_embedder.get_index_stats()
        
        return {
            "status": "success",
            "rag_enabled": settings.DATA_SOURCE_RAG_ENABLED,
            "model": settings.SENTENCE_TRANSFORMER_MODEL,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting RAG status: {str(e)}")
        return {
            "status": "success",
            "rag_enabled": settings.DATA_SOURCE_RAG_ENABLED,
            "model": settings.SENTENCE_TRANSFORMER_MODEL,
            "stats": {
                "total_chunks": 0,
                "total_files": 0,
                "categories": {},
                "sources": {},
                "last_updated": None
            }
        }


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    source_id: str = Form(...),
    source_name: str = Form(...),
    category: Optional[str] = Form(None)
):
    """
    Upload a file to a data source and index it.
    
    Args:
        file: The file to upload
        source_id: ID of the data source (e.g., "oncology", "diabetes")
        source_name: Display name of the data source
        category: Optional category override (auto-detected if not provided)
    """
    try:
        # Validate file extension
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        
        # Create source directory
        source_dir = DATA_SOURCES_DIR / source_id
        source_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = source_dir / f"{file_id}{ext}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest and create chunks
        ingest_result = await data_source_ingester.ingest_file(
            file_path=str(file_path),
            source_id=source_id,
            source_name=source_name,
            category=category,
            file_id=file_id,
            metadata={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(content)
            }
        )
        
        if not ingest_result["success"]:
            # Clean up file on failure
            if file_path.exists():
                file_path.unlink()
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to process file: {ingest_result['error']}"
            )
        
        # Store chunks with embeddings
        if settings.DATA_SOURCE_RAG_ENABLED:
            embed_result = await data_source_embedder.store_chunks_batch(
                ingest_result["chunks"],
                generate_embeddings=True
            )
        else:
            # Store without embeddings when disabled
            embed_result = await data_source_embedder.store_chunks_batch(
                ingest_result["chunks"],
                generate_embeddings=False
            )
        
        # Store file metadata
        await data_source_embedder.store_file_metadata(
            file_id=file_id,
            source_id=source_id,
            source_name=source_name,
            category=ingest_result["category"],
            file_name=file.filename,
            file_path=str(file_path),
            chunk_count=ingest_result["chunk_count"],
            metadata={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(content),
                "extraction_metadata": ingest_result["extraction_metadata"]
            }
        )
        
        return {
            "status": "success",
            "message": f"File uploaded and indexed successfully",
            "file_id": file_id,
            "file_name": file.filename,
            "source_id": source_id,
            "source_name": source_name,
            "category": ingest_result["category"],
            "chunk_count": ingest_result["chunk_count"],
            "embeddings_generated": settings.DATA_SOURCE_RAG_ENABLED
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/list")
async def list_sources():
    """
    List all data sources with their statistics.
    """
    try:
        sources = await data_source_retriever.get_sources_list()
        stats = await data_source_embedder.get_index_stats()
        
        return {
            "status": "success",
            "sources": sources,
            "total_sources": len(sources),
            "total_chunks": stats["total_chunks"],
            "total_files": stats["total_files"],
            "rag_enabled": settings.DATA_SOURCE_RAG_ENABLED
        }
    except Exception as e:
        logger.error(f"Error listing sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sources: {str(e)}"
        )


@router.get("/{source_id}/files")
async def get_source_files(source_id: str):
    """
    Get all files for a specific data source.
    """
    try:
        files = await data_source_retriever.get_source_files(source_id)
        
        return {
            "status": "success",
            "source_id": source_id,
            "files": files,
            "total_files": len(files)
        }
    except Exception as e:
        logger.error(f"Error getting source files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get source files: {str(e)}"
        )


@router.get("/search")
async def search_sources(
    query: str,
    category: Optional[str] = None,
    source_id: Optional[str] = None,
    top_k: int = 10
):
    """
    Search across indexed data sources.
    
    Args:
        query: Search query text
        category: Optional category filter
        source_id: Optional source filter
        top_k: Number of results to return
    """
    if not settings.DATA_SOURCE_RAG_ENABLED:
        return {
            "status": "success",
            "message": "Data Source RAG is disabled",
            "results": [],
            "rag_enabled": False
        }
    
    try:
        results = await data_source_retriever.search(
            query=query,
            category=category,
            source_id=source_id,
            top_k=top_k
        )
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "total_results": len(results),
            "rag_enabled": True
        }
    except Exception as e:
        logger.error(f"Error searching sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.delete("/{source_id}")
async def delete_source(source_id: str):
    """
    Delete all files and embeddings for a data source.
    """
    try:
        deleted_count = await data_source_embedder.delete_source_embeddings(source_id)
        
        # Also delete files from disk
        source_dir = DATA_SOURCES_DIR / source_id
        if source_dir.exists():
            shutil.rmtree(source_dir)
        
        return {
            "status": "success",
            "message": f"Deleted source {source_id}",
            "deleted_chunks": deleted_count
        }
    except Exception as e:
        logger.error(f"Error deleting source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete source: {str(e)}"
        )


@router.delete("/{source_id}/files/{file_id}")
async def delete_file(source_id: str, file_id: str):
    """
    Delete a specific file and its embeddings.
    """
    try:
        db = get_database()
        
        # Get file info
        file_doc = await db.data_sources_files.find_one({"_id": file_id})
        
        if not file_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        # Delete embeddings
        deleted_count = await data_source_embedder.delete_file_embeddings(file_id)
        
        # Delete file from disk
        if file_doc.get("file_path"):
            file_path = Path(file_doc["file_path"])
            if file_path.exists():
                file_path.unlink()
        
        return {
            "status": "success",
            "message": f"Deleted file {file_id}",
            "deleted_chunks": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.post("/rebuild-index")
async def rebuild_index(source_id: Optional[str] = None):
    """
    Rebuild embeddings index for all or specific data source.
    Re-generates embeddings for all indexed files.
    """
    if not settings.DATA_SOURCE_RAG_ENABLED:
        return {
            "status": "error",
            "message": "Data Source RAG is disabled. Enable it in settings first."
        }
    
    try:
        db = get_database()
        
        # Build query
        query = {}
        if source_id:
            query["source_id"] = source_id
        
        # Get all files
        files = []
        async for doc in db.data_sources_files.find(query):
            files.append(doc)
        
        if not files:
            return {
                "status": "success",
                "message": "No files found to reindex",
                "reindexed": 0
            }
        
        total_chunks = 0
        errors = 0
        
        for file_doc in files:
            file_path = file_doc.get("file_path")
            
            if not file_path or not Path(file_path).exists():
                logger.warning(f"File not found: {file_path}")
                errors += 1
                continue
            
            # Re-ingest file
            ingest_result = await data_source_ingester.ingest_file(
                file_path=file_path,
                source_id=file_doc["source_id"],
                source_name=file_doc["source_name"],
                category=file_doc["category"],
                file_id=file_doc["_id"],
                metadata=file_doc.get("metadata", {})
            )
            
            if ingest_result["success"]:
                # Delete old embeddings
                await data_source_embedder.delete_file_embeddings(file_doc["_id"])
                
                # Store new embeddings
                await data_source_embedder.store_chunks_batch(
                    ingest_result["chunks"],
                    generate_embeddings=True
                )
                
                total_chunks += ingest_result["chunk_count"]
            else:
                errors += 1
        
        return {
            "status": "success",
            "message": f"Reindexed {len(files) - errors} files",
            "files_processed": len(files),
            "total_chunks": total_chunks,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error rebuilding index: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebuild index: {str(e)}"
        )


@router.get("/categories")
async def get_categories():
    """
    Get list of available categories.
    """
    from app.rag.data_sources_ingest import CATEGORY_KEYWORDS
    
    return {
        "status": "success",
        "categories": list(CATEGORY_KEYWORDS.keys())
    }
