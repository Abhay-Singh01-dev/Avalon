from datetime import datetime
from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, PlainSerializer
from bson import ObjectId

def serialize_object_id(v) -> str:
    """Serialize ObjectId to string"""
    return str(v)

PyObjectId = Annotated[
    ObjectId,
    PlainSerializer(serialize_object_id, return_type=str)
]

class DocumentBase(BaseModel):
    """Base model for document metadata."""
    filename: str = Field(..., description="Original filename")
    filepath: str = Field(..., description="Path to the stored file")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the document"
    )

class DocumentCreate(DocumentBase):
    """Model for creating a new document."""
    content: str = Field(..., description="Extracted text content from the document")

class DocumentInDB(DocumentBase):
    """Model for documents stored in the database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    content: str = Field(..., description="Extracted text content from the document")
    processed: bool = Field(default=False, description="Whether the document has been processed")
    processed_at: Optional[datetime] = Field(None, description="When the document was processed")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "filename": "clinical_trial.pdf",
                "filepath": "uploads/123e4567-e89b-12d3-a456-426614174000.pdf",
                "content_type": "application/pdf",
                "size": 10240,
                "content": "Extracted text content from the document...",
                "processed": True,
                "processed_at": "2023-01-01T12:00:00Z",
                "created_at": "2023-01-01T12:00:00Z",
                "metadata": {}
            }
        }
    )

class DocumentResponse(DocumentInDB):
    """Response model for document endpoints."""
    # Note: 'content' field is inherited but can be excluded at serialization time if needed
    pass

class DocumentProcessResponse(BaseModel):
    """Response model for document processing results."""
    document_id: str = Field(..., description="MongoDB document ID")
    status: str = Field(..., description="Processing status")
    message: Optional[str] = Field(None, description="Additional status message")
    insights: Optional[Dict[str, Any]] = Field(None, description="Extracted insights from the document")

class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
