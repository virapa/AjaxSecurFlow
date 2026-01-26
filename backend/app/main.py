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

from backend.app.api.v1 import auth, proxy

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(proxy.router, prefix="/api/v1/ajax", tags=["ajax"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/")
async def root():
    return {"message": "AjaxSecurFlow Proxy API is running"}
