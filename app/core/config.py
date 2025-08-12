from pathlib import Path
from typing import List
import os
from dotenv import load_dotenv


load_dotenv()

class Settings:
    """Application configuration settings"""
    
    APP_NAME: str = "FastAPI LTI 1.3 Tool"
    VERSION: str = "1.3.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    LTI_VERSION: str = "1.3.0"
    LTI_TOOL_NAME: str = os.getenv("LTI_TOOL_NAME", "FastAPI LTI 1.3 Tool")
    LTI_DESCRIPTION: str = os.getenv("LTI_DESCRIPTION", "A comprehensive LTI 1.3 tool built with FastAPI")
    
    LTI_LOGIN_URL: str = os.getenv("LTI_LOGIN_URL", "http://localhost:8000/lti/login")
    LTI_LAUNCH_URL: str = os.getenv("LTI_LAUNCH_URL", "http://localhost:8000/lti/launch")
    LTI_DEEP_LINKING_URL: str = os.getenv("LTI_DEEP_LINKING_URL", "http://localhost:8000/lti/deep-linking")
    LTI_JWKS_URL: str = os.getenv("LTI_JWKS_URL", "http://localhost:8000/lti/jwks")
    
    LTI_CLIENT_ID: str = os.getenv("LTI_CLIENT_ID", "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS")
    LTI_DEPLOYMENT_ID: str = os.getenv("LTI_DEPLOYMENT_ID", "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS")
    LTI_TOOL_URL: str = os.getenv("LTI_TOOL_URL", "http://localhost:8000")
    
    LTI_PLATFORM_ISSUER: str = os.getenv("LTI_PLATFORM_ISSUER", "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS")
    LTI_PLATFORM_AUTH_URL: str = os.getenv("LTI_PLATFORM_AUTH_URL", "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS")
    LTI_PLATFORM_TOKEN_URL: str = os.getenv("LTI_PLATFORM_TOKEN_URL", "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS")
    LTI_PLATFORM_JWKS_URL: str = os.getenv("LTI_PLATFORM_JWKS_URL", "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS")
    
    LTI_PRIVATE_KEY_PATH: str = os.getenv("LTI_PRIVATE_KEY_PATH", "keys/private.pem")
    LTI_PUBLIC_KEY_PATH: str = os.getenv("LTI_PUBLIC_KEY_PATH", "keys/public.pem")
    LTI_KEY_ID: str = os.getenv("LTI_KEY_ID", "lti-key-1")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "RS256")  
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    
    ALLOW_ORIGINS: List[str] = os.getenv("ALLOW_ORIGINS", "http://localhost:8080,http://localhost:8000").split(",")
    ALLOW_CREDENTIALS: bool = os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"
    ALLOW_METHODS: List[str] = os.getenv("ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    ALLOW_HEADERS: List[str] = os.getenv("ALLOW_HEADERS", "*").split(",")
    

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "uploads/"))
    ALLOWED_EXTENSIONS: List[str] = os.getenv("ALLOWED_EXTENSIONS", "pdf,doc,docx,txt,png,jpg,jpeg,gif").split(",")
    
    MOODLE_BASE_URL: str = os.getenv("MOODLE_BASE_URL", "http://localhost:8080")
    MOODLE_WS_TOKEN: str = os.getenv("MOODLE_WS_TOKEN", "")
    
    LTI_CONSUMER_KEY: str = os.getenv("LTI_CONSUMER_KEY", "")
    LTI_SHARED_SECRET: str = os.getenv("LTI_SHARED_SECRET", "")
    
    PRODUCTION: bool = os.getenv("PRODUCTION", "false").lower() == "true"
    HTTPS_ONLY: bool = os.getenv("HTTPS_ONLY", "false").lower() == "true"
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"

settings = Settings()
