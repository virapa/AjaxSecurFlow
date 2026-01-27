from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (e.g. initialize DB connection pools if needed explicitly)
    yield
    # Shutdown logic

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
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
    if not request.url.path.startswith("/api/v1"):
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
    except Exception:
        # Failsafe: Audit failure shouldn't crash the main request
        pass
        
    response.headers["X-Correlation-ID"] = correlation_id
    return response

from backend.app.api.v1 import auth, proxy, users, billing
from backend.app.api.v1.endpoints import ajax as ajax_endpoints

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
# Specific Ajax endpoints (Must be before generic proxy)
app.include_router(ajax_endpoints.router, prefix="/api/v1/ajax", tags=["ajax-core"])
# Generic Proxy (Catch-all)
app.include_router(proxy.router, prefix="/api/v1/ajax", tags=["ajax-proxy"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])

@app.get("/health")
async def health_check():
    """
    Service health check endpoint for monitoring systems.
    """
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/")
async def root():
    """
    API Root endpoint.
    """
    return {"message": "AjaxSecurFlow Proxy API is running"}
