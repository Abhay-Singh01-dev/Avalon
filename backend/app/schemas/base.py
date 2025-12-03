from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class Status(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    PENDING = "pending"

class ResponseModel(BaseModel):
    """Base response model for all API responses"""
    status: Status
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    model_config = ConfigDict()

class PaginatedResponse(ResponseModel):
    """Response model for paginated data"""
    page: int
    total_pages: int
    total_items: int
    items_per_page: int

class ErrorResponse(ResponseModel):
    """Standard error response"""
    status: Status = Status.ERROR
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(ResponseModel):
    """Standard success response"""
    status: Status = Status.SUCCESS
    message: str = "Operation completed successfully"

class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Dict[str, str] = {}
