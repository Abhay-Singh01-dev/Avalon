from datetime import datetime
from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field, ConfigDict, PlainSerializer
from bson import ObjectId
from enum import Enum

def serialize_object_id(v) -> str:
    """Serialize ObjectId to string"""
    return str(v)

PyObjectId = Annotated[
    ObjectId,
    PlainSerializer(serialize_object_id, return_type=str)
]

# Base model with common fields
class BaseDBModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias='_id')
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

# Example models - will be expanded later
class ConversationType(str, Enum):
    CHAT = "chat"
    REPORT = "report"
    UPLOAD = "upload"

class Conversation(BaseDBModel):
    type: ConversationType
    title: str
    user_id: str
    metadata: Dict[str, Any] = {}
    is_active: bool = True

class Message(BaseDBModel):
    conversation_id: PyObjectId
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Dict[str, Any] = {}

class DocumentType(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    WORD = "word"
    OTHER = "other"

class UploadedDocument(BaseDBModel):
    filename: str
    file_type: DocumentType
    size: int  # in bytes
    storage_path: str
    user_id: str
    metadata: Dict[str, Any] = {}
    processed: bool = False
