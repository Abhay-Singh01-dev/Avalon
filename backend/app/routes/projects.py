from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure
from pydantic import BaseModel
import logging
import os
import shutil
from pathlib import Path
import uuid

from app.db.mongo import get_database
from app.schemas.chat_schema import PyObjectId
from app.config import settings
from app.services.rag import DocumentExtractor, TextChunker, Embedder, ProjectRetriever
from app.services.rag.retriever import get_rag_status

router = APIRouter(tags=["projects"])
logger = logging.getLogger(__name__)

PROJECTS_COLLECTION = "projects"
CONVERSATIONS_COLLECTION = "conversations"
PROJECT_FILES_COLLECTION = "project_files"
PROJECT_LINKS_COLLECTION = "project_links"

# Ensure project files directory exists
PROJECT_FILES_DIR = Path(settings.PROJECT_FILES_DIR)
PROJECT_FILES_DIR.mkdir(parents=True, exist_ok=True)


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    chat_ids: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProjectsListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


@router.get("", response_model=ProjectsListResponse)
async def list_projects():
    """
    List all projects.
    Returns all projects from MongoDB.
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        
        # Get all projects
        cursor = projects_collection.find({}).sort("updated_at", -1)
        
        projects = []
        async for doc in cursor:
            # Convert _id to string
            doc["id"] = str(doc.pop("_id"))
            # Convert chat_ids ObjectIds to strings
            if "chat_ids" in doc and doc["chat_ids"]:
                doc["chat_ids"] = [str(chat_id) if isinstance(chat_id, ObjectId) else chat_id for chat_id in doc["chat_ids"]]
            # Convert dates to ISO strings
            if "created_at" in doc and isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].isoformat()
            if "updated_at" in doc and isinstance(doc["updated_at"], datetime):
                doc["updated_at"] = doc["updated_at"].isoformat()
            projects.append(ProjectResponse(**doc))
        
        total = await projects_collection.count_documents({})
        
        return ProjectsListResponse(projects=projects, total=total)
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving projects: {str(e)}"
        )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    """
    Create a new project.
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        
        # Create project document
        project_doc = {
            "name": project.name,
            "description": project.description or "",
            "chat_ids": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert project
        result = await projects_collection.insert_one(project_doc)
        project_id = result.inserted_id
        
        # Fetch the created project
        created_project = await projects_collection.find_one({"_id": project_id})
        created_project["id"] = str(created_project.pop("_id"))
        if "created_at" in created_project and isinstance(created_project["created_at"], datetime):
            created_project["created_at"] = created_project["created_at"].isoformat()
        if "updated_at" in created_project and isinstance(created_project["updated_at"], datetime):
            created_project["updated_at"] = created_project["updated_at"].isoformat()
        
        return ProjectResponse(**created_project)
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the project: {str(e)}"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """
    Get a single project by ID.
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        
        # Convert string ID to ObjectId
        try:
            proj_id = PyObjectId(project_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project_id: {str(e)}"
            )
        
        # Find the project
        project = await projects_collection.find_one({"_id": proj_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Convert _id to string
        project["id"] = str(project.pop("_id"))
        # Convert chat_ids ObjectIds to strings
        if "chat_ids" in project and project["chat_ids"]:
            project["chat_ids"] = [str(chat_id) if isinstance(chat_id, ObjectId) else chat_id for chat_id in project["chat_ids"]]
        # Convert dates to ISO strings
        if "created_at" in project and isinstance(project["created_at"], datetime):
            project["created_at"] = project["created_at"].isoformat()
        if "updated_at" in project and isinstance(project["updated_at"], datetime):
            project["updated_at"] = project["updated_at"].isoformat()
        
        return ProjectResponse(**project)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving the project: {str(e)}"
        )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_update: ProjectUpdate):
    """
    Update a project (rename or update description).
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        
        # Convert string ID to ObjectId
        try:
            proj_id = PyObjectId(project_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project_id: {str(e)}"
            )
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        if project_update.name is not None:
            update_doc["name"] = project_update.name
        if project_update.description is not None:
            update_doc["description"] = project_update.description
        
        # Update project
        result = await projects_collection.update_one(
            {"_id": proj_id},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Fetch updated project
        updated_project = await projects_collection.find_one({"_id": proj_id})
        updated_project["id"] = str(updated_project.pop("_id"))
        if "chat_ids" in updated_project and updated_project["chat_ids"]:
            updated_project["chat_ids"] = [str(chat_id) if isinstance(chat_id, ObjectId) else chat_id for chat_id in updated_project["chat_ids"]]
        if "created_at" in updated_project and isinstance(updated_project["created_at"], datetime):
            updated_project["created_at"] = updated_project["created_at"].isoformat()
        if "updated_at" in updated_project and isinstance(updated_project["updated_at"], datetime):
            updated_project["updated_at"] = updated_project["updated_at"].isoformat()
        
        return ProjectResponse(**updated_project)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the project: {str(e)}"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    """
    Delete a project.
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Convert string ID to ObjectId
        try:
            proj_id = PyObjectId(project_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project_id: {str(e)}"
            )
        
        # Check if project exists
        project = await projects_collection.find_one({"_id": proj_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Remove project_id from all conversations
        await conversations_collection.update_many(
            {"project_id": proj_id},
            {"$set": {"project_id": None}}
        )
        
        # Delete project
        result = await projects_collection.delete_one({"_id": proj_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        return None
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the project: {str(e)}"
        )


@router.get("/{project_id}/chats", response_model=Dict[str, Any])
async def get_project_chats(project_id: str):
    """
    Get all chats in a project.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Convert string ID to ObjectId
        try:
            proj_id = PyObjectId(project_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project_id: {str(e)}"
            )
        
        # Find all conversations in this project
        cursor = conversations_collection.find({"project_id": proj_id}).sort("updated_at", -1)
        
        chats = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            if "project_id" in doc and doc["project_id"]:
                doc["project_id"] = str(doc["project_id"])
            chats.append({
                "id": doc["id"],
                "title": doc.get("title", ""),
                "updated_at": doc.get("updated_at").isoformat() if isinstance(doc.get("updated_at"), datetime) else None
            })
        
        return {"chats": chats}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting project chats {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving project chats: {str(e)}"
        )


@router.post("/{project_id}/add_chat", status_code=status.HTTP_200_OK)
async def add_chat_to_project(project_id: str, payload: Dict[str, str]):
    """
    Add a chat to a project.
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        chat_id = payload.get("chat_id")
        if not chat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chat_id is required"
            )
        
        # Convert string IDs to ObjectId
        try:
            proj_id = PyObjectId(project_id)
            conv_id = PyObjectId(chat_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ID: {str(e)}"
            )
        
        # Verify project exists
        project = await projects_collection.find_one({"_id": proj_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Verify conversation exists
        conversation = await conversations_collection.find_one({"_id": conv_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {chat_id} not found"
            )
        
        # Add chat to project's chat_ids (if not already present)
        await projects_collection.update_one(
            {"_id": proj_id},
            {
                "$addToSet": {"chat_ids": conv_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Update conversation's project_id
        await conversations_collection.update_one(
            {"_id": conv_id},
            {
                "$set": {
                    "project_id": proj_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"status": "success", "message": "Chat added to project"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error adding chat to project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while adding chat to project: {str(e)}"
        )


@router.post("/{project_id}/remove_chat", status_code=status.HTTP_200_OK)
async def remove_chat_from_project(project_id: str, payload: Dict[str, str]):
    """
    Remove a chat from a project.
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        chat_id = payload.get("chat_id")
        if not chat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chat_id is required"
            )
        
        # Convert string IDs to ObjectId
        try:
            proj_id = PyObjectId(project_id)
            conv_id = PyObjectId(chat_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ID: {str(e)}"
            )
        
        # Remove chat from project's chat_ids
        await projects_collection.update_one(
            {"_id": proj_id},
            {
                "$pull": {"chat_ids": conv_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Remove project_id from conversation
        await conversations_collection.update_one(
            {"_id": conv_id},
            {
                "$set": {
                    "project_id": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"status": "success", "message": "Chat removed from project"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error removing chat from project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while removing chat from project: {str(e)}"
        )


# ============================================
# PROJECT FILES ENDPOINTS (RAG Document Upload)
# ============================================

class ProjectFileResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str  # uploaded, processing, indexed, failed
    extracted_text_preview: Optional[str] = None
    chunk_count: Optional[int] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


class ProjectLinkCreate(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectLinkResponse(BaseModel):
    id: str
    project_id: str
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = False  # Disabled by default - requires larger model
    fetched: bool = False
    created_at: Optional[str] = None


@router.get("/rag/status")
async def get_project_rag_status():
    """
    Get RAG system status including all feature flags.
    Shows what's enabled/disabled and why.
    """
    return get_rag_status()


@router.post("/{project_id}/upload", response_model=ProjectFileResponse)
async def upload_project_file(
    project_id: str,
    file: UploadFile = File(...)
):
    """
    Upload a document to a project's knowledge base.
    
    Supported formats: PDF, DOCX, TXT, CSV, XLSX
    
    The document will be:
    1. Saved to project_files/{project_id}/
    2. Text extracted
    3. Chunked into segments
    4. Embeddings generated (if RAG enabled)
    
    Note: RAG retrieval is DISABLED by default until larger models are installed.
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        files_collection = db[PROJECT_FILES_COLLECTION]
        
        # Validate project exists
        try:
            proj_id = PyObjectId(project_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project_id"
            )
        
        project = await projects_collection.find_one({"_id": proj_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Validate file type
        original_filename = file.filename or "unknown"
        file_ext = Path(original_filename).suffix.lower()
        allowed_types = {'.pdf', '.docx', '.txt', '.csv', '.xlsx'}
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_types)}"
            )
        
        # Create project directory
        project_dir = PROJECT_FILES_DIR / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        stored_filename = f"{file_id}{file_ext}"
        file_path = project_dir / stored_filename
        
        # Save uploaded file
        content = await file.read()
        file_size = len(content)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Create file record
        file_doc = {
            "project_id": project_id,
            "filename": stored_filename,
            "original_filename": original_filename,
            "file_type": file_ext.lstrip('.'),
            "file_size": file_size,
            "file_path": str(file_path),
            "status": "uploaded",
            "extracted_text": None,
            "chunk_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "error": None
        }
        
        result = await files_collection.insert_one(file_doc)
        file_doc_id = str(result.inserted_id)
        
        # Process file: extract text, chunk, and embed
        try:
            # Extract text
            extractor = DocumentExtractor(str(PROJECT_FILES_DIR))
            extraction_result = extractor.extract_text(str(file_path), file_ext)
            
            if not extraction_result["success"]:
                await files_collection.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {
                        "status": "failed",
                        "error": extraction_result.get("error", "Extraction failed"),
                        "updated_at": datetime.utcnow()
                    }}
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to extract text: {extraction_result.get('error')}"
                )
            
            extracted_text = extraction_result["text"]
            
            # Save extracted text
            extractor.save_extracted_text(project_id, file_doc_id, extracted_text)
            
            # Chunk text
            chunker = TextChunker(
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
                project_files_dir=str(PROJECT_FILES_DIR)
            )
            
            chunks = chunker.chunk_text(
                extracted_text,
                file_doc_id,
                metadata={
                    "filename": original_filename,
                    "file_type": file_ext.lstrip('.')
                }
            )
            
            # Save chunks
            chunker.save_chunks(project_id, file_doc_id, chunks)
            
            # Generate embeddings (only if RAG is enabled)
            embedding_result = {"embedded_count": 0, "message": "Embedding skipped - RAG disabled"}
            if settings.ENABLE_PROJECT_RAG:
                embedder = Embedder()
                embedding_result = await embedder.embed_and_store_chunks(
                    project_id, file_doc_id, chunks
                )
            
            # Update file record
            await files_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {
                    "status": "indexed",
                    "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
                    "chunk_count": len(chunks),
                    "embedding_count": embedding_result.get("embedded_count", 0),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            logger.info(f"Successfully processed file {original_filename} for project {project_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            await files_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.utcnow()
                }}
            )
        
        # Fetch and return the file record
        file_record = await files_collection.find_one({"_id": result.inserted_id})
        
        return ProjectFileResponse(
            id=str(file_record["_id"]),
            project_id=file_record["project_id"],
            filename=file_record["filename"],
            original_filename=file_record["original_filename"],
            file_type=file_record["file_type"],
            file_size=file_record["file_size"],
            status=file_record["status"],
            extracted_text_preview=file_record.get("extracted_text", "")[:200] if file_record.get("extracted_text") else None,
            chunk_count=file_record.get("chunk_count", 0),
            created_at=file_record["created_at"].isoformat() if isinstance(file_record.get("created_at"), datetime) else None,
            error=file_record.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/{project_id}/files", response_model=Dict[str, Any])
async def get_project_files(project_id: str):
    """
    Get all files uploaded to a project.
    """
    try:
        db = get_database()
        files_collection = db[PROJECT_FILES_COLLECTION]
        
        cursor = files_collection.find({"project_id": project_id}).sort("created_at", -1)
        
        files = []
        async for doc in cursor:
            files.append(ProjectFileResponse(
                id=str(doc["_id"]),
                project_id=doc["project_id"],
                filename=doc["filename"],
                original_filename=doc["original_filename"],
                file_type=doc["file_type"],
                file_size=doc["file_size"],
                status=doc["status"],
                extracted_text_preview=doc.get("extracted_text", "")[:200] if doc.get("extracted_text") else None,
                chunk_count=doc.get("chunk_count", 0),
                created_at=doc["created_at"].isoformat() if isinstance(doc.get("created_at"), datetime) else None,
                error=doc.get("error")
            ).model_dump())
        
        # Get RAG status
        rag_status = get_rag_status()
        
        return {
            "files": files,
            "total": len(files),
            "rag_enabled": settings.ENABLE_PROJECT_RAG,
            "rag_status_message": rag_status["message"]
        }
        
    except Exception as e:
        logger.error(f"Error getting project files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project files: {str(e)}"
        )


@router.get("/{project_id}/files/{file_id}/preview")
async def get_file_preview(project_id: str, file_id: str):
    """
    Get a preview of extracted text from a file.
    """
    try:
        db = get_database()
        files_collection = db[PROJECT_FILES_COLLECTION]
        
        try:
            doc_id = PyObjectId(file_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file_id"
            )
        
        file_doc = await files_collection.find_one({
            "_id": doc_id,
            "project_id": project_id
        })
        
        if not file_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Try to load full extracted text from file
        text_file = PROJECT_FILES_DIR / project_id / f"{file_id}.txt"
        full_text = None
        
        if text_file.exists():
            with open(text_file, 'r', encoding='utf-8') as f:
                full_text = f.read()
        
        return {
            "id": str(file_doc["_id"]),
            "filename": file_doc["original_filename"],
            "file_type": file_doc["file_type"],
            "status": file_doc["status"],
            "extracted_text": full_text or file_doc.get("extracted_text", ""),
            "chunk_count": file_doc.get("chunk_count", 0),
            "rag_enabled": settings.ENABLE_PROJECT_RAG
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file preview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file preview: {str(e)}"
        )


@router.post("/{project_id}/reindex")
async def reindex_project_documents(project_id: str):
    """
    Re-index all documents in a project.
    This will regenerate chunks and embeddings.
    
    Note: Embedding generation only works if ENABLE_PROJECT_RAG=true
    """
    try:
        db = get_database()
        files_collection = db[PROJECT_FILES_COLLECTION]
        
        # Get all files for project
        cursor = files_collection.find({"project_id": project_id})
        files = await cursor.to_list(None)
        
        if not files:
            return {
                "status": "success",
                "message": "No files to reindex",
                "reindexed_count": 0
            }
        
        reindexed = 0
        errors = []
        
        chunker = TextChunker(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            project_files_dir=str(PROJECT_FILES_DIR)
        )
        embedder = Embedder()
        
        for file_doc in files:
            file_id = str(file_doc["_id"])
            
            try:
                # Load extracted text
                text_file = PROJECT_FILES_DIR / project_id / f"{file_id}.txt"
                
                if not text_file.exists():
                    # Re-extract from original file
                    extractor = DocumentExtractor(str(PROJECT_FILES_DIR))
                    result = extractor.extract_text(file_doc["file_path"])
                    
                    if not result["success"]:
                        errors.append(f"{file_doc['original_filename']}: extraction failed")
                        continue
                    
                    extracted_text = result["text"]
                    extractor.save_extracted_text(project_id, file_id, extracted_text)
                else:
                    with open(text_file, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()
                
                # Re-chunk
                chunks = chunker.chunk_text(
                    extracted_text,
                    file_id,
                    metadata={
                        "filename": file_doc["original_filename"],
                        "file_type": file_doc["file_type"]
                    }
                )
                chunker.save_chunks(project_id, file_id, chunks)
                
                # Re-embed if RAG enabled
                if settings.ENABLE_PROJECT_RAG:
                    await embedder.embed_and_store_chunks(project_id, file_id, chunks)
                
                # Update file record
                await files_collection.update_one(
                    {"_id": file_doc["_id"]},
                    {"$set": {
                        "status": "indexed",
                        "chunk_count": len(chunks),
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                reindexed += 1
                
            except Exception as e:
                errors.append(f"{file_doc['original_filename']}: {str(e)}")
        
        return {
            "status": "success" if not errors else "partial",
            "message": f"Reindexed {reindexed} files" + (f", {len(errors)} errors" if errors else ""),
            "reindexed_count": reindexed,
            "errors": errors,
            "rag_enabled": settings.ENABLE_PROJECT_RAG
        }
        
    except Exception as e:
        logger.error(f"Error reindexing project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex project: {str(e)}"
        )


@router.delete("/{project_id}/files/{file_id}")
async def delete_project_file(project_id: str, file_id: str):
    """
    Delete a file from a project's knowledge base.
    """
    try:
        db = get_database()
        files_collection = db[PROJECT_FILES_COLLECTION]
        
        try:
            doc_id = PyObjectId(file_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file_id"
            )
        
        file_doc = await files_collection.find_one({
            "_id": doc_id,
            "project_id": project_id
        })
        
        if not file_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Delete physical files
        file_path = Path(file_doc.get("file_path", ""))
        if file_path.exists():
            file_path.unlink()
        
        text_file = PROJECT_FILES_DIR / project_id / f"{file_id}.txt"
        if text_file.exists():
            text_file.unlink()
        
        chunks_file = PROJECT_FILES_DIR / project_id / f"{file_id}_chunks.jsonl"
        if chunks_file.exists():
            chunks_file.unlink()
        
        # Delete embeddings
        embedder = Embedder()
        await embedder.delete_document_embeddings(project_id, file_id)
        
        # Delete file record
        await files_collection.delete_one({"_id": doc_id})
        
        return {"status": "success", "message": "File deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


# ============================================
# PROJECT LINKS ENDPOINTS (Saved for future use)
# ============================================

@router.post("/{project_id}/add-link", response_model=ProjectLinkResponse)
async def add_project_link(project_id: str, link_data: ProjectLinkCreate):
    """
    Add a link to a project for future indexing.
    
    Note: Link fetching/scraping is DISABLED by default.
    Links are saved for future use when larger models are available.
    """
    try:
        db = get_database()
        projects_collection = db[PROJECTS_COLLECTION]
        links_collection = db[PROJECT_LINKS_COLLECTION]
        
        # Validate project exists
        try:
            proj_id = PyObjectId(project_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project_id"
            )
        
        project = await projects_collection.find_one({"_id": proj_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Validate URL format
        url = link_data.url.strip()
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL must start with http:// or https://"
            )
        
        # Check for duplicate
        existing = await links_collection.find_one({
            "project_id": project_id,
            "url": url
        })
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Link already exists in this project"
            )
        
        # Create link record
        link_doc = {
            "project_id": project_id,
            "url": url,
            "title": link_data.title or url,
            "description": link_data.description,
            "enabled": False,  # Always disabled - requires larger model
            "fetched": False,
            "content": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await links_collection.insert_one(link_doc)
        
        return ProjectLinkResponse(
            id=str(result.inserted_id),
            project_id=project_id,
            url=url,
            title=link_data.title or url,
            description=link_data.description,
            enabled=False,
            fetched=False,
            created_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding link: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add link: {str(e)}"
        )


@router.get("/{project_id}/links", response_model=Dict[str, Any])
async def get_project_links(project_id: str):
    """
    Get all links saved for a project.
    """
    try:
        db = get_database()
        links_collection = db[PROJECT_LINKS_COLLECTION]
        
        cursor = links_collection.find({"project_id": project_id}).sort("created_at", -1)
        
        links = []
        async for doc in cursor:
            links.append(ProjectLinkResponse(
                id=str(doc["_id"]),
                project_id=doc["project_id"],
                url=doc["url"],
                title=doc.get("title"),
                description=doc.get("description"),
                enabled=doc.get("enabled", False),
                fetched=doc.get("fetched", False),
                created_at=doc["created_at"].isoformat() if isinstance(doc.get("created_at"), datetime) else None
            ).model_dump())
        
        return {
            "links": links,
            "total": len(links),
            "link_fetch_enabled": settings.ENABLE_LINK_FETCH,
            "message": "Link fetching is disabled. Requires larger model (≥14B)." if not settings.ENABLE_LINK_FETCH else "Link fetching is enabled."
        }
        
    except Exception as e:
        logger.error(f"Error getting project links: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project links: {str(e)}"
        )


@router.delete("/{project_id}/links/{link_id}")
async def delete_project_link(project_id: str, link_id: str):
    """
    Delete a link from a project.
    """
    try:
        db = get_database()
        links_collection = db[PROJECT_LINKS_COLLECTION]
        
        try:
            doc_id = PyObjectId(link_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid link_id"
            )
        
        result = await links_collection.delete_one({
            "_id": doc_id,
            "project_id": project_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        return {"status": "success", "message": "Link deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting link: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete link: {str(e)}"
        )
