from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
import logging

from ..core.security import SecurityManager

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_lti_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current LTI user from JWT token.
    
    Returns:
        Dict containing user information from the LTI launch
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = SecurityManager.verify_token(credentials.credentials)
        
        required_fields = ['user_id', 'resource_link_id']
        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token missing required field: {field}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return payload
        
    except HTTPException:

        raise
    except Exception as e:
        logger.error(f"Error validating user token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def require_instructor(
    current_user: Dict[str, Any] = Depends(get_current_lti_user)
) -> Dict[str, Any]:
    """
    Dependency that requires the user to have instructor privileges.
    
    Returns:
        Dict containing user information (if user is instructor)
        
    Raises:
        HTTPException: If user is not an instructor
    """
    if not current_user.get('is_instructor', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor privileges required"
        )
    
    return current_user

async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_lti_user)
) -> Dict[str, Any]:
    """
    Dependency that requires the user to have administrator privileges.
    
    Returns:
        Dict containing user information (if user is admin)
        
    Raises:
        HTTPException: If user is not an administrator
    """
    user_roles = current_user.get('roles', [])
    
    if 'Administrator' not in user_roles and not current_user.get('is_instructor', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    
    return current_user

def validate_resource_access(resource_link_id: str):
    """
    Dependency factory to validate access to a specific resource.
    
    Args:
        resource_link_id: The resource link ID to validate against
        
    Returns:
        Function that validates user has access to the resource
    """
    async def _validate_access(
        current_user: Dict[str, Any] = Depends(get_current_lti_user)
    ) -> Dict[str, Any]:
        
        if current_user.get('resource_link_id') != resource_link_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this resource"
            )
        
        return current_user
    
    return _validate_access
