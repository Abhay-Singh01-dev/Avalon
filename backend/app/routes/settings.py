from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.db.mongo import get_database

router = APIRouter(tags=["Settings"])
logger = logging.getLogger(__name__)

SETTINGS_COLLECTION = "settings"
DEFAULT_USER_ID = "default"  # Since no auth, use a single default user


@router.get("")
async def get_settings():
    """
    Get settings (open access, no authentication).
    """
    try:
        db = get_database()
        settings_collection = db[SETTINGS_COLLECTION]
        
        # Get or create settings for the default user
        settings = await settings_collection.find_one({"user_id": DEFAULT_USER_ID})
        
        if not settings:
            # Return default settings
            return {
                "agentPersona": None,
                "responseStyle": None,
                "focusAreas": {},
                "dataSources": {}
            }
        
        # Return settings without MongoDB _id
        result = {
            "agentPersona": settings.get("agentPersona"),
            "responseStyle": settings.get("responseStyle"),
            "focusAreas": settings.get("focusAreas", {}),
            "dataSources": settings.get("dataSources", {})
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving settings: {str(e)}"
        )


@router.patch("")
async def update_settings(payload: Dict[str, Any]):
    """
    Update settings (open access, no authentication).
    """
    try:
        db = get_database()
        settings_collection = db[SETTINGS_COLLECTION]
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        if "agentPersona" in payload:
            update_data["agentPersona"] = payload["agentPersona"]
        if "responseStyle" in payload:
            update_data["responseStyle"] = payload["responseStyle"]
        if "focusAreas" in payload:
            update_data["focusAreas"] = payload["focusAreas"]
        if "dataSources" in payload:
            update_data["dataSources"] = payload["dataSources"]
        
        # Upsert settings
        result = await settings_collection.update_one(
            {"user_id": DEFAULT_USER_ID},
            {
                "$set": update_data,
                "$setOnInsert": {
                    "user_id": DEFAULT_USER_ID,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        return {
            "status": "success",
            "message": "Settings updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating settings: {str(e)}"
        )

