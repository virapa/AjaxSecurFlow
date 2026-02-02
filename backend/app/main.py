from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.app.core.config import settings

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
from backend.app.services import audit_service

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
            
            await audit_service.log_request_action(
                db=db,
                request=request,
                user_id=user_id,
                action=f"AUTO_AUDIT_{request.method}",
                status_code=response.status_code,
                latency_ms=latency_ms,
                correlation_id=correlation_id
            )
    except Exception:  # nosec B110
        # Failsafe: Audit failure shouldn't crash the main request
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
            clean_path = path.replace(settings.API_V1_STR, "")
            new_paths[clean_path] = methods
        else:
            new_paths[path] = methods
            
    openapi_schema["paths"] = new_paths
    
    # Display the Base URL exactly as in your image
    openapi_schema["servers"] = [{"url": settings.API_V1_STR, "description": "Local server"}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

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
