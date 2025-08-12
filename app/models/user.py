from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"

class User(BaseModel):
    id: Optional[str] = None
    lti_user_id: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT
    context_id: Optional[str] = None
    resource_link_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: bool = True

class UserSession(BaseModel):
    session_id: str
    user_id: str
    lti_user_id: str
    context_id: Optional[str] = None
    resource_link_id: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
