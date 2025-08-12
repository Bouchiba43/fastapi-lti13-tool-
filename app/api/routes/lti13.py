from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json
import urllib.parse

from ...core.config import settings
from ...core.lti13_validator import lti13_validator
from ...models.lti import LTI13User, LTI13MessageType, LTIRole
from ...services.lti13_grade_service import lti13_grade_service

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/lti", tags=["lti13"])

@router.get("/jwks")
async def get_jwks():
    """Provide tool's public key set (JWKS) for platforms"""
    try:
        with open(settings.LTI_PUBLIC_KEY_PATH, 'r') as f:
            public_key_pem = f.read()
        
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        import jwt
        
        public_key = load_pem_public_key(public_key_pem.encode('utf-8'))
        
        public_numbers = public_key.public_numbers()
        
        jwk = jwt.algorithms.RSAAlgorithm.to_jwk(public_key)
        jwk_dict = json.loads(jwk)
        jwk_dict['kid'] = settings.LTI_KEY_ID
        jwk_dict['use'] = 'sig'
        jwk_dict['alg'] = 'RS256'
        
        jwks = {
            "keys": [jwk_dict]
        }
        
        return jwks
        
    except Exception as e:
        logger.error(f"Failed to generate JWKS: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate JWKS")

@router.get("/config")
async def get_lti13_config():
    """LTI 1.3 Configuration JSON for tool registration"""
    config = {
        "title": settings.LTI_TOOL_NAME,
        "description": settings.LTI_DESCRIPTION,
        "oidc_initiation_url": settings.LTI_LOGIN_URL,
        "target_link_uri": settings.LTI_LAUNCH_URL,
        "scopes": [
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
        ],
        "extensions": [
            {
                "domain": settings.LTI_TOOL_URL.replace("http://", "").replace("https://", ""),
                "tool_id": "fastapi_lti13_tool",
                "platform": "moodle.org",
                "privacy_level": "public",
                "settings": {
                    "placements": [
                        {
                            "placement": "course_navigation",
                            "message_type": "LtiResourceLinkRequest",
                            "target_link_uri": settings.LTI_LAUNCH_URL
                        }
                    ]
                }
            }
        ],
        "public_jwk_url": settings.LTI_JWKS_URL,
        "custom_fields": {}
    }
    
    return config

@router.get("/login", response_class=HTMLResponse)
@router.post("/login", response_class=HTMLResponse)
async def oidc_login(request: Request):
    """OIDC Login Initiation (Step 1 of LTI 1.3 launch)"""

    if request.method == "GET":
        params = dict(request.query_params)
    else:
        form_data = await request.form()
        params = dict(form_data)
    
    logger.info(f"OIDC Login initiated from {request.client.host}")
    logger.info(f"Login parameters: {params}")
    
    required_params = ['iss', 'login_hint', 'target_link_uri']
    missing_params = [p for p in required_params if p not in params]
    
    if missing_params:
        logger.error(f"Missing required OIDC parameters: {missing_params}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required parameters: {missing_params}"
        )
    
    if params.get('iss') != settings.LTI_PLATFORM_ISSUER:
        logger.error(f"Invalid issuer: {params.get('iss')}")
        raise HTTPException(status_code=400, detail="Invalid issuer")
    
    import secrets
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
       
    auth_params = {
        'response_type': 'id_token',
        'client_id': settings.LTI_CLIENT_ID,
        'redirect_uri': settings.LTI_LAUNCH_URL,
        'login_hint': params.get('login_hint'),
        'state': state,
        'nonce': nonce,
        'response_mode': 'form_post',
        'scope': 'openid',
        'prompt': 'none'
    }
    
    if 'lti_message_hint' in params:
        auth_params['lti_message_hint'] = params['lti_message_hint']
    
    if 'lti_deployment_id' in params:
        auth_params['lti_deployment_id'] = params['lti_deployment_id']
    
    auth_url = settings.LTI_PLATFORM_AUTH_URL
    query_string = urllib.parse.urlencode(auth_params)
    full_auth_url = f"{auth_url}?{query_string}"
    
    logger.info(f"Redirecting to platform auth: {full_auth_url}")
    
    return RedirectResponse(url=full_auth_url, status_code=302)

@router.post("/launch")
async def lti13_launch(request: Request):
    """Handle LTI 1.3 launch requests (Step 2 - after OIDC auth)"""
    
    form_data = await request.form()
    request_data = dict(form_data)
    
    logger.info(f"LTI 1.3 Launch Request from {request.client.host}")
    logger.info(f"Form data keys: {list(request_data.keys())}")
    
    id_token = request_data.get('id_token')
    if not id_token:
        logger.error("No id_token found in launch request")
        raise HTTPException(status_code=400, detail="Missing id_token")
    
    state = request_data.get('state')
    logger.info(f"Received state: {state}")
    logger.info(f"ID Token (first 50 chars): {id_token[:50]}...")
    
    validation_result = lti13_validator.validate_jwt_token(
        id_token, 
        audience=settings.LTI_CLIENT_ID
    )
    
    if not validation_result["valid"]:
        logger.error(f"JWT validation failed: {validation_result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid JWT token: {validation_result.get('error')}"
        )
    
    jwt_payload = validation_result["payload"]
    
    logger.info(f"JWT Payload received:")
    logger.info(f"  Issuer (iss): {jwt_payload.get('iss')}")
    logger.info(f"  Audience (aud): {jwt_payload.get('aud')}")
    logger.info(f"  Subject (sub): {jwt_payload.get('sub')}")
    logger.info(f"  Deployment ID: {jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/deployment_id')}")
    logger.info(f"  Message Type: {jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/message_type')}")
    
    lti_validation = lti13_validator.validate_lti_message(jwt_payload)
    
    if not lti_validation["valid"]:
        logger.error(f"LTI message validation failed: {lti_validation['errors']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid LTI message: {', '.join(lti_validation['errors'])}"
        )
    
    if lti_validation["warnings"]:
        logger.warning(f"LTI validation warnings: {lti_validation['warnings']}")
    
    user_roles = []
    roles_claim = jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
    
    for role_uri in roles_claim:
        if 'Instructor' in role_uri:
            user_roles.append(LTIRole.INSTRUCTOR)
        elif 'Learner' in role_uri:
            user_roles.append(LTIRole.LEARNER)
        elif 'Administrator' in role_uri:
            user_roles.append(LTIRole.ADMINISTRATOR)
        elif 'TeachingAssistant' in role_uri:
            user_roles.append(LTIRole.TEACHING_ASSISTANT)
        else:
            user_roles.append(LTIRole.MEMBER)
    
    context_claim = jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/context', {})
    resource_link_claim = jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/resource_link', {})
    
    lti_user = LTI13User(
        user_id=jwt_payload.get('sub', 'unknown'),
        name=jwt_payload.get('name'),
        given_name=jwt_payload.get('given_name'),
        family_name=jwt_payload.get('family_name'),
        email=jwt_payload.get('email'),
        picture=jwt_payload.get('picture'),
        roles=user_roles,
        context_id=context_claim.get('id'),
        context_title=context_claim.get('title'),
        context_label=context_claim.get('label'),
        resource_link_id=resource_link_claim.get('id', 'unknown'),
        resource_link_title=resource_link_claim.get('title'),
        deployment_id=jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/deployment_id', '1'),
        message_type=LTI13MessageType.RESOURCE_LINK_REQUEST,
        custom_parameters=jwt_payload.get('https://purl.imsglobal.org/spec/lti/claim/custom', {})
    )
    
    from ...core.security import SecurityManager
    security_manager = SecurityManager()
    
    token_data = {
        "user_id": lti_user.user_id,
        "context_id": lti_user.context_id,
        "resource_link_id": lti_user.resource_link_id,
        "roles": [role.value for role in lti_user.roles],
        "deployment_id": lti_user.deployment_id
    }
    
    session_token = security_manager.create_access_token(token_data)
    
    logger.info(f"LTI 1.3 launch successful for user: {lti_user.user_id}")
    
    launch_data = {
        "user_id": lti_user.user_id,
        "context_id": lti_user.context_id,
        "resource_link_id": lti_user.resource_link_id,
        "roles": [role.value for role in lti_user.roles],
        "lis_outcome_service_url": getattr(lti_user, 'lis_outcome_service_url', None),
        "lis_result_sourcedid": getattr(lti_user, 'lis_result_sourcedid', None)
    }
    
    return templates.TemplateResponse("tool_interface.html", {
        "request": request,
        "user": lti_user,
        "launch_data": launch_data,
        "session_token": session_token,
        "api_base_url": settings.LTI_TOOL_URL,
        "lti_version": "1.3"
    })

@router.get("/deep-linking", response_class=HTMLResponse)
@router.post("/deep-linking", response_class=HTMLResponse)
async def deep_linking(request: Request):
    """Handle LTI 1.3 Deep Linking requests"""

    return HTMLResponse(
        content="<h1>LTI 1.3 Deep Linking</h1><p>Content selection interface would go here</p>",
        status_code=200
    )

@router.get("/health")
async def lti13_health():
    """LTI 1.3 specific health check"""
    
    health_status = {
        "status": "healthy",
        "lti_version": "1.3.0",
        "oidc_login_url": settings.LTI_LOGIN_URL,
        "launch_url": settings.LTI_LAUNCH_URL,
        "jwks_url": settings.LTI_JWKS_URL,
        "client_id": settings.LTI_CLIENT_ID,
        "deployment_id": settings.LTI_DEPLOYMENT_ID,
        "platform_issuer": settings.LTI_PLATFORM_ISSUER
    }
    
    placeholder_values = [
        "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS",
        "your-consumer-key",
        "lti-tool-client-id"
    ]
    
    config_complete = True
    missing_config = []
    
    if settings.LTI_CLIENT_ID in placeholder_values:
        config_complete = False
        missing_config.append("LTI_CLIENT_ID")
    
    if settings.LTI_PLATFORM_ISSUER in placeholder_values:
        config_complete = False
        missing_config.append("LTI_PLATFORM_ISSUER")
    
    if settings.LTI_DEPLOYMENT_ID in placeholder_values:
        config_complete = False
        missing_config.append("LTI_DEPLOYMENT_ID")
    
    health_status["moodle_config_complete"] = config_complete
    if not config_complete:
        health_status["missing_config"] = missing_config
        health_status["status"] = "needs_configuration"
        health_status["message"] = "Please complete Moodle registration and update .env file"
    
    try:
        with open(settings.LTI_PRIVATE_KEY_PATH, 'r'):
            health_status["private_key"] = "present"
    except FileNotFoundError:
        health_status["private_key"] = "missing"
        health_status["status"] = "degraded"
    
    try:
        with open(settings.LTI_PUBLIC_KEY_PATH, 'r'):
            health_status["public_key"] = "present"
    except FileNotFoundError:
        health_status["public_key"] = "missing"
        health_status["status"] = "degraded"
    
    return health_status
