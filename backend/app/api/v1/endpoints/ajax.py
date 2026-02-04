from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.v1.auth import get_current_user
from backend.app.core.db import get_db
from backend.app.domain.models import User
from backend.app.services.ajax_client import AjaxClient, AjaxAuthError
from backend.app.services.billing_service import is_subscription_active
from backend.app.services import audit_service
from backend.app.schemas import ajax as schemas
from backend.app.schemas.auth import ErrorMessage
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

from backend.app.api.v1.utils import handle_ajax_error
import httpx

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
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the list of all hubs associated with the authenticated user.

    Args:
        current_user: The user object retrieved from the security token.
        db: Database session (for auditing or supplemental lookups).

    Returns:
        List[schemas.HubDetail]: A list of hubs with their metadata.

    Raises:
        HTTPException: 403 if subscription is inactive, 502 for upstream errors.
    """
    if not is_subscription_active(current_user):
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    try:
        client = AjaxClient()
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
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information for a specific hub.

    Args:
        hub_id: Unique identifier of the hub.
        current_user: The authenticated user.

    Returns:
        schemas.HubDetail: Hub specific detail.
    """
    if not is_subscription_active(current_user):
        raise HTTPException(status_code=403, detail="Active subscription required")
        
    try:
        client = AjaxClient()
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
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve security groups and partitions for a specific hub.

    Args:
        hub_id: Unique identifier of the hub.
        current_user: The authenticated user.

    Returns:
        List[schemas.GroupBase]: List of groups configured in the hub.
    """
    if not is_subscription_active(current_user):
        raise HTTPException(status_code=403, detail="Active subscription required")

    try:
        client = AjaxClient()
        response = await client.get_hub_groups(user_email=current_user.email, hub_id=hub_id)
        return response.get("groups", []) if isinstance(response, dict) else response
    except Exception as e:
        handle_ajax_error(e)

@router.get(
    "/hubs/{hub_id}/devices", 
    response_model=List[schemas.DeviceDetail],
    summary="List Hub Devices",
    responses={
        403: {"model": ErrorMessage, "description": "Subscription inactive"},
        502: {"model": ErrorMessage, "description": "Upstream Ajax API error"}
    }
)
async def read_hub_devices(
    hub_id: str = Path(..., description="ID of the Hub to query devices from", example="0004C602"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch all devices currently linked to the specified hub.

    Args:
        hub_id: Unique identifier of the hub.
        current_user: The authenticated user.

    Returns:
        List[schemas.DeviceDetail]: Detailed list of devices.
    """
    if not is_subscription_active(current_user):
        raise HTTPException(status_code=403, detail="Active subscription required")

    try:
        client = AjaxClient()
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
    db: AsyncSession = Depends(get_db),
):
    """
    Get all technical and telemetry data for a specific device.
    """
    if not is_subscription_active(current_user):
        raise HTTPException(status_code=403, detail="Active subscription required")
        
    try:
        client = AjaxClient()
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

@router.get(
    "/hubs/{hub_id}/logs", 
    response_model=schemas.EventLogList,
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
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve event logs and history for a specific hub with pagination support.

    Args:
        hub_id: Unique identifier of the hub.
        limit: Max number of logs to return.
        offset: Pagination offset.
        current_user: The authenticated user.

    Returns:
        schemas.EventLogList: Container with log entries and total count.
    """
    if not is_subscription_active(current_user):
        raise HTTPException(status_code=403, detail="Active subscription required")

    try:
        client = AjaxClient()
        raw_data = await client.get_hub_logs(
            user_email=current_user.email, 
            hub_id=hub_id, 
            limit=limit, 
            offset=offset
        )
        
        # Diagnostic logging
        logger.info(f"raw_data type: {type(raw_data)}")
        if isinstance(raw_data, list):
            logger.info(f"raw_data is a list of length {len(raw_data)}")
            # If it's a list, we might need to wrap it for EventLogList
            validated_data = {"logs": raw_data, "total_count": len(raw_data)}
        else:
            logger.info(f"raw_data keys: {raw_data.keys() if isinstance(raw_data, dict) else 'N/A'}")
            validated_data = raw_data

        # Explicitly validate to capture detailed errors in logs
        try:
            return schemas.EventLogList.model_validate(validated_data)
        except Exception as ve:
            logger.error(f"Pydantic Validation Error for Hub Logs ({hub_id}): {ve}")
            raise ve
            
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
async def set_hub_arm_state(
    request: Request,
    hub_id: str = Path(..., description="ID of the Hub to control", example="0004C602"),
    command: schemas.HubCommandRequest = Body(..., description="Arming command details"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Set the arming state for a specific hub or security group.

    This command supports the following **arming states**:
    - `0`: **DISARMED** - Deactivate security.
    - `1`: **ARMED** - Fully activate security.
    - `2`: **NIGHT_MODE** - Activate partial/stay mode.

    If `groupId` is provided in the request body, the command will only affect that specific partition. 
    Otherwise, the command applies to the entire Hub.
    """
    if not is_subscription_active(current_user):
        raise HTTPException(status_code=403, detail="Active subscription required")

    try:
        client = AjaxClient()
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
            severity="WARNING", # Commands are altidude-level actions
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
