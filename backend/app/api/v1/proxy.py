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
        
        # Determine resource_id from path (e.g., /hubs/123/...)
        resource_id = None
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0] == "hubs":
            resource_id = path_parts[1]

        # Determine severity based on method
        # Mutations (POST, PUT, DELETE) are more sensitive
        severity = "WARNING" if request.method in ["POST", "PUT", "DELETE", "PATCH"] else "INFO"

        # Updated to include user_email for multitenant support
        response_data = await client.request(
            user_email=current_user.email,
            method=request.method,
            endpoint=endpoint,
            json=body if isinstance(body, dict) else None,
        )
        
        # Log successful proxy action with enhanced context
        await audit_service.log_request_action(
            db=db,
            request=request,
            user_id=current_user.id,
            action=f"PROXY_{request.method}",
            status_code=200,
            severity=severity,
            resource_id=resource_id,
            payload={"path": path}
        )
        
        return response_data
        
    except Exception as e:
        # Log failed proxy action with elevated severity
        await audit_service.log_request_action(
            db=db,
            request=request,
            user_id=current_user.id,
            action=f"PROXY_{request.method}_FAILED",
            status_code=502,
            severity="CRITICAL",
            payload={"error": str(e), "path": path}
        )
        raise HTTPException(status_code=502, detail=f"Upstream API Error: {str(e)}")
