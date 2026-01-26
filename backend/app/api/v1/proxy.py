from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.ajax_client import AjaxClient
from backend.app.services.rate_limiter import RateLimiter
from backend.app.services import audit_service, billing_service
from backend.app.api.v1.auth import get_current_user
from backend.app.domain.models import User
from backend.app.core.db import get_db

router = APIRouter()
rate_limiter = RateLimiter(key_prefix="ajax_proxy", limit=100, window=60)

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_ajax_request(
    path: str, 
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _ = Depends(rate_limiter)
):
    """
    Proxy request to Ajax Systems API.
    Only allows access if user has an active subscription.
    """
    # SaaS Enforcement: Validate Subscription
    if not billing_service.is_subscription_active(current_user):
        # We allow free plan users if they are below a certain quota, 
        # but for this industrial version, let's require active subscription.
        raise HTTPException(
            status_code=403, 
            detail="Active subscription required to access Proxy API."
        )

    client = AjaxClient()
    
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            body = await request.body()
    
    try:
        endpoint = f"/{path}"
        
        response_data = await client.request(
            method=request.method,
            endpoint=endpoint,
            json=body if isinstance(body, dict) else None,
        )
        
        # Log successful proxy action
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action=f"PROXY_{request.method}",
            endpoint=endpoint,
            status_code=200,
            payload={"path": path}
        )
        
        return response_data
        
    except Exception as e:
        # Log failed proxy action
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action=f"PROXY_{request.method}_FAILED",
            endpoint=f"/{path}",
            status_code=502,
            payload={"error": str(e)}
        )
        raise HTTPException(status_code=502, detail=f"Upstream API Error: {str(e)}")
