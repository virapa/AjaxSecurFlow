from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db, get_ajax_client
from backend.app.api.v1.auth import get_current_user
from backend.app.domain.models import User
from backend.app.services.ajax_client import AjaxClient, AjaxAuthError
from backend.app.services.billing_service import is_subscription_active, can_access_feature
from backend.app.services.global_rate_limiter import global_ajax_rate_limiter
from backend.app.services import audit_service, notification_service
from backend.app.schemas import ajax as schemas
from backend.app.schemas.auth import ErrorMessage
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Global rate limiter: 100 requests per minute TOTAL across all users
rate_limiter = global_ajax_rate_limiter

from backend.app.api.v1.utils import handle_ajax_error
import httpx


async def verify_hub_access(user_email: str, hub_id: str, client: AjaxClient) -> None:
    """
    Validates that the user has access to the specified hub.
    This prevents Broken Access Control (A01:2025) even if the upstream API 
    doesn't strictly enforce it for some resources.
    """
    try:
        # We fetch the user's hubs and check if the requested ID is present
        hubs_data = await client.get_hubs(user_email=user_email)
        hubs = hubs_data.get("hubs", []) if isinstance(hubs_data, dict) else hubs_data
        
        hub_ids = [str(h.get("id") if isinstance(h, dict) else h) for h in hubs]
        if hub_id not in hub_ids:
            logger.warning(f"Unauthorized Access Attempt: User {user_email} tried to access hub {hub_id}")
            raise HTTPException(
                status_code=403, 
                detail="Access denied to this security hub."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying hub access: {str(e)}")
        # If we can't verify, we fail secure (A10:2025)
        raise HTTPException(
            status_code=502, 
            detail="Could not verify access permissions with security provider."
        )

@router.get(
    "/hubs", 
    response_model=List[schemas.HubDetail],
    summary="List User Hubs",
    responses={
        401: {"model": ErrorMessage, "description": "Bearer token invalid or missing"},
        403: {"model": ErrorMessage, "description": "Subscription inactive"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_hubs(
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Retrieve the list of all hubs associated with the authenticated user.
    """
    if not can_access_feature(current_user, "list_hubs"):
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    try:
        response = await client.get_hubs(user_email=current_user.email)
        return response.get("hubs", []) if isinstance(response, dict) else response
    except Exception as e:
        handle_ajax_error(e)

@router.get(
    "/hubs/{hub_id}", 
    response_model=schemas.HubDetail,
    summary="Get Hub Detail",
    responses={
        404: {"model": ErrorMessage, "description": "Hub not found"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_hub_detail(
    hub_id: str = Path(..., description="The unique 8-character ID of the Hub", example="0004C602"),
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Get detailed information for a specific hub.
    """
    if not can_access_feature(current_user, "read_telemetry"):
        raise HTTPException(status_code=403, detail="BASIC or higher subscription required")
        
    await verify_hub_access(current_user.email, hub_id, client)
        
    try:
        data = await client.get_hub_details(user_email=current_user.email, hub_id=hub_id)
        
        # Mapping for legacy fields if they are missing at root but exist in nested objects
        if isinstance(data, dict):
            if "battery" in data and not data.get("battery_level"):
                data["battery_level"] = data["battery"].get("chargeLevelPercentage")
            if "gsm" in data and not data.get("gsm_signal"):
                data["gsm_signal"] = data["gsm"].get("signalLevel")
            if "firmware" in data and not data.get("firmware_version"):
                data["firmware_version"] = data["firmware"].get("version")
            if "ethernet" in data and not data.get("ethernet_ip"):
                data["ethernet_ip"] = data["ethernet"].get("ip")
                
        return data
    except Exception as e:
        handle_ajax_error(e)

@router.get(
    "/hubs/{hub_id}/groups", 
    response_model=List[schemas.GroupBase],
    summary="List Hub Groups",
    responses={
        403: {"model": ErrorMessage, "description": "Subscription inactive"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_hub_groups(
    hub_id: str = Path(..., description="ID of the Hub to query groups from", example="0004C602"),
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Retrieve security groups and partitions for a specific hub.
    """
    if not can_access_feature(current_user, "read_telemetry"):
        raise HTTPException(status_code=403, detail="BASIC or higher subscription required")

    await verify_hub_access(current_user.email, hub_id, client)

    try:
        response = await client.get_hub_groups(user_email=current_user.email, hub_id=hub_id)
        return response.get("groups", []) if isinstance(response, dict) else response
    except Exception as e:
        handle_ajax_error(e)

@router.get(
    "/hubs/{hub_id}/rooms", 
    response_model=List[schemas.Room],
    summary="List Hub Rooms",
    responses={
        403: {"model": ErrorMessage, "description": "Subscription inactive"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_hub_rooms(
    hub_id: str = Path(..., description="ID of the Hub to query rooms from", example="0004C602"),
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Retrieve the list of rooms configured for a specific hub.
    """
    if not can_access_feature(current_user, "read_telemetry"):
        raise HTTPException(status_code=403, detail="BASIC or higher subscription required")

    await verify_hub_access(current_user.email, hub_id, client)

    try:
        response = await client.get_hub_rooms(user_email=current_user.email, hub_id=hub_id)
        return response
    except Exception as e:
        handle_ajax_error(e)

@router.get(
    "/hubs/{hub_id}/rooms/{room_id}", 
    response_model=schemas.Room,
    summary="Get Room Detail",
    responses={
        404: {"model": ErrorMessage, "description": "Room not found"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_room_detail(
    hub_id: str = Path(..., description="ID of the Hub", example="0004C602"),
    room_id: str = Path(..., description="ID of the Room", example="1"),
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Get all details for a specific room within a hub.
    """
    if not can_access_feature(current_user, "read_telemetry"):
        raise HTTPException(status_code=403, detail="BASIC or higher subscription required")

    await verify_hub_access(current_user.email, hub_id, client)

    try:
        data = await client.get_room_details(
            user_email=current_user.email, 
            hub_id=hub_id, 
            room_id=room_id
        )
        return data
    except Exception as e:
        handle_ajax_error(e)

@router.get(
    "/hubs/{hub_id}/devices", 
    response_model=List[schemas.DeviceListItem],
    summary="List Hub Devices",
    responses={
        403: {"model": ErrorMessage, "description": "Subscription inactive"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_hub_devices(
    hub_id: str = Path(..., description="ID of the Hub to query devices from", example="0004C602"),
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Fetch all devices currently linked to the specified hub.
    """
    if not can_access_feature(current_user, "read_telemetry"):
        raise HTTPException(status_code=403, detail="BASIC or higher subscription required")

    await verify_hub_access(current_user.email, hub_id, client)

    try:
        response = await client.get_hub_devices(user_email=current_user.email, hub_id=hub_id)
        return response.get("devices", []) if isinstance(response, dict) else response
    except Exception as e:
        handle_ajax_error(e)

@router.get(
    "/hubs/{hub_id}/devices/{device_id}", 
    response_model=schemas.DeviceDetail,
    summary="Get Device Detail",
    responses={
        404: {"model": ErrorMessage, "description": "Device not found"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_device_detail(
    hub_id: str = Path(..., description="ID of the Hub where the device is registered", example="0004C602"),
    device_id: str = Path(..., description="The unique 8-character ID of the Device", example="3056A52F"),
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Get all technical and telemetry data for a specific device.
    """
    if not can_access_feature(current_user, "read_telemetry"):
        raise HTTPException(status_code=403, detail="BASIC or higher subscription required")
        
    await verify_hub_access(current_user.email, hub_id, client)
        
    try:
        data = await client.get_device_details(
            user_email=current_user.email, 
            hub_id=hub_id, 
            device_id=device_id
        )
        
        # Enrichment & Legacy Mapping
        if isinstance(data, dict):
            # Map legacy fields for easier frontend use
            data["battery_level"] = data.get("batteryChargeLevelPercentage")
            data["signal_strength"] = data.get("signalLevel")
            
        return data
    except Exception as e:
        handle_ajax_error(e)

# --- Logs/Events ---
@router.get(
    "/hubs/{hub_id}/logs", 
    response_model=schemas.EventLogResponse,
    summary="Get Hub Event Logs",
    responses={
        403: {"model": ErrorMessage, "description": "Subscription inactive"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_hub_logs(
    hub_id: str = Path(..., description="ID of the Hub to query logs from", example="0004C602"),
    limit: int = Query(100, description="Max number of logs to return (Page size)"),
    offset: int = Query(0, description="Number of logs to skip (Pagination)"),
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Retrieve event logs and history for a specific hub with pagination support.
    Returns a wrapped object with logs and total count.
    """
    if not can_access_feature(current_user, "read_logs"):
        raise HTTPException(status_code=403, detail="BASIC or higher subscription required")

    await verify_hub_access(current_user.email, hub_id, client)

    try:
        raw_data = await client.get_hub_logs(
            user_email=current_user.email, 
            hub_id=hub_id, 
            limit=limit, 
            offset=offset
        )
        
        # Parse logs list from response
        logs_list = []
        if isinstance(raw_data, list):
            logs_list = raw_data
        elif isinstance(raw_data, dict) and "logs" in raw_data:
            logs_list = raw_data["logs"]
            
        # Mapping for human-readable events in Spanish
        EVENT_MAP = {
            "Arm": "Sistema Armado",
            "Disarm": "Sistema Desarmado",
            "NightModeOn": "Modo Noche Activado",
            "Panic": "ALERTA DE PÁNICO",
            "Motion": "Movimiento Detectado",
            "Door": "Apertura de Puerta",
            "PowerLost": "Pérdida de Alimentación",
            "PowerRestored": "Alimentación Restaurada"
        }

        # Map raw data to schema and handle enrichment
        validated_logs = []
        for log in logs_list:
            # 1. Identity Mapping
            obj_type = log.get("sourceObjectType")
            obj_name = log.get("sourceObjectName")
            
            if obj_type == "USER":
                # We prioritize user_name for USER objects
                log["user_name"] = obj_name
            else:
                # We prioritize device_name for everything else
                log["device_name"] = obj_name
                
            # 2. Description Mapping (Event Translation)
            # Prioritize eventTag if it's in our map
            tag = log.get("eventTag")
            if tag in EVENT_MAP:
                log["event_desc"] = EVENT_MAP[tag]
            elif not log.get("event_desc") and tag:
                log["event_desc"] = tag # Fallback to raw tag if no mapping exists
                
            validated_logs.append(schemas.EventLog.model_validate(log))
            
            # --- SECURITY ALERT DETECTION ---
            # If the event is critical (Motion/Panic), ensure we have a notification
            if tag in ["Motion", "Panic"]:
                notification_title = EVENT_MAP.get(tag, tag)
                notification_message = f"Detección en {obj_name or 'dispositivo desconocido'} ({hub_id})"
                
                # Proactive notification generation
                # Note: In a production scale-out, we'd use a separate background task 
                # or check for duplicate notification IDs within a sliding window.
                await notification_service.create_notification(
                    db=db,
                    user_id=current_user.id,
                    title=f"ALERTA: {notification_title}",
                    message=notification_message,
                    notification_type="security",
                    link=f"/dashboard?hub={hub_id}"
                )

        return schemas.EventLogResponse(
            logs=validated_logs,
            total_count=len(validated_logs)
        )
            
    except Exception as e:
        handle_ajax_error(e)

@router.post(
    "/hubs/{hub_id}/arm-state", 
    response_model=schemas.CommandResponse,
    summary="Set Arm State (Control)",
    responses={
        200: {"model": schemas.CommandResponse, "description": "Command sent successfully"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
@router.post("/hubs/{hub_id}/command", response_model=schemas.CommandResponse)
async def send_hub_command(
    hub_id: str = Path(..., description="ID of the Hub to control", example="0004C602"),
    command: schemas.HubCommandRequest = Body(..., description="Arming command details"),
    current_user: User = Depends(get_current_user),
    ajax_client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Send a command to the Ajax Hub (Arm, Disarm, Night Mode).
    """
    if not can_access_feature(current_user, "send_commands"):
        raise HTTPException(status_code=403, detail="PRO or higher subscription required")

    await verify_hub_access(current_user.email, hub_id, ajax_client)
    
    user_id = await ajax_client._get_ajax_user_id(current_user.email)
    if not user_id:
        raise HTTPException(status_code=400, detail="User not linked to Ajax")

    try:
        result = await ajax_client.send_command(
            user_email=current_user.email,
            user_id=user_id,
            hub_id=hub_id,
            command=command.arm_state,
            group_id=command.group_id
        )

        if not result:
            raise HTTPException(status_code=500, detail="Command failed")

        return {"success": True, "message": "Command sent successfully"}
    except Exception as e:
        handle_ajax_error(e)

@router.get("/hubs/{hub_id}/role", response_model=schemas.UserHubBinding)
async def get_hub_role(
    hub_id: str = Path(..., description="ID of the Hub to query role from", example="0004C602"),
    current_user: User = Depends(get_current_user),
    ajax_client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Check the current user's role in the specified hub (MASTER, PRO, USER).
    This role determines access levels (e.g., viewing logs).
    """
    if not can_access_feature(current_user, "list_hubs"):
        raise HTTPException(status_code=403, detail="Active subscription required")

    # We verify hub access implicitly by checking if binding exists
    user_id = await ajax_client._get_ajax_user_id(current_user.email)
    if not user_id:
         raise HTTPException(status_code=400, detail="User not linked to Ajax")

    try:
        binding = await ajax_client.get_user_hub_binding(current_user.email, user_id, hub_id)
        if not binding:
             raise HTTPException(status_code=404, detail="Hub binding not found or access denied")
        
        return binding
    except Exception as e:
        handle_ajax_error(e)

async def set_hub_arm_state(
    request: Request,
    hub_id: str = Path(..., description="ID of the Hub to control", example="0004C602"),
    command: schemas.HubCommandRequest = Body(..., description="Arming command details"),
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limiter),
):
    """
    Set the arming state for a specific hub or security group.
    """
    if not can_access_feature(current_user, "send_commands"):
        raise HTTPException(status_code=403, detail="PRO or higher subscription required")

    await verify_hub_access(current_user.email, hub_id, client)

    try:
        response = await client.set_arm_state(
            user_email=current_user.email,
            hub_id=hub_id, 
            arm_state=command.arm_state, 
            group_id=command.group_id
        )
        
        # Audit high-severity security action
        await audit_service.log_request_action(
            db=db,
            request=request,
            user_id=current_user.id,
            action="HUB_SET_ARM_STATE",
            status_code=200,
            severity="WARNING",
            resource_id=hub_id,
            payload={
                "hub_id": hub_id, 
                "arm_state": command.arm_state, 
                "group_id": command.group_id
            }
        )
        
        return response
    except Exception as e:
        # Audit failed high-severity action
        await audit_service.log_request_action(
            db=db,
            request=request,
            user_id=current_user.id,
            action="HUB_SET_ARM_STATE_FAILED",
            status_code=502,
            severity="CRITICAL",
            resource_id=hub_id,
            payload={"error": str(e)}
        )
        handle_ajax_error(e)
