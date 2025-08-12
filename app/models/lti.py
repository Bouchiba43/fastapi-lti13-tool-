from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LTIRole(str, Enum):
    """LTI 1.3 Role enumeration"""
    ADMINISTRATOR = "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator"
    INSTRUCTOR = "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"
    LEARNER = "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
    TEACHING_ASSISTANT = "http://purl.imsglobal.org/vocab/lis/v2/membership/Instructor#TeachingAssistant"
    CONTENT_DEVELOPER = "http://purl.imsglobal.org/vocab/lis/v2/membership#ContentDeveloper"
    MENTOR = "http://purl.imsglobal.org/vocab/lis/v2/membership#Mentor"
    MEMBER = "http://purl.imsglobal.org/vocab/lis/v2/membership#Member"

class LTI13MessageType(str, Enum):
    """LTI 1.3 Message Types"""
    RESOURCE_LINK_REQUEST = "LtiResourceLinkRequest"
    DEEP_LINKING_REQUEST = "LtiDeepLinkingRequest"
    SUBMISSION_REVIEW_REQUEST = "LtiSubmissionReviewRequest"

class LTI13User(BaseModel):
    """LTI 1.3 User Model"""
    user_id: str = Field(..., description="Platform user ID (sub)")
    name: Optional[str] = Field(None, description="User's full name")
    given_name: Optional[str] = Field(None, description="User's given name")
    family_name: Optional[str] = Field(None, description="User's family name")
    email: Optional[str] = Field(None, description="User's email address")
    picture: Optional[str] = Field(None, description="User's profile picture URL")
    
    roles: List[LTIRole] = Field(default_factory=list, description="User's roles in the context")
    
    context_id: Optional[str] = Field(None, description="Context (course) ID")
    context_title: Optional[str] = Field(None, description="Context (course) title")
    context_label: Optional[str] = Field(None, description="Context (course) label")
    
    resource_link_id: str = Field(..., description="Resource link ID")
    resource_link_title: Optional[str] = Field(None, description="Resource link title")
    
    platform_name: Optional[str] = Field(None, description="Platform name")
    
    launch_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the launch occurred")
    deployment_id: str = Field(..., description="LTI deployment ID")
    message_type: LTI13MessageType = Field(default=LTI13MessageType.RESOURCE_LINK_REQUEST)
    
    custom_parameters: Dict[str, Any] = Field(default_factory=dict, description="Custom parameters from launch")

class LTI13Grade(BaseModel):
    """LTI 1.3 Grade Model for Assignment and Grade Service"""
    scoreGiven: Optional[float] = Field(None, description="Score given to the user")
    scoreMaximum: Optional[float] = Field(None, description="Maximum possible score")
    comment: Optional[str] = Field(None, description="Comment about the grade")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the grade was recorded")
    activityProgress: Optional[str] = Field(None, description="Activity progress status")
    gradingProgress: Optional[str] = Field(None, description="Grading progress status")
    userId: str = Field(..., description="User ID receiving the grade")

class LTI13Progress(BaseModel):
    """LTI 1.3 Progress Model"""
    user_id: str = Field(..., description="User ID")
    resource_link_id: str = Field(..., description="Resource link ID")
    progress_data: Dict[str, Any] = Field(default_factory=dict, description="Progress data")
    completion_status: str = Field(default="in_progress", description="Completion status")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access time")

class LTI13Context(BaseModel):
    """LTI 1.3 Context (Course) Model"""
    id: str = Field(..., description="Context ID")
    label: Optional[str] = Field(None, description="Context label")
    title: Optional[str] = Field(None, description="Context title")
    type: Optional[List[str]] = Field(None, description="Context types")

class LTI13ResourceLink(BaseModel):
    """LTI 1.3 Resource Link Model"""
    id: str = Field(..., description="Resource link ID")
    title: Optional[str] = Field(None, description="Resource link title")
    description: Optional[str] = Field(None, description="Resource link description")

class LTI13DeepLinkingSettings(BaseModel):
    """LTI 1.3 Deep Linking Settings"""
    deep_link_return_url: str = Field(..., description="URL to return to after deep linking")
    accept_types: List[str] = Field(..., description="Accepted content types")
    accept_presentation_document_targets: List[str] = Field(..., description="Accepted presentation targets")
    accept_media_types: Optional[str] = Field(None, description="Accepted media types")
    auto_create: Optional[bool] = Field(None, description="Auto-create flag")
    title: Optional[str] = Field(None, description="Title for the deep linking")
    text: Optional[str] = Field(None, description="Text for the deep linking")
    data: Optional[str] = Field(None, description="Custom data")


# Bouchiba43 i have removed the lti 1.0/1.1 so no need for below models maybe i will add it in the future if needed

class LTIUser(BaseModel):
    """Legacy LTI 1.1 User Model (for backward compatibility)"""
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    context_id: Optional[str] = None
    context_title: Optional[str] = None
    resource_link_id: str
    launch_timestamp: datetime = Field(default_factory=datetime.utcnow)

class LTIGrade(BaseModel):
    """Legacy LTI 1.1 Grade Model (for backward compatibility)"""
    user_id: str
    score: float
    max_score: float
    comment: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LTIProgress(BaseModel):
    """Legacy LTI 1.1 Progress Model (for backward compatibility)"""
    user_id: str
    resource_link_id: str
    progress_data: Dict[str, Any] = Field(default_factory=dict)
    completion_status: str = "in_progress"
    last_accessed: datetime = Field(default_factory=datetime.utcnow)


class UserProgress(BaseModel):
    """User Progress Model"""
    user_id: str
    resource_link_id: str
    progress_data: Dict[str, Any] = Field(default_factory=dict)
    completion_status: str = "in_progress"
    last_accessed: datetime = Field(default_factory=datetime.utcnow)

class GradePassbackRequest(BaseModel):
    """Grade Passback Request Model"""
    user_id: str
    score: float
    max_score: float = 100.0
    comment: Optional[str] = None
    activity_id: Optional[str] = None
