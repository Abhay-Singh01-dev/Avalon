from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from .base import ResponseModel

class ReportType(str, Enum):
    CLINICAL_TRIAL = "clinical_trial"
    PATENT_ANALYSIS = "patent_analysis"
    MARKET_RESEARCH = "market_research"
    CUSTOM = "custom"

class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    TXT = "txt"

class ReportRequest(BaseModel):
    """Request model for generating a report"""
    report_type: ReportType
    parameters: Dict[str, Any] = {}
    format: ReportFormat = ReportFormat.PDF
    title: Optional[str] = None
    description: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_type": "clinical_trial",
                "parameters": {
                    "drug_name": "Ibuprofen",
                    "phase": 3,
                    "date_range": {
                        "start": "2020-01-01",
                        "end": "2023-12-31"
                    }
                },
                "format": "pdf",
                "title": "Clinical Trial Analysis for Ibuprofen",
                "description": "Comprehensive analysis of clinical trials for Ibuprofen"
            }
        }
    )

class ReportResponse(ResponseModel):
    """Response model for report generation"""
    report_id: str
    status: ReportStatus
    report_type: ReportType
    format: ReportFormat
    title: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Report generation started",
                "report_id": "rep_123456789",
                "status": "processing",
                "report_type": "clinical_trial",
                "format": "pdf",
                "title": "Clinical Trial Analysis for Ibuprofen",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }
    )

class ReportListResponse(ResponseModel):
    """Response model for listing reports"""
    reports: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Reports retrieved successfully",
                "reports": [
                    {
                        "id": "rep_123456789",
                        "title": "Clinical Trial Analysis for Ibuprofen",
                        "report_type": "clinical_trial",
                        "status": "completed",
                        "created_at": "2023-01-01T12:00:00Z",
                        "updated_at": "2023-01-01T12:05:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }
    )

class ReportContentResponse(ResponseModel):
    """Response model for report content"""
    report_id: str
    content: str
    format: ReportFormat
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Report content retrieved successfully",
                "report_id": "rep_123456789",
                "content": "<h1>Clinical Trial Analysis for Ibuprofen</h1>...",
                "format": "html"
            }
        }
    )
