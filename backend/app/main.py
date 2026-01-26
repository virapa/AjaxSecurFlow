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

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/")
async def root():
    return {"message": "AjaxSecurFlow Proxy API is running"}
