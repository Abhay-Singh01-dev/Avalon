from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from app.db.mongo import get_database

router = APIRouter(tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_admin_stats():
    """
    Get application statistics (no authentication required).
    """
    try:
        db = get_database()
        
        # Count documents in collections
        chats_count = await db.conversations.count_documents({})
        messages_count = await db.messages.count_documents({})
        projects_count = await db.projects.count_documents({})
        reports_count = await db.reports.count_documents({})
        
        return {
            "conversations": chats_count,
            "messages": messages_count,
            "projects": projects_count,
            "reports": reports_count,
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving stats: {str(e)}"
        )

