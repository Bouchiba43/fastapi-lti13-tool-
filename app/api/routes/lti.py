from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import time

from ...core.config import settings
from ...core.lti_validator import LTISignatureValidator
from ...core.security import SecurityManager
from ...models.lti import LTILaunchRequest, LTIUser, LTIRole
from ...services.grade_service import LTIOutcomesService

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/lti", tags=["lti"])

@router.get("/config", response_class=HTMLResponse)
async def get_lti_config():
    """LTI XML configuration endpoint for Moodle"""
    xml_config = f'''<?xml version="1.0" encoding="UTF-8"?>
<cartridge_basiclti_link xmlns="http://www.imsglobal.org/xsd/imslticc_v1p0"
    xmlns:blti="http://www.imsglobal.org/xsd/imsbasiclti_v1p0"
    xmlns:lticm="http://www.imsglobal.org/xsd/imslticm_v1p0"
    xmlns:lticp="http://www.imsglobal.org/xsd/imslticp_v1p0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imslticc_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticc_v1p0.xsd
    http://www.imsglobal.org/xsd/imsbasiclti_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imsbasiclti_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticm_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticm_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticp_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticp_v1p0.xsd">
    
    <blti:title>{settings.LTI_TOOL_NAME}</blti:title>
    <blti:description>{settings.LTI_DESCRIPTION}</blti:description>
    <blti:launch_url>{settings.LTI_LAUNCH_URL}</blti:launch_url>
    <blti:icon>{settings.LTI_ICON_URL}</blti:icon>
    <blti:secure_icon>{settings.LTI_ICON_URL}</blti:secure_icon>
    
    <blti:extensions platform="canvas.instructure.com">
        <lticm:property name="privacy_level">public</lticm:property>
        <lticm:property name="domain">localhost:8000</lticm:property>
    </blti:extensions>
    
    <blti:extensions platform="moodle.org">
        <lticm:property name="privacy_level">public</lticm:property>
        <lticm:property name="domain">localhost:8000</lticm:property>
        <lticm:property name="tool_id">my_fastapi_lti_tool</lticm:property>
    </blti:extensions>
    
    <cartridge_bundle identifierref="BLTI001_Bundle"/>
    <cartridge_icon identifierref="BLTI001_Icon"/>
</cartridge_basiclti_link>'''
    
    return HTMLResponse(content=xml_config, media_type="application/xml")

@router.post("/debug-launch")
async def debug_lti_launch(request: Request):
    """Debug endpoint for LTI launch - shows all parameters without validation"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    form_data = await request.form()
    request_data = dict(form_data)
    
    return {
        "url": str(request.url),
        "method": request.method,
        "headers": dict(request.headers),
        "form_data": request_data,
        "client_host": request.client.host,
        "expected_consumer_key": settings.LTI_CONSUMER_KEY,
        "expected_shared_secret": settings.LTI_SHARED_SECRET[:4] + "***" if settings.LTI_SHARED_SECRET else None
    }

@router.get("/test-signature")
async def test_signature():
    """Test OAuth signature generation for debugging"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    test_params = {
        "lti_message_type": "basic-lti-launch-request",
        "lti_version": "LTI-1p0",
        "resource_link_id": "test_resource_123",
        "oauth_consumer_key": settings.LTI_CONSUMER_KEY,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": "test_nonce_12345",
        "oauth_version": "1.0",
        "user_id": "test_user",
        "context_id": "test_context"
    }
    
    test_url = settings.LTI_LAUNCH_URL
    signature = LTISignatureValidator.generate_signature(
        "POST", test_url, test_params, settings.LTI_SHARED_SECRET
    )
    
    test_params["oauth_signature"] = signature
    
    return {
        "test_url": test_url,
        "test_params": test_params,
        "signature": signature,
        "consumer_key": settings.LTI_CONSUMER_KEY,
        "validation_url": f"{settings.LTI_LAUNCH_URL.rsplit('/', 1)[0]}/debug-launch"
    }

@router.post("/launch")
async def lti_launch(request: Request):
    """Handle LTI launch requests from Moodle"""
    
    form_data = await request.form()
    request_data = dict(form_data)
    
    logger.info(f"LTI Launch Request from {request.client.host}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    logger.info(f"OAuth Consumer Key: {request_data.get('oauth_consumer_key')}")
    logger.info(f"LTI Message Type: {request_data.get('lti_message_type')}")
    logger.info(f"LTI Version: {request_data.get('lti_version')}")
    logger.info(f"Resource Link ID: {request_data.get('resource_link_id')}")
    
    launch_url = str(request.url).split('?')[0]
    
    if 'oauth_signature' in request_data:
        logger.info(f"Signature validation URL: {launch_url}")
        logger.info(f"OAuth signature provided: {request_data.get('oauth_signature')}")
    
    validation_result = LTISignatureValidator.validate_lti_request(
        request_data, launch_url, "POST"
    )
    
    if not validation_result["valid"]:
        logger.error(f"LTI validation failed: {validation_result['errors']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid LTI request: {', '.join(validation_result['errors'])}"
        )
    
    if validation_result["warnings"]:
        logger.warning(f"LTI validation warnings: {validation_result['warnings']}")
    
    user_roles = []
    if request_data.get('roles'):
        role_strings = request_data['roles'].split(',')
        for role_str in role_strings:
            role_str = role_str.strip()
            if 'Instructor' in role_str or 'Teacher' in role_str:
                user_roles.append(LTIRole.INSTRUCTOR)
            elif 'Student' in role_str or 'Learner' in role_str:
                user_roles.append(LTIRole.LEARNER)
            elif 'TeachingAssistant' in role_str:
                user_roles.append(LTIRole.TEACHING_ASSISTANT)
            elif 'Administrator' in role_str:
                user_roles.append(LTIRole.ADMINISTRATOR)
            else:
                user_roles.append(LTIRole.MEMBER)
    
    lti_user = LTIUser(
        user_id=request_data.get('user_id', 'unknown'),
        full_name=request_data.get('lis_person_name_full', 'Unknown User'),
        given_name=request_data.get('lis_person_name_given'),
        family_name=request_data.get('lis_person_name_family'),
        email=request_data.get('lis_person_contact_email_primary'),
        roles=user_roles,
        context_id=request_data.get('context_id'),
        context_title=request_data.get('context_title'),
        resource_link_id=request_data.get('resource_link_id', 'unknown'),
        launch_timestamp=datetime.utcnow()
    )
    
    token_data = {
        "user_id": lti_user.user_id,
        "full_name": lti_user.full_name,
        "email": lti_user.email,
        "roles": [role.value for role in lti_user.roles],
        "is_instructor": lti_user.is_instructor,
        "context_id": lti_user.context_id,
        "context_title": lti_user.context_title,
        "resource_link_id": lti_user.resource_link_id,
        "lis_outcome_service_url": request_data.get('lis_outcome_service_url'),
        "lis_result_sourcedid": request_data.get('lis_result_sourcedid')
    }
    
    session_token = SecurityManager.create_access_token(token_data)
    
    launch_data = {
        "user_id": lti_user.user_id,
        "resource_link_id": lti_user.resource_link_id,
        "lis_outcome_service_url": request_data.get('lis_outcome_service_url'),
        "lis_result_sourcedid": request_data.get('lis_result_sourcedid'),
        "launch_timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"User {lti_user.user_id} launched tool in context {lti_user.context_id}")
    
    return templates.TemplateResponse("tool_interface.html", {
        "request": request,
        "user": lti_user,
        "session_token": session_token,
        "launch_data": launch_data
    })

@router.get("/xml-config")
async def get_xml_config():
    """Alternative endpoint for XML config (some LMS prefer this URL)"""
    return await get_lti_config()
