from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ...models.lti import UserProgress, GradePassbackRequest
from ...core.security import SecurityManager
from ...services.grade_service import LTIOutcomesService
from ...core.config import settings
from ..dependencies import get_current_lti_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tool", tags=["tool"])

@router.post("/save-progress")
async def save_user_progress(
    progress_data: Dict[str, Any],
    current_user = Depends(get_current_lti_user)
):
    """Save user's progress on activities"""
    
    logger.info(f"Saving progress for user {current_user['user_id']}: {progress_data}")
    
    progress = UserProgress(
        user_id=current_user['user_id'],
        resource_link_id=current_user['resource_link_id'],
        activity_id=progress_data.get('activity_id', 'unknown'),
        progress_percentage=progress_data.get('progress_percentage', 0.0),
        status=progress_data.get('status', 'in_progress'),
        score=progress_data.get('score'),
        attempts=progress_data.get('attempts', 0),
        time_spent=progress_data.get('time_spent', 0),
        last_accessed=datetime.utcnow(),
        completed_at=datetime.utcnow() if progress_data.get('status') == 'completed' else None,
        data=progress_data.get('data', {})
    )
    
    return {
        "status": "success",
        "message": "Progress saved successfully",
        "progress": progress.dict()
    }

@router.post("/submit-grade")
async def submit_grade_to_lms(
    grade_request: GradePassbackRequest,
    current_user = Depends(get_current_lti_user)
):
    """Submit grade back to Moodle using LTI Outcomes Service"""
    
    outcomes_url = current_user.get('lis_outcome_service_url')
    sourcedid = current_user.get('lis_result_sourcedid')
    
    if not outcomes_url or not sourcedid:
        return {
            "status": "warning",
            "message": "Grade passback not available for this launch",
            "supports_grading": False
        }
    
    try:
        outcomes_service = LTIOutcomesService(
            consumer_key=settings.LTI_CONSUMER_KEY,
            consumer_secret=settings.LTI_SHARED_SECRET
        )
        
        result = outcomes_service.send_grade(
            outcomes_url=outcomes_url,
            sourcedid=sourcedid,
            grade=grade_request.grade,
            message_identifier=f"grade_{current_user['user_id']}_{datetime.utcnow().timestamp()}"
        )
        
        if result["success"]:
            logger.info(f"Grade {grade_request.grade} submitted successfully for user {current_user['user_id']}")
            return {
                "status": "success",
                "message": "Grade submitted to LMS successfully",
                "grade": grade_request.grade,
                "supports_grading": True
            }
        else:
            logger.error(f"Grade submission failed: {result}")
            return {
                "status": "error",
                "message": f"Failed to submit grade: {result.get('error', 'Unknown error')}",
                "supports_grading": True
            }
            
    except Exception as e:
        logger.error(f"Error submitting grade: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting grade: {str(e)}"
        )

@router.get("/progress")
async def get_user_progress(
    current_user = Depends(get_current_lti_user)
) -> List[Dict[str, Any]]:
    """Get user's progress across all activities"""
    
    mock_progress = [
        {
            "activity_id": "quiz_1",
            "activity_name": "Introduction Quiz",
            "activity_type": "quiz",
            "progress_percentage": 100.0,
            "status": "completed",
            "score": 0.85,
            "attempts": 2,
            "time_spent": 420,  # seconds
            "last_accessed": "2024-01-15T10:30:00Z",
            "completed_at": "2024-01-15T10:37:00Z"
        },
        {
            "activity_id": "assignment_1",
            "activity_name": "Essay Assignment",
            "activity_type": "assignment",
            "progress_percentage": 75.0,
            "status": "in_progress",
            "score": None,
            "attempts": 1,
            "time_spent": 1800,
            "last_accessed": "2024-01-16T14:20:00Z",
            "completed_at": None
        },
        {
            "activity_id": "reading_1",
            "activity_name": "Chapter 1 Reading",
            "activity_type": "reading",
            "progress_percentage": 60.0,
            "status": "in_progress",
            "score": None,
            "attempts": 1,
            "time_spent": 900,
            "last_accessed": "2024-01-16T09:15:00Z",
            "completed_at": None
        }
    ]
    
    return mock_progress

@router.get("/activities")
async def get_available_activities(
    current_user = Depends(get_current_lti_user)
) -> List[Dict[str, Any]]:
    """Get list of available activities for the user"""
    
    activities = [
        {
            "id": "quiz_1",
            "name": "Introduction Quiz",
            "type": "quiz",
            "description": "Test your knowledge with this interactive quiz",
            "duration_minutes": 15,
            "max_attempts": 3,
            "available": True,
            "required": True
        },
        {
            "id": "assignment_1", 
            "name": "Essay Assignment",
            "type": "assignment",
            "description": "Write a 500-word essay on the topic",
            "duration_minutes": 60,
            "max_attempts": 1,
            "available": True,
            "required": True
        },
        {
            "id": "reading_1",
            "name": "Chapter 1 Reading",
            "type": "reading",
            "description": "Read and understand the first chapter",
            "duration_minutes": 30,
            "max_attempts": None,
            "available": True,
            "required": False
        }
    ]
    
    if not current_user.get('is_instructor', False):
        return activities
    else:
        activities.append({
            "id": "grade_management",
            "name": "Grade Management",
            "type": "management",
            "description": "Manage student grades and progress",
            "duration_minutes": None,
            "max_attempts": None,
            "available": True,
            "required": False
        })
        return activities

@router.get("/student-progress")
async def get_all_student_progress(
    current_user = Depends(get_current_lti_user)
):
    """Get progress for all students (instructor only)"""
    
    if not current_user.get('is_instructor', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can view all student progress"
        )
    
    student_progress = [
        {
            "user_id": "student_001",
            "name": "John Doe",
            "email": "john.doe@university.edu",
            "overall_progress": 85.0,
            "activities": [
                {"activity_id": "quiz_1", "score": 0.9, "completed": True},
                {"activity_id": "assignment_1", "score": 0.8, "completed": True},
                {"activity_id": "reading_1", "score": None, "completed": False}
            ]
        },
        {
            "user_id": "student_002", 
            "name": "Jane Smith",
            "email": "jane.smith@university.edu",
            "overall_progress": 92.0,
            "activities": [
                {"activity_id": "quiz_1", "score": 0.95, "completed": True},
                {"activity_id": "assignment_1", "score": 0.89, "completed": True},
                {"activity_id": "reading_1", "score": None, "completed": True}
            ]
        }
    ]
    
    return student_progress

@router.post("/bulk-grade-submission")
async def submit_bulk_grades(
    grade_submissions: List[Dict[str, Any]],
    current_user = Depends(get_current_lti_user)
):
    """Submit grades for multiple students (instructor only)"""
    
    if not current_user.get('is_instructor', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can submit bulk grades"
        )
    
    results = []
    
    for submission in grade_submissions:
        try:
            logger.info(f"Bulk grade submission: {submission}")
            
            results.append({
                "user_id": submission.get("user_id"),
                "grade": submission.get("grade"),
                "status": "success",
                "message": "Grade submitted successfully"
            })
            
        except Exception as e:
            results.append({
                "user_id": submission.get("user_id"),
                "grade": submission.get("grade"),
                "status": "error",
                "message": str(e)
            })
    
    return {
        "status": "completed",
        "results": results,
        "successful_submissions": len([r for r in results if r["status"] == "success"]),
        "failed_submissions": len([r for r in results if r["status"] == "error"])
    }
