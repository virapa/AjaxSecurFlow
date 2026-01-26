from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Any
from backend.app.services.ajax_client import AjaxClient
from backend.app.services.rate_limiter import RateLimiter
from backend.app.api.v1.auth import get_current_user

router = APIRouter()
rate_limiter = RateLimiter(key_prefix="ajax_proxy", limit=100, window=60)

# We secure the proxy so only authenticated users can use it
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_ajax_request(
    path: str, 
    request: Request,
    current_user: str = Depends(get_current_user),
    _ = Depends(rate_limiter) # Apply Rate Limit
):
    """
    Proxy request to Ajax Systems API.
    """
    client = AjaxClient()
    
    # Extract body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            body = await request.body()
    
    # We might want to filter headers or forward specific ones
    # For now, we trust AjaxClient to handle Auth headers
    
    try:
        # AjaxClient login method is handled internally.
        # We just pass the path. Note that AjaxClient base_url is already set.
        # If 'path' comes in as 'some/endpoint', we append it.
        
        # NOTE: AjaxClient.request takes "endpoint".
        # Ensure leading slash logic is correct.
        endpoint = f"/{path}"
        
        response_data = await client.request(
            method=request.method,
            endpoint=endpoint,
            json=body if isinstance(body, dict) else None,
            # content=body if not dict... (httpx handles this)
        )
        return response_data
        
    except Exception as e:
        # In PROD, log error details and return generic 500 or mapped error
        raise HTTPException(status_code=502, detail=f"Upstream API Error: {str(e)}")
