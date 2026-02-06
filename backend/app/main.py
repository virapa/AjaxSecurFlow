from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from backend.app.core.config import settings
from backend.app.services.ajax_client import AjaxAuthError
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (e.g. initialize DB connection pools if needed explicitly)
    yield
    # Shutdown logic


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## AjaxSecurFlow Proxy API
    An advanced, secure proxy for Ajax Systems API with:
    - **Unified Authentication**: Integrated with Ajax cloud identities.
    - **Session Persistence**: Automated token refresh (Dual Token).
    - **SaaS Billing**: Integrated Stripe lifecycle management.
    - **Corporate Auditing**: Comprehensive logging and tracking.
    """,
    contact={
        "name": "Development",
    },
    license_info={
        "name": "Proprietary",
    },
    lifespan=lifespan
)

import re
MALICIOUS_PATTERNS = [
    # Legacy server extensions
    r"\.(php|asp|aspx|jsp|cgi|pl|cfm|rb|py)$",
    # Sensitive files
    r"(\.env|\.git|\.vscode|\.ssh|web\.config|composer\.json|package\.json|Dockerfile)",
    # Admin panels
    r"/(admin|phpmyadmin|wp-admin|wp-content|wordpress|administrator|backoffice|cp|controlpanel|manager)",
    # Path traversal
    r"(/etc/passwd|/etc/shadow|/windows/system\.ini|win\.ini|\.\./)",
    # DB and logs
    r"\.(sql|bak|old|swp|log|sqlite|db)$",
    # Specific probes
    r"/(sdk|jk-status|balancer-manager|admin-console|webmail|happyaxis|uddiclient|fckeditor)"
]
MALICIOUS_REGEX = re.compile("|".join(MALICIOUS_PATTERNS), re.IGNORECASE)

@app.middleware("http")
async def request_shield_middleware(request: Request, call_next):
    """
    Backend Request Shield:
    Intercepts and blocks malicious scanning patterns before processing.
    """
    path = request.url.path
    if MALICIOUS_REGEX.search(path):
        logger.warning(f"[SECURITY] Blocked malicious backend probe: {path} from {request.client.host if request.client else 'unknown'}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Forbidden: Malicious activity detected."}
        )
    return await call_next(request)

# Global Exception Handlers
@app.exception_handler(AjaxAuthError)
async def ajax_auth_exception_handler(request: Request, exc: AjaxAuthError):
    """Handle Ajax authentication failures specifically."""
    logger.warning(f"Ajax Auth Failure: {exc}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Upstream authentication failure. Please check your Ajax credentials."}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Final fallback to prevent leaking technical details."""
    logger.exception(f"Unhandled exception at {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardize auditing with automated middleware
import time
import uuid
from fastapi import Request
from backend.app.core.db import async_session_factory
from backend.app.crud import audit as crud_audit
from backend.app.services import audit_service


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    Injects security headers recommended by OWASP 2025:
    - Content-Security-Policy (CSP)
    - Strict-Transport-Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
    """
    response = await call_next(request)
    
    # Prevents Clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevents MIME-sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Controls how much referrer information is sent
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Enforces HTTPS
    # Only meaningful on HTTPS deployments
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Basic CSP - Restrictive by default
    # Note: Swagger UI and Redoc require jsdelivr for assets by default in FastAPI
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "frame-ancestors 'none';"
    )
    
    return response

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """
    Automated Corporate Audit Middleware:
    - Generates Correlation ID
    - Measures Latency
    - Logs all API requests automatically
    """
    # Only audit API routes
    if not request.scope['path'].startswith(settings.API_V1_STR):
        return await call_next(request)

    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    
    # Non-blocking background log (via new session to avoid context issues)
    # Note: For mission-critical high-load, this would go to a queue (Celery/Kafka)
    try:
        async with async_session_factory() as db:
            # We try to get user_id from state if auth middleware/dependency already set it
            # (Though in FastAPI, middleware runs BEFORE dependencies, so user_id might be None here)
            user_id = getattr(request.state, "user_id", None)
            
            await crud_audit.create_audit_log(
                db=db,
                user_id=user_id,
                action=f"AUTO_AUDIT_{request.method}",
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                latency_ms=latency_ms,
                correlation_id=correlation_id
            )
    except Exception as e:  # nosec B110
        # Failsafe: Audit failure shouldn't crash the main request
        logger.error(f"Audit middleware failure: {str(e)}")
        pass
        
    response.headers["X-Correlation-ID"] = correlation_id
    return response
from fastapi.openapi.utils import get_openapi
from backend.app.api.v1.api import api_router

# Include router normally for full test compatibility
app.include_router(api_router, prefix=settings.API_V1_STR)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    try:
        # Generate the base schema
        openapi_schema = get_openapi(
            title="Ajax Client API",
            version="1.135.0", # Usando versión de tu imagen
            description="General API description",
            routes=app.routes,
        )
        
        # VISUAL CLEANUP: Strip /api/v1 from the paths displayed in Swagger
        new_paths = {}
        for path, methods in openapi_schema["paths"].items():
            if path.startswith(settings.API_V1_STR):
                clean_path = path.replace(settings.API_V1_STR, "", 1) # Only replace first occurrence
                if not clean_path.startswith("/"):
                    clean_path = "/" + clean_path
                new_paths[clean_path] = methods
            else:
                new_paths[path] = methods
                
        openapi_schema["paths"] = new_paths
        
        # Display the Base URL exactly as in your image
        openapi_schema["servers"] = [{"url": settings.API_V1_STR, "description": "Local server"}]
        
        app.openapi_schema = openapi_schema
        logger.info("OpenAPI schema generated successfully with path cleanup.")
        return app.openapi_schema
    except Exception as e:
        logger.error(f"Error generating OpenAPI schema: {e}")
        # Return fallback default schema if custom logic fails
        return get_openapi(
            title="Ajax Client API (Fallback)",
            version="1.0.0",
            routes=app.routes
        )

app.openapi = custom_openapi

@app.get("/health", tags=["System"], include_in_schema=False)
async def health_check():
    """
    Service health check endpoint for monitoring systems.
    """
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    """
    API Root endpoint.
    """
    return {"message": "AjaxSecurFlow Proxy API is running"}
