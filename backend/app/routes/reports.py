from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure
from pydantic import BaseModel
import logging
import uuid

from app.db.mongo import get_database
from app.schemas.chat_schema import PyObjectId
from app.utils.report_generator import (
    extract_agent_data,
    generate_pdf_content,
    generate_csv_content,
    save_report_files
)

router = APIRouter(tags=["reports"])
logger = logging.getLogger(__name__)

REPORTS_COLLECTION = "reports"
CONVERSATIONS_COLLECTION = "conversations"


class ReportGenerateRequest(BaseModel):
    report_type: Optional[str] = None
    parameters: Dict[str, Any] = {}
    format: str = "pdf"  # pdf, csv, xlsx
    title: Optional[str] = None
    description: Optional[str] = None
    conversation_id: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    name: str
    about: Optional[str] = None
    query: Optional[str] = None
    type: str
    created_at: Optional[str] = None
    file_url: Optional[str] = None
    has_table: Optional[bool] = None
    size: Optional[int] = None


class ReportsListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int


@router.post("/generate", response_model=Dict[str, Any])
async def generate_report(request: ReportGenerateRequest):
    """
    Generate a real PDF and CSV report from conversation data.
    Extracts agent summaries and data tables from the conversation.
    """
    try:
        db = get_database()
        reports_collection = db[REPORTS_COLLECTION]
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Generate unique report ID
        report_id = str(uuid.uuid4())
        
        # Get conversation data
        if not request.conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="conversation_id is required to generate a report"
            )
        
        try:
            conv_id = PyObjectId(request.conversation_id)
            conversation = await conversations_collection.find_one({"_id": conv_id})
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {request.conversation_id} not found"
                )
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid conversation_id: {str(e)}"
            )
        
        # Extract messages
        messages = conversation.get("messages", [])
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation has no messages"
            )
        
        # Extract query from first user message
        query = ""
        for msg in messages:
            if msg.get("role") == "user":
                query = msg.get("content", "")
                break
        
        # Extract agent data from conversation
        logger.info(f"[REPORT_GEN] Extracting agent data from {len(messages)} messages")
        report_data = extract_agent_data(messages)
        
        # Generate title if not provided
        title = request.title or f"Research Report: {query[:50]}"
        
        # Generate PDF content (summaries only)
        logger.info(f"[REPORT_GEN] Generating PDF content for report {report_id}")
        pdf_content = generate_pdf_content(
            report_data=report_data,
            title=title,
            conversation_id=request.conversation_id,
            report_id=report_id
        )
        
        # Generate CSV content (tables only or "No table available")
        logger.info(f"[REPORT_GEN] Generating CSV content (has_table={report_data['has_table']})")
        csv_content = generate_csv_content(report_data)
        
        # Save files to disk
        pdf_path, csv_path, pdf_size, csv_size = await save_report_files(
            report_id=report_id,
            pdf_content=pdf_content,
            csv_content=csv_content
        )
        
        # Create report documents in MongoDB (one for PDF, one for CSV)
        pdf_report_doc = {
            "_id": f"{report_id}_pdf",
            "name": f"{title} (PDF)",
            "about": request.description or f"Research report generated from conversation",
            "query": query,
            "type": "pdf",
            "report_type": request.report_type or "general",
            "parameters": request.parameters,
            "conversation_id": request.conversation_id,
            "status": "completed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "file_url": f"/uploads/reports/{report_id}.pdf",
            "size": pdf_size,
            "has_table": False  # PDF contains summaries only
        }
        
        csv_report_doc = {
            "_id": f"{report_id}_csv",
            "name": f"{title} (CSV)",
            "about": request.description or f"Data table from research report",
            "query": query,
            "type": "csv",
            "report_type": request.report_type or "general",
            "parameters": request.parameters,
            "conversation_id": request.conversation_id,
            "status": "completed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "file_url": f"/uploads/reports/{report_id}.csv",
            "size": csv_size,
            "has_table": report_data["has_table"]
        }
        
        # Insert both reports
        await reports_collection.insert_one(pdf_report_doc)
        await reports_collection.insert_one(csv_report_doc)
        
        logger.info(f"[REPORT_GEN] Successfully generated reports: PDF and CSV")
        
        return {
            "status": "success",
            "report_id": report_id,
            "pdf_report_id": pdf_report_doc["_id"],
            "csv_report_id": csv_report_doc["_id"],
            "message": "Report generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the report: {str(e)}"
        )


@router.get("", response_model=ReportsListResponse)
async def list_reports(
    page: int = 1,
    page_size: int = 10,
    type: Optional[str] = None
):
    """
    List all reports with pagination.
    """
    try:
        db = get_database()
        reports_collection = db[REPORTS_COLLECTION]
        
        # Build query
        query = {}
        if type:
            query["type"] = type
        
        # Get total count
        total = await reports_collection.count_documents(query)
        
        # Get paginated results
        skip = (page - 1) * page_size
        cursor = reports_collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        
        reports = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            if "created_at" in doc and isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].isoformat()
            reports.append(ReportResponse(
                id=doc["id"],
                name=doc.get("name", ""),
                about=doc.get("about"),
                query=doc.get("query"),
                type=doc.get("type", "pdf"),
                created_at=doc.get("created_at"),
                file_url=doc.get("file_url"),
                has_table=doc.get("has_table"),
                size=doc.get("size")
            ))
        
        return ReportsListResponse(reports=reports, total=total)
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving reports: {str(e)}"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str):
    """
    Get a generated report by ID.
    """
    try:
        db = get_database()
        reports_collection = db[REPORTS_COLLECTION]
        
        # Find the report
        report = await reports_collection.find_one({"_id": report_id})
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        # Convert _id to string
        report["id"] = str(report.pop("_id"))
        if "created_at" in report and isinstance(report["created_at"], datetime):
            report["created_at"] = report["created_at"].isoformat()
        
        return ReportResponse(
            id=report["id"],
            name=report.get("name", ""),
            about=report.get("about"),
            query=report.get("query"),
            type=report.get("type", "pdf"),
            created_at=report.get("created_at"),
            file_url=report.get("file_url"),
            has_table=report.get("has_table"),
            size=report.get("size")
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting report {report_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving the report: {str(e)}"
        )


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """
    Delete a report by ID.
    """
    try:
        db = get_database()
        reports_collection = db[REPORTS_COLLECTION]
        
        # Find the report
        report = await reports_collection.find_one({"_id": report_id})
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        # Delete the report
        result = await reports_collection.delete_one({"_id": report_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete report"
            )
        
        # TODO: In production, also delete the actual file from storage (S3, etc.)
        
        return {
            "status": "success",
            "message": f"Report {report_id} deleted successfully"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the report: {str(e)}"
        )


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """
    Download a generated report file (PDF or CSV).
    
    PILOT: Fully functional file download from local storage.
    """
    from fastapi.responses import FileResponse
    import os
    
    try:
        db = get_database()
        reports_collection = db[REPORTS_COLLECTION]
        
        # Find the report
        report = await reports_collection.find_one({"_id": report_id})
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        # Get file URL and determine file path
        file_url = report.get("file_url", "")
        report_type = report.get("type", "pdf")
        
        # Extract base report ID from composite ID (e.g., "abc123_pdf" -> "abc123")
        base_report_id = report_id.replace("_pdf", "").replace("_csv", "")
        
        # Construct file path
        file_extension = "pdf" if report_type == "pdf" else "csv"
        file_path = f"uploads/reports/{base_report_id}.{file_extension}"
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"[REPORT_DOWNLOAD] File not found: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report file not found on disk. Please regenerate the report."
            )
        
        # Determine media type
        media_type = "application/pdf" if report_type == "pdf" else "text/csv"
        
        # Generate download filename
        report_name = report.get("name", f"report_{base_report_id}")
        # Clean filename for download
        safe_filename = "".join(c for c in report_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        download_filename = f"{safe_filename}.{file_extension}"
        
        logger.info(f"[REPORT_DOWNLOAD] Serving file: {file_path} as {download_filename}")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=download_filename,
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"'
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while downloading the report: {str(e)}"
        )
