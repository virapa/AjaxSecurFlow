from fastapi import APIRouter, Depends, Request, HTTPException, Path
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.ajax_client import AjaxClient
from backend.app.services.global_rate_limiter import global_ajax_rate_limiter
from backend.app.services import audit_service, billing_service
from backend.app.schemas.auth import ErrorMessage
from backend.app.api.v1.auth import get_current_user
from backend.app.api.v1.utils import handle_ajax_error
from backend.app.domain.models import User
from backend.app.api.deps import get_db, get_ajax_client
from urllib.parse import unquote

router = APIRouter()
# Global rate limiter: shares the same 100 req/min pool with /ajax endpoints
rate_limiter = global_ajax_rate_limiter

@router.get("/{path:path}", summary="Generic Ajax API Proxy (GET)")
@router.post("/{path:path}", summary="Generic Ajax API Proxy (POST)")
@router.put("/{path:path}", summary="Generic Ajax API Proxy (PUT)")
@router.delete("/{path:path}", summary="Generic Ajax API Proxy (DELETE)")
@router.patch("/{path:path}", summary="Generic Ajax API Proxy (PATCH)")
async def proxy_ajax_request(
    request: Request,
    path: str = Path(..., description="The sub-resource path in Ajax API (e.g., 'hubs', 'hubs/ID/devices')"), 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client: AjaxClient = Depends(get_ajax_client),
    _ = Depends(rate_limiter)
):
    """
    Catch-all proxy route that forwards authenticated requests to the Ajax Systems API.
    - Requires an active subscription.
    - Implements Rate Limiting (100 req/min).
    - Automatically manages session tokens and background refreshes.
    """
    # SaaS Enforcement: Validate Subscription
    if not billing_service.can_access_feature(current_user, "access_proxy"):
        raise HTTPException(
            status_code=403, 
            detail="PREMIUM subscription required to access Proxy API."
        )

    
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            body = await request.body()
    
    try:
        # Decode path in case it comes encoded (e.g. from Swagger UI)
        decoded_path = unquote(path)
        endpoint = f"/{decoded_path.lstrip('/')}"
        
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
        # IMPORTANT: We log the real error INTERNALLY for the admin
        await audit_service.log_request_action(
            db=db,
            request=request,
            user_id=current_user.id,
            action=f"PROXY_{request.method}_FAILED",
            status_code=502,
            severity="CRITICAL",
            payload={"error": str(e), "path": path} # str(e) is safe here because it's DB only
        )
        # We use the handle_ajax_error to return a SAFE message to the USER
        handle_ajax_error(e)
