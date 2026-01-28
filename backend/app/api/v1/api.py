from fastapi import APIRouter
from backend.app.api.v1 import auth, users, billing, proxy
from backend.app.api.v1.endpoints import ajax

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Identity & Session"])
api_router.include_router(users.router, prefix="/users", tags=["User Profiles"])
api_router.include_router(ajax.router, prefix="/ajax", tags=["Ajax Hub Management"])
api_router.include_router(proxy.router, prefix="/ajax", tags=["Generic Proxy Access"])
api_router.include_router(billing.router, prefix="/billing", tags=["Subscription & Billing"])
