import jwt
import json
import time
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from .config import settings

logger = logging.getLogger(__name__)

class LTI13Validator:
    """LTI 1.3 JWT validator and message handler"""
    
    def __init__(self):
        self.platform_jwks_cache = {}
        self.cache_expiry = 3600  
    
    @staticmethod
    def generate_key_pair():
        """Generate RSA key pair for JWT signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode('utf-8'), public_pem.decode('utf-8')
    
    def get_platform_jwks(self, platform_issuer: str) -> Dict[str, Any]:
        """Fetch and cache platform JWKS"""
        
        if platform_issuer in self.platform_jwks_cache:
            cached_data = self.platform_jwks_cache[platform_issuer]
            if time.time() - cached_data['timestamp'] < self.cache_expiry:
                return cached_data['jwks']
        
        if 'moodle' in platform_issuer.lower() or platform_issuer == settings.LTI_PLATFORM_ISSUER:
            jwks_url = settings.LTI_PLATFORM_JWKS_URL
        else:

            jwks_url = f"{platform_issuer}/.well-known/jwks.json"
        
        try:
            logger.info(f"Fetching JWKS from: {jwks_url}")
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()
            
            jwks = response.json()
            
            self.platform_jwks_cache[platform_issuer] = {
                'jwks': jwks,
                'timestamp': time.time()
            }
            
            return jwks
            
        except Exception as e:
            logger.error(f"Failed to fetch JWKS from {jwks_url}: {e}")
            return {"keys": []}
    
    def validate_jwt_token(self, token: str, audience: str = None) -> Dict[str, Any]:
        """Validate LTI 1.3 JWT token"""
        
        try:
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            logger.info(f"JWT Header: {header}")
            logger.info(f"JWT Payload (unverified): {json.dumps(payload, indent=2)}")
            
            if 'iss' not in payload:
                raise ValueError("Missing issuer (iss) in JWT")
            
            if 'aud' not in payload:
                raise ValueError("Missing audience (aud) in JWT")
            
            platform_issuer = payload['iss']
            jwks = self.get_platform_jwks(platform_issuer)
            
            if not jwks.get('keys'):
                logger.warning("No JWKS keys found, skipping signature verification for development")
                if settings.DEBUG:
                    logger.warning("DEBUG MODE: Skipping JWT signature verification")
                    return {
                        "valid": True,
                        "payload": payload,
                        "warnings": ["Signature verification skipped in debug mode"]
                    }
                else:
                    raise ValueError("No public keys available for signature verification")
            
            kid = header.get('kid')
            public_key = None
            
            for key_data in jwks['keys']:
                if kid and key_data.get('kid') == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
                    break
                elif not kid and key_data.get('use') == 'sig':
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
                    break
            
            if not public_key:
                raise ValueError(f"No matching public key found for kid: {kid}")
            
            verified_payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=audience or settings.LTI_CLIENT_ID,
                issuer=platform_issuer
            )
            
            return {
                "valid": True,
                "payload": verified_payload,
                "warnings": []
            }
            
        except jwt.ExpiredSignatureError:
            logger.error("JWT token has expired")
            return {"valid": False, "error": "Token expired"}
            
        except jwt.InvalidAudienceError as e:
            logger.error(f"Invalid audience: {e}")
            return {"valid": False, "error": f"Invalid audience: {e}"}
            
        except jwt.InvalidIssuerError as e:
            logger.error(f"Invalid issuer: {e}")
            return {"valid": False, "error": f"Invalid issuer: {e}"}
            
        except jwt.InvalidSignatureError:
            logger.error("JWT signature verification failed")
            return {"valid": False, "error": "Invalid signature"}
            
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return {"valid": False, "error": str(e)}
    
    def validate_lti_message(self, jwt_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate LTI 1.3 message content"""
        
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        required_claims = [
            'iss',  # Issuer
            'aud',  # Audience
            'exp',  # Expiration
            'iat',  # Issued at
            'nonce',  # Nonce
            'https://purl.imsglobal.org/spec/lti/claim/message_type',
            'https://purl.imsglobal.org/spec/lti/claim/version',
            'https://purl.imsglobal.org/spec/lti/claim/deployment_id'
        ]
        
        missing_claims = [claim for claim in required_claims if claim not in jwt_payload]
        if missing_claims:
            validation_result["errors"].append(f"Missing required claims: {missing_claims}")
        
        lti_version = jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/version')
        if lti_version != '1.3.0':
            validation_result["warnings"].append(f"LTI version {lti_version} may not be fully supported")
        
        message_type = jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/message_type')
        supported_types = [
            'LtiResourceLinkRequest',
            'LtiDeepLinkingRequest',
            'LtiSubmissionReviewRequest'
        ]
        
        if message_type not in supported_types:
            validation_result["warnings"].append(f"Message type {message_type} may not be fully supported")
        
        deployment_id = jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/deployment_id')
        if deployment_id != settings.LTI_DEPLOYMENT_ID:
            validation_result["errors"].append(f"Invalid deployment ID: {deployment_id}")
        
        target_link_uri = jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/target_link_uri')
        if target_link_uri and not target_link_uri.startswith(settings.LTI_TOOL_URL):
            validation_result["warnings"].append(f"Target link URI doesn't match tool URL: {target_link_uri}")
        
        current_time = int(time.time())
        exp = jwt_payload.get('exp', 0)
        iat = jwt_payload.get('iat', 0)
        
        if exp < current_time:
            validation_result["errors"].append("Token has expired")
        
        if iat > current_time + 60: 
            validation_result["errors"].append("Token issued in the future")
        
        validation_result["valid"] = len(validation_result["errors"]) == 0
        
        return validation_result
    
    def create_tool_jwt(self, payload: Dict[str, Any]) -> str:
        """Create JWT token signed by the tool's private key"""

        current_time = int(time.time())
        payload.update({
            'iss': settings.LTI_TOOL_URL,
            'aud': settings.LTI_PLATFORM_ISSUER,
            'iat': current_time,
            'exp': current_time + 3600,  # 1 hour expiration
        })
        
        try:
            with open(settings.LTI_PRIVATE_KEY_PATH, 'r') as f:
                private_key_pem = f.read()
            
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            
            token = jwt.encode(
                payload,
                private_key,
                algorithm='RS256',
                headers={'kid': settings.LTI_KEY_ID}
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to create JWT: {e}")
            raise ValueError(f"JWT creation failed: {e}")

lti13_validator = LTI13Validator()
