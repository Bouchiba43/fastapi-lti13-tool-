from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from ...models.lti import LTIUser, UserProgress
from ...models.user import User
from ..dependencies import get_current_lti_user, require_instructor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_lti_user)
) -> Dict[str, Any]:
    """Get current user information"""
    return current_user

@router.get("/progress")
async def get_user_progress(
    current_user: Dict[str, Any] = Depends(get_current_lti_user)
) -> List[Dict[str, Any]]:
    """Get user's progress across all activities"""
    
    mock_progress = [
        {
            "user_id": current_user['user_id'],
            "resource_link_id": current_user['resource_link_id'],
            "activity_id": "quiz_1",
            "activity_type": "quiz",
            "progress_percentage": 100.0,
            "status": "completed",
            "score": 0.85,
            "attempts": 2,
            "time_spent": 420, 
            "last_accessed": "2024-01-15T10:30:00Z",
            "completed_at": "2024-01-15T10:37:00Z"
        },
        {
            "user_id": current_user['user_id'],
            "resource_link_id": current_user['resource_link_id'],
            "activity_id": "assignment_1",
            "activity_type": "assignment",
            "progress_percentage": 60.0,
            "status": "in_progress",
            "score": None,
            "attempts": 1,
            "time_spent": 1200,
            "last_accessed": "2024-01-16T09:15:00Z",
            "completed_at": None
        }
    ]
    
    return mock_progress

@router.put("/preferences")
async def update_user_preferences(
    preferences: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_lti_user)
):
    """Update user preferences"""
    
    logger.info(f"Updating preferences for user {current_user['user_id']}: {preferences}")
    
    return {
        "status": "success",
        "message": "Preferences updated successfully",
        "preferences": preferences
    }

@router.get("/profile")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_lti_user)
):
    """Get detailed user profile"""
    
    profile = {
        "user_id": current_user['user_id'],
        "full_name": current_user.get('full_name'),
        "email": current_user.get('email'),
        "roles": current_user.get('roles', []),
        "is_instructor": current_user.get('is_instructor', False),
        "context_id": current_user.get('context_id'),
        "context_title": current_user.get('context_title'),
        "resource_link_id": current_user.get('resource_link_id'),
        "launch_timestamp": current_user.get('iat'),
        "token_expires": current_user.get('exp'),
        "statistics": {
            "total_activities": 3,
            "completed_activities": 1,
            "in_progress_activities": 2,
            "average_score": 0.85,
            "total_time_spent": 1620  
        }
    }
    
    return profile
            