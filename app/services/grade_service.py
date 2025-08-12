import xml.etree.ElementTree as ET
import requests
import hashlib
import hmac
import base64
import urllib.parse
import time
import uuid
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class LTIOutcomesService:
    """LTI Basic Outcomes Service for grade passback"""
    
    def __init__(self, consumer_key: str, consumer_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
    
    def send_grade(
        self,
        outcomes_url: str,
        sourcedid: str,
        grade: float,
        message_identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send grade back to LMS using LTI Basic Outcomes Service"""
        
        if not message_identifier:
            message_identifier = str(uuid.uuid4())
        
        xml_payload = self._create_outcomes_xml(sourcedid, grade, message_identifier)
        
        oauth_params = self._create_oauth_params()
        signature = self._generate_outcomes_signature(
            "POST", outcomes_url, xml_payload, oauth_params
        )
        oauth_params['oauth_signature'] = signature
        
        auth_header = self._create_auth_header(oauth_params)
        
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/xml',
            'User-Agent': 'FastAPI-LTI-Tool/1.0'
        }
        
        try:
            response = requests.post(
                outcomes_url,
                data=xml_payload,
                headers=headers,
                timeout=30
            )
            
            return self._parse_outcomes_response(response)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending grade: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": "REQUEST_ERROR"
            }
    
    def _create_outcomes_xml(self, sourcedid: str, grade: float, message_identifier: str) -> str:
        """Create XML payload for outcomes service"""
        
        xml_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
    <imsx_POXHeader>
        <imsx_POXRequestHeaderInfo>
            <imsx_version>V1.0</imsx_version>
            <imsx_messageIdentifier>{message_identifier}</imsx_messageIdentifier>
        </imsx_POXRequestHeaderInfo>
    </imsx_POXHeader>
    <imsx_POXBody>
        <replaceResultRequest>
            <resultRecord>
                <sourcedGUID>
                    <sourcedId>{sourcedid}</sourcedId>
                </sourcedGUID>
                <result>
                    <resultScore>
                        <language>en</language>
                        <textString>{grade}</textString>
                    </resultScore>
                </result>
            </resultRecord>
        </replaceResultRequest>
    </imsx_POXBody>
</imsx_POXEnvelopeRequest>'''
        
        return xml_template
    
    def _create_oauth_params(self) -> Dict[str, str]:
        """Create OAuth parameters"""
        return {
            'oauth_consumer_key': self.consumer_key,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': str(uuid.uuid4()),
            'oauth_version': '1.0',
            'oauth_body_hash': ''
        }
    
    def _generate_outcomes_signature(
        self, 
        method: str, 
        url: str, 
        body: str, 
        oauth_params: Dict[str, str]
    ) -> str:
        """Generate OAuth signature for outcomes request"""
        
        body_hash = base64.b64encode(hashlib.sha1(body.encode('utf-8')).digest()).decode('utf-8')
        oauth_params['oauth_body_hash'] = body_hash
        
        encoded_params = []
        for key, value in sorted(oauth_params.items()):
            encoded_key = urllib.parse.quote_plus(str(key))
            encoded_value = urllib.parse.quote_plus(str(value))
            encoded_params.append(f"{encoded_key}={encoded_value}")
        
        parameter_string = "&".join(encoded_params)
        
        base_string_parts = [
            method.upper(),
            urllib.parse.quote_plus(url),
            urllib.parse.quote_plus(parameter_string)
        ]
        signature_base = "&".join(base_string_parts)
        
        signing_key = f"{urllib.parse.quote_plus(self.consumer_secret)}&"
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode('utf-8'),
                signature_base.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return signature
    
    def _create_auth_header(self, oauth_params: Dict[str, str]) -> str:
        """Create OAuth Authorization header"""
        auth_parts = []
        for key, value in sorted(oauth_params.items()):
            encoded_key = urllib.parse.quote_plus(key)
            encoded_value = urllib.parse.quote_plus(value)
            auth_parts.append(f'{encoded_key}="{encoded_value}"')
        
        return f"OAuth {', '.join(auth_parts)}"
    
    def _parse_outcomes_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse LTI Outcomes service response"""
        
        result = {
            "success": False,
            "status_code": response.status_code,
            "response_body": response.text
        }
        
        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            result["code"] = "HTTP_ERROR"
            return result
        
        try:
            root = ET.fromstring(response.text)
            
            status_info = root.find('.//{http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0}imsx_statusInfo')
            
            if status_info is not None:
                code_major = status_info.find('.//{http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0}imsx_codeMajor')
                severity = status_info.find('.//{http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0}imsx_severity')
                description = status_info.find('.//{http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0}imsx_description')
                
                result["code_major"] = code_major.text if code_major is not None else "unknown"
                result["severity"] = severity.text if severity is not None else "unknown"
                result["description"] = description.text if description is not None else "No description"
                
                result["success"] = result["code_major"].lower() == "success"
            
        except ET.ParseError as e:
            result["error"] = f"XML Parse Error: {e}"
            result["code"] = "XML_PARSE_ERROR"
        
        return result