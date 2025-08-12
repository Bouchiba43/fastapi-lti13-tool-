import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.config import settings
from ..core.lti13_validator import lti13_validator
from ..models.lti import LTI13Grade

logger = logging.getLogger(__name__)

class LTI13GradeService:
    """LTI 1.3 Assignment and Grade Service (AGS) implementation"""
    
    def __init__(self):
        self.service_url = None
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self, ags_claim: Dict[str, Any]) -> str:
        """Get access token for AGS service"""
        
        if self.access_token and self.token_expiry:
            if datetime.utcnow().timestamp() < self.token_expiry:
                return self.access_token
        
        token_url = settings.LTI_PLATFORM_TOKEN_URL
        
        client_assertion_payload = {
            'iss': settings.LTI_CLIENT_ID,
            'sub': settings.LTI_CLIENT_ID,
            'aud': token_url,
            'jti': f"lti-service-token-{int(datetime.utcnow().timestamp())}"
        }
        
        try:
            client_assertion = lti13_validator.create_tool_jwt(client_assertion_payload)
            
            token_data = {
                'grant_type': 'client_credentials',
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': client_assertion,
                'scope': 'https://purl.imsglobal.org/spec/lti-ags/scope/score'
            }
            
            response = requests.post(
                token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            response.raise_for_status()
            token_response = response.json()
            
            self.access_token = token_response['access_token']
            self.token_expiry = datetime.utcnow().timestamp() + token_response.get('expires_in', 3600)
            
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get AGS access token: {e}")
            raise ValueError(f"Token request failed: {e}")
    
    def submit_grade(
        self, 
        user_id: str,
        score_given: float,
        score_maximum: float,
        ags_claim: Dict[str, Any],
        comment: Optional[str] = None,
        activity_progress: str = "Completed",
        grading_progress: str = "FullyGraded"
    ) -> bool:
        """Submit grade using LTI 1.3 AGS"""
        
        try:
            access_token = self.get_access_token(ags_claim)
            
            lineitems_url = ags_claim.get('lineitems')
            if not lineitems_url:
                logger.error("No lineitems URL in AGS claim")
                return False
            
            scores_url = f"{lineitems_url.rstrip('/')}/scores"
            
            score_data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "scoreGiven": score_given,
                "scoreMaximum": score_maximum,
                "userId": user_id,
                "activityProgress": activity_progress,
                "gradingProgress": grading_progress
            }
            
            if comment:
                score_data["comment"] = comment
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/vnd.ims.lis.v1.score+json'
            }
            
            logger.info(f"Submitting grade to: {scores_url}")
            logger.info(f"Score data: {json.dumps(score_data, indent=2)}")
            
            response = requests.post(
                scores_url,
                json=score_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Grade submitted successfully for user {user_id}")
                return True
            else:
                logger.error(f"Grade submission failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting grade: {e}")
            return False
    
    def get_lineitem(self, ags_claim: Dict[str, Any], lineitem_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get lineitem information from AGS"""
        
        try:
            access_token = self.get_access_token(ags_claim)
            
            lineitems_url = ags_claim.get('lineitems')
            if not lineitems_url:
                return None
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/vnd.ims.lis.v2.lineitem+json'
            }
            
            if lineitem_id:
                url = f"{lineitems_url}/{lineitem_id}"
            else:
                url = lineitems_url
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting lineitem: {e}")
            return None
    
    def create_lineitem(
        self, 
        ags_claim: Dict[str, Any],
        label: str,
        score_maximum: float,
        resource_id: Optional[str] = None,
        tag: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new lineitem in the gradebook"""
        
        try:
            access_token = self.get_access_token(ags_claim)
            
            lineitems_url = ags_claim.get('lineitems')
            if not lineitems_url:
                return None
            
            lineitem_data = {
                "scoreMaximum": score_maximum,
                "label": label
            }
            
            if resource_id:
                lineitem_data["resourceId"] = resource_id
            
            if tag:
                lineitem_data["tag"] = tag
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/vnd.ims.lis.v2.lineitem+json'
            }
            
            response = requests.post(
                lineitems_url,
                json=lineitem_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Lineitem creation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating lineitem: {e}")
            return None

lti13_grade_service = LTI13GradeService()
