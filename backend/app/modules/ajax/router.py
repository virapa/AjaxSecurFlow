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

router = APIRouter(
    tags=["Ajax API"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient plan permissions"},
        429: {"description": "Rate limit exceeded"}
    }
)

@router.get(
    "/hubs",
    response_model=List[HubDetail],
    summary="List all hubs",
    description="""
    Get a list of all hubs accessible to the authenticated user.
    
    **Required Plan**: Free or higher
    
    **Plan Access**:
    - ✅ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: List of hub objects with details including name, status, role, and configuration.
    """,
    tags=["Hubs", "Free Tier"],
    responses={
        200: {"description": "List of hubs retrieved successfully"},
        403: {"description": "Hub access not included in your plan"}
    }
)
async def list_hubs(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "list_hubs"):
        raise HTTPException(status_code=403, detail="Feature not available in your plan")
    return await ajax.get_hubs(user_email=current_user.email)

@router.get(
    "/hubs/{hub_id}",
    response_model=HubDetail,
    summary="Get hub details",
    description="""
    Get detailed information for a specific hub.
    
    **Required Plan**: Free or higher
    
    **Plan Access**:
    - ✅ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: Hub object with complete details including devices, rooms, and current status.
    """,
    tags=["Hubs", "Free Tier"],
    responses={
        200: {"description": "Hub details retrieved successfully"},
        403: {"description": "Hub access not included in your plan"},
        404: {"description": "Hub not found"}
    }
)
async def get_hub(
    hub_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "list_hubs"):
        raise HTTPException(status_code=403, detail="Hub access not included in your plan")
    return await ajax.get_hub_details(user_email=current_user.email, hub_id=hub_id)

@router.get(
    "/hubs/{hub_id}/devices",
    response_model=List[DeviceListItem],
    summary="List hub devices",
    description="""
    Get a list of all devices in a specific hub.
    
    **Required Plan**: Basic or higher
    
    **Plan Access**:
    - ❌ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: List of devices with name, type, online status, room, and group information.
    """,
    tags=["Devices", "Basic Tier"],
    responses={
        200: {"description": "Device list retrieved successfully"},
        403: {"description": "Device access not included in your plan"},
        404: {"description": "Hub not found"}
    }
)
async def list_devices(
    hub_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "read_devices"):
         raise HTTPException(status_code=403, detail="Device access not included in your plan")
    return await ajax.get_hub_devices(user_email=current_user.email, hub_id=hub_id)

@router.get(
    "/hubs/{hub_id}/devices/{device_id}",
    response_model=DeviceDetail,
    summary="Get device details",
    description="""
    Get detailed information for a specific device.
    
    **Required Plan**: Basic or higher
    
    **Plan Access**:
    - ❌ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: Device object with complete details including configuration and current state.
    """,
    tags=["Devices", "Basic Tier"],
    responses={
        200: {"description": "Device details retrieved successfully"},
        403: {"description": "Device access not included in your plan"},
        404: {"description": "Device not found"}
    }
)
async def get_device(
    hub_id: str,
    device_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "read_devices"):
        raise HTTPException(status_code=403, detail="Device access not included in your plan")
    return await ajax.get_device_details(user_email=current_user.email, hub_id=hub_id, device_id=device_id)

@router.get(
    "/hubs/{hub_id}/groups",
    response_model=List[GroupBase],
    summary="List hub groups",
    description="""
    Get a list of all security groups in a specific hub.
    
    **Required Plan**: Basic or higher
    
    **Plan Access**:
    - ❌ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: List of groups with IDs and names.
    """,
    tags=["Groups", "Basic Tier"],
    responses={
        200: {"description": "Group list retrieved successfully"},
        403: {"description": "Group access not included in your plan"},
        404: {"description": "Hub not found"}
    }
)
async def list_groups(
    hub_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "read_groups"):
        raise HTTPException(status_code=403, detail="Group access not included in your plan")
    return await ajax.get_hub_groups(user_email=current_user.email, hub_id=hub_id)

@router.get(
    "/hubs/{hub_id}/rooms",
    response_model=List[Room],
    summary="List hub rooms",
    description="""
    Get a list of all rooms in a specific hub.
    
    **Required Plan**: Basic or higher
    
    **Plan Access**:
    - ❌ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: List of rooms with IDs and names.
    """,
    tags=["Rooms", "Basic Tier"],
    responses={
        200: {"description": "Room list retrieved successfully"},
        403: {"description": "Room access not included in your plan"},
        404: {"description": "Hub not found"}
    }
)
async def list_rooms(
    hub_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "read_rooms"):
        raise HTTPException(status_code=403, detail="Room access not included in your plan")
    return await ajax.get_hub_rooms(user_email=current_user.email, hub_id=hub_id)

@router.get(
    "/hubs/{hub_id}/rooms/{room_id}",
    response_model=Room,
    summary="Get room details",
    description="""
    Get detailed information for a specific room.
    
    **Required Plan**: Basic or higher
    
    **Plan Access**:
    - ❌ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: Room object with complete details.
    """,
    tags=["Rooms", "Basic Tier"],
    responses={
        200: {"description": "Room details retrieved successfully"},
        403: {"description": "Room access not included in your plan"},
        404: {"description": "Room not found"}
    }
)
async def get_room(
    hub_id: str,
    room_id: str,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "read_rooms"):
        raise HTTPException(status_code=403, detail="Room access not included in your plan")
    return await ajax.get_room_details(user_email=current_user.email, hub_id=hub_id, room_id=room_id)

@router.get(
    "/hubs/{hub_id}/logs",
    response_model=EventLogResponse,
    summary="Get hub event logs",
    description="""
    Get paginated event logs for a specific hub.
    
    **Required Plan**: Basic or higher
    
    **Plan Access**:
    - ❌ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: Paginated list of events with timestamps, types, and details.
    """,
    tags=["Logs", "Basic Tier"],
    responses={
        200: {"description": "Event logs retrieved successfully"},
        403: {"description": "Logs access not included in your plan"},
        404: {"description": "Hub not found"}
    }
)
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


@router.post(
    "/hubs/{hub_id}/arm-state",
    response_model=CommandResponse,
    summary="Set hub arm state",
    description="""
    Send arm/disarm command to a specific hub.
    
    **Required Plan**: Pro or higher
    
    **Plan Access**:
    - ❌ Free
    - ❌ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Request Body**:
    - `armState`: 0 (disarm), 1 (arm), 2 (night mode), 3 (partial arm)
    - `groupId` (optional): Specific group to arm/disarm
    
    **Returns**: Command execution result with status.
    """,
    tags=["Commands", "Pro Tier"],
    responses={
        200: {"description": "Command sent successfully"},
        403: {"description": "Command execution not included in your plan"},
        404: {"description": "Hub not found"},
        400: {"description": "Invalid arm state or group ID"}
    }
)
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
