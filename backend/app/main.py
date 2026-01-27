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
