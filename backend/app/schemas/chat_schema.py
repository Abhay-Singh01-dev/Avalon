from pydantic import BaseModel, Field, HttpUrl, validator, ConfigDict, PlainSerializer
from typing import List, Optional, Dict, Any, Annotated, Literal
from datetime import datetime
from enum import Enum
from bson import ObjectId
from .base import ResponseModel

# Custom Pydantic type for MongoDB ObjectId
def validate_object_id(v):
    """Validate and convert ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if not ObjectId.is_valid(v):
        raise ValueError("Invalid ObjectId")
    return ObjectId(v)

def serialize_object_id(v) -> str:
    """Serialize ObjectId to string"""
    return str(v)

PyObjectId = Annotated[
    ObjectId,
    PlainSerializer(serialize_object_id, return_type=str)
]

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class Message(BaseModel):
    """A single message in a conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True
    )

class MessageInDB(Message):
    """Message as stored in the database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True
    )

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None
    stream: bool = False
    model: Optional[str] = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=4000)
    attachments: Optional[List[str]] = Field(None, description="List of uploaded document IDs")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata (e.g., document_id for DOCUMENT mode)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "What are the latest clinical trials for diabetes?",
                "conversation_id": "60d5ec9f581f7a3f1c7e8f2a",
                "project_id": "60d5ec9f581f7a3f1c7e8f2b",
                "stream": False,
                "model": "mistral-7b-instruct-v0.2",
                "temperature": 0.7,
                "metadata": {"document_id": "60d5ec9f581f7a3f1c7e8f2c"}
            }
        }
    )

class ChatResponse(ResponseModel):
    """Response model for chat endpoint"""
    message_id: str
    conversation_id: str
    content: str
    timestamp: datetime
    model: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Message processed successfully",
                "message_id": "60d5ec9f581f7a3f1c7e8f2c",
                "conversation_id": "60d5ec9f581f7a3f1c7e8f2a",
                "content": "Here are some recent clinical trials for diabetes...",
                "timestamp": "2023-01-01T12:00:00Z",
                "model": "mistral-7b-instruct-v0.2",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }
        }
    )

class Conversation(BaseModel):
    """A conversation with a user"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    project_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[MessageInDB] = []
    metadata: Dict[str, Any] = {}
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "id": "60d5ec9f581f7a3f1c7e8f2a",
                "title": "Diabetes Research Discussion",
                "project_id": "60d5ec9f581f7a3f1c7e8f2b",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:30:00Z",
                "messages": [
                    {
                        "id": "60d5ec9f581f7a3f1c7e8f2c",
                        "role": "user",
                        "content": "What are the latest clinical trials for diabetes?",
                        "timestamp": "2023-01-01T12:00:00Z"
                    },
                    {
                        "id": "60d5ec9f581f7a3f1c7e8f2d",
                        "role": "assistant",
                        "content": "Here are some recent clinical trials for diabetes...",
                        "timestamp": "2023-01-01T12:00:05Z"
                    }
                ],
                "metadata": {
                    "source": "web",
                    "user_agent": "Mozilla/5.0..."
                }
            }
        }
    )

class ConversationList(ResponseModel):
    """List of conversations"""
    conversations: List[Conversation]
    total: int
    page: int
    page_size: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Conversations retrieved successfully",
                "conversations": [
                    {
                        "id": "60d5ec9f581f7a3f1c7e8f2a",
                        "title": "Diabetes Research Discussion",
                        "created_at": "2023-01-01T12:00:00Z",
                        "updated_at": "2023-01-01T12:30:00Z",
                        "messages_count": 2
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }
    )


# Research Insights Table Schema
class ResearchInsightRow(BaseModel):
    """A single row in the research insights table"""
    section: str = Field(..., description="Section name (e.g., Market Insights, Clinical Trials)")
    key_findings: List[str] = Field(default_factory=list, description="Bullet list of key findings")
    depth: Literal["High", "Medium", "Low"] = Field("Medium", description="Data depth indicator")
    visualization: Optional[str] = Field(None, description="Graph ID or visualization type")
    links: List[str] = Field(default_factory=list, description="Source URLs")
    status: Literal["Complete", "Missing Data", "Limited"] = Field("Complete", description="Data availability status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "section": "Market Insights",
                "key_findings": [
                    "Global market size: $XX billion",
                    "CAGR: XX% (2024-2030)",
                    "Key players: Company A, Company B"
                ],
                "depth": "High",
                "visualization": "market_chart_001",
                "links": ["https://example.com/source1", "https://example.com/source2"],
                "status": "Complete"
            }
        }
    )


class ResearchInsightsTable(BaseModel):
    """Complete research insights table structure"""
    insights: List[ResearchInsightRow] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "insights": [
                    {
                        "section": "Market Insights",
                        "key_findings": ["Global market size: $50B", "CAGR: 8.5%"],
                        "depth": "High",
                        "visualization": "market_chart_001",
                        "links": ["https://example.com/market"],
                        "status": "Complete"
                    },
                    {
                        "section": "Clinical Trials",
                        "key_findings": ["45 active trials", "Phase III: 12 trials"],
                        "depth": "Medium",
                        "visualization": None,
                        "links": ["https://clinicaltrials.gov"],
                        "status": "Complete"
                    }
                ]
            }
        }
    )
