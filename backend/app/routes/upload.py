"""
Document Upload Routes

Hospital-Grade Document Processing for Pilot Deployment
- PHI detection in uploaded documents
- Local-only text extraction
- Full audit trail of document processing
"""

import os
import uuid
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.file_extractor import FileExtractor
from app.db.mongo import get_database
from app.schemas.document_schema import DocumentInDB
from app.utils.phi_detector import detect_phi_in_document, PHIDetectionResult

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types and their MIME types
ALLOWED_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain'
}

def get_file_extension(filename: str) -> str:
    """Get the lowercase file extension with dot."""
    return Path(filename).suffix.lower()

async def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Save uploaded file to disk asynchronously."""
    try:
        with open(destination, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
    except Exception as e:
        if destination.exists():
            destination.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

@router.post("/document", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Upload a document file (PDF, DOCX, TXT) and process its content.
    
    - **file**: Document file to upload (max 25MB)
    - Returns: Document ID and processing status
    """
    # Validate file extension
    file_ext = get_file_extension(file.filename)
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    try:
        # Save file
        await save_upload_file(file, file_path)
        
        # Extract text content (LOCAL-ONLY processing for PHI safety)
        logger.info(f"[DOC_UPLOAD] Extracting text from {file.filename}")
        extractor = FileExtractor()
        text_content = await extractor.extract_text(str(file_path))
        
        # PHI Detection in document content (PILOT CRITICAL)
        logger.info(f"[DOC_UPLOAD] Scanning for PHI in {file.filename}")
        phi_result = detect_phi_in_document(text_content)
        
        if phi_result.contains_phi:
            logger.warning(
                f"[DOC_PHI_DETECTED] PHI found in {file.filename}. "
                f"Types: {[t.value for t in phi_result.phi_types]}, "
                f"Confidence: {phi_result.confidence:.2f}"
            )
        
        # Prepare document for database with PHI metadata
        document = DocumentInDB(
            filename=file.filename,
            filepath=str(file_path),
            content=text_content,
            content_type=file.content_type,
            size=os.path.getsize(file_path),
            created_at=datetime.utcnow()
        )
        
        # Add document dict and include PHI detection results
        doc_dict = document.dict(by_alias=True)
        doc_dict["phi_detected"] = phi_result.contains_phi
        doc_dict["phi_types"] = [t.value for t in phi_result.phi_types]
        doc_dict["phi_confidence"] = phi_result.confidence
        doc_dict["processing_mode"] = "local_only"  # Always local for document processing
        
        # Save to MongoDB
        result = await db.internal_docs.insert_one(doc_dict)
        
        logger.info(f"[DOC_UPLOAD] Successfully processed {file.filename} (PHI: {phi_result.contains_phi})")
        
        return {
            "success": True,
            "file_id": str(result.inserted_id),
            "doc_id": str(result.inserted_id),
            "name": file.filename,
            "filename": file.filename,
            "message": "File uploaded and processed successfully",
            "phi_detected": phi_result.contains_phi,
            "phi_warning": "⚠️ PHI detected - Document will be processed locally only" if phi_result.contains_phi else None,
            "processing_mode": "local_only"
        }
        
    except ValueError as e:
        # Clean up file if processing fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )

@router.get("/documents/{doc_id}", response_model=DocumentInDB)
async def get_document(
    doc_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Retrieve a processed document by its ID.
    """
    from bson import ObjectId
    
    try:
        document = await db.internal_docs.find_one({"_id": ObjectId(doc_id)})
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )
