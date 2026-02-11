from fastapi import APIRouter
from backend.app.modules.auth.router import router as auth_router
from backend.app.modules.billing.router import router as billing_router
from backend.app.modules.ajax.router import router as ajax_router
from backend.app.modules.security.router import router as security_router
from backend.app.modules.notifications.router import router as notifications_router
from backend.app.modules.support.router import router as support_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(auth_router, prefix="/users", tags=["Users Profile"], include_in_schema=False)
api_router.include_router(billing_router, prefix="/billing", tags=["Billing & Subscriptions"])
api_router.include_router(ajax_router, prefix="/ajax", tags=["Ajax Systems Proxy"])
api_router.include_router(security_router, prefix="/security", tags=["Security Auditing"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["User Notifications"])
api_router.include_router(support_router, prefix="/support", tags=["Support & Help"])
