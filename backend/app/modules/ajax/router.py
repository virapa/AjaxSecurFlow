import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from redis.asyncio import Redis
from urllib.parse import unquote

from backend.app.shared.infrastructure.redis.deps import get_redis
from backend.app.shared.infrastructure.redis.rate_limiter import global_ajax_rate_limiter
from backend.app.shared.infrastructure.ajax.deps import get_ajax_client
from backend.app.modules.auth import service as auth_service
from backend.app.modules.billing import service as billing_service
from backend.app.modules.ajax import service as ajax_service
from backend.app.modules.ajax.schemas import (
    HubDetail, DeviceListItem, DeviceDetail, 
    HubCommandRequest, CommandResponse, EventLogResponse,
    GroupBase, Room
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/hubs", response_model=List[HubDetail])
async def list_hubs(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "list_hubs"):
        raise HTTPException(status_code=403, detail="Feature not available in your plan")
    return await ajax.get_hubs(user_email=current_user.email)

@router.get("/hubs/{hub_id}", response_model=HubDetail)
async def get_hub(
    hub_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    return await ajax.get_hub_details(user_email=current_user.email, hub_id=hub_id)

@router.get("/hubs/{hub_id}/devices", response_model=List[DeviceListItem])
async def list_devices(
    hub_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.is_subscription_active(current_user):
         raise HTTPException(status_code=403, detail="Active subscription required")
    return await ajax.get_hub_devices(user_email=current_user.email, hub_id=hub_id)

@router.get("/hubs/{hub_id}/devices/{device_id}", response_model=DeviceDetail)
async def get_device(
    hub_id: str,
    device_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    return await ajax.get_device_details(user_email=current_user.email, hub_id=hub_id, device_id=device_id)

@router.get("/hubs/{hub_id}/groups", response_model=List[GroupBase])
async def list_groups(
    hub_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    return await ajax.get_hub_groups(user_email=current_user.email, hub_id=hub_id)

@router.get("/hubs/{hub_id}/rooms", response_model=List[Room])
async def list_rooms(
    hub_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    return await ajax.get_hub_rooms(user_email=current_user.email, hub_id=hub_id)

@router.get("/hubs/{hub_id}/rooms/{room_id}", response_model=Room)
async def get_room(
    hub_id: str,
    room_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    return await ajax.get_room_details(user_email=current_user.email, hub_id=hub_id, room_id=room_id)

@router.get("/hubs/{hub_id}/logs", response_model=EventLogResponse)
async def get_logs(
    hub_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "read_logs"):
        raise HTTPException(status_code=403, detail="Logs access not included in your plan")
    return await ajax.get_hub_logs(user_email=current_user.email, hub_id=hub_id, limit=limit, offset=offset)


@router.post("/hubs/{hub_id}/arm-state", response_model=CommandResponse)
async def arm_hub(
    hub_id: str,
    body: HubCommandRequest,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "send_commands"):
        raise HTTPException(status_code=403, detail="Command execution not included in your plan")
    
    result = await ajax.set_arm_state(
        current_user.email, 
        hub_id, 
        body.arm_state, 
        body.group_id
    )
    return {"success": True, "message": "Command sent successfully"}

# --- Catch-all Proxy Routes ---

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
async def proxy_ajax_request(
    request: Request,
    path: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    """
    Catch-all proxy route for Ajax API resources not explicitly defined.
    """
    if not billing_service.can_access_feature(current_user, "access_proxy"):
        raise HTTPException(status_code=403, detail="PREMIUM subscription required to access Proxy API.")

    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
             body = await request.body()

    decoded_path = unquote(path)
    endpoint = f"/{decoded_path.lstrip('/')}"
    
    return await ajax.request(
        user_email=current_user.email,
        method=request.method,
        endpoint=endpoint,
        json=body if isinstance(body, dict) else None
    )
