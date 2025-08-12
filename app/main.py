from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import time

from .core.config import settings
from .api.routes import lti13, user, tool

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""

    logger.info("FastAPI LTI Tool starting up...")
    logger.info(f"Environment: {'Production' if not settings.DEBUG else 'Development'}")
    logger.info(f"LTI Launch URL: {settings.LTI_LAUNCH_URL}")
    
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    yield
    
    logger.info("FastAPI LTI Tool shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="A comprehensive LTI (Learning Tools Interoperability) external tool built with FastAPI",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url} from {request.client.host}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {process_time:.4f}s")
    
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(lti13.router)
app.include_router(user.router)
app.include_router(tool.router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "FastAPI LTI External Tool",
        "version": settings.VERSION,
        "status": "running",
        "environment": "development" if settings.DEBUG else "production",
        "lti_config_url": f"{settings.LTI_LAUNCH_URL.rsplit('/', 2)[0]}/lti/config",
        "launch_url": settings.LTI_LAUNCH_URL,
        "docs_url": "/docs" if settings.DEBUG else None
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "services": {
            "lti": "operational",
            "api": "operational",
            "static_files": "operational"
        },
        "configuration": {
            "lti_client_id_configured": bool(settings.LTI_CLIENT_ID and settings.LTI_CLIENT_ID != "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS"),
            "lti_deployment_id_configured": bool(settings.LTI_DEPLOYMENT_ID and settings.LTI_DEPLOYMENT_ID != "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS"),
            "lti_platform_configured": bool(settings.LTI_PLATFORM_ISSUER and settings.LTI_PLATFORM_ISSUER != "CHANGE_ME_MOODLE_WILL_PROVIDE_THIS"),
            "upload_directory_exists": settings.UPLOAD_DIR.exists(),
            "debug_mode": settings.DEBUG
        }
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Internal server error: {str(exc)}",
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )