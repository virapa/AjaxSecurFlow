from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.v1.auth import get_current_user
from backend.app.core.db import get_db
from backend.app.domain.models import User
from backend.app.services.ajax_client import AjaxClient, AjaxAuthError
from backend.app.services.billing_service import is_subscription_active
from backend.app.services import audit_service
from backend.app.schemas import ajax as schemas
from backend.app.schemas.auth import ErrorMessage

router = APIRouter()

def handle_ajax_error(e: Exception) -> None:
    """
    Standardize exception handling for Ajax API calls.
    """
    if isinstance(e, AjaxAuthError):
        raise HTTPException(status_code=502, detail="Upstream authentication failed")
    raise HTTPException(status_code=502, detail=str(e))

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
    hub_id: str,
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
        return await client.get_hub_details(user_email=current_user.email, hub_id=hub_id)
    except Exception as e:
        handle_ajax_error(e)

@router.get("/hubs/{hub_id}/groups", response_model=List[schemas.GroupBase])
async def read_hub_groups(
    hub_id: str,
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

@router.get("/hubs/{hub_id}/devices", response_model=List[schemas.DeviceDetail])
async def read_hub_devices(
    hub_id: str,
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

@router.get("/hubs/{hub_id}/logs", response_model=schemas.EventLogList)
async def read_hub_logs(
    hub_id: str,
    limit: int = 100,
    offset: int = 0,
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
        return await client.get_hub_logs(
            user_email=current_user.email, 
            hub_id=hub_id, 
            limit=limit, 
            offset=offset
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
async def set_hub_arm_state(
    hub_id: str,
    command: schemas.HubCommandRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Set the arming state (Arm, Disarm, Night) for a specific hub or group.

    Args:
        hub_id: Unique identifier of the hub.
        command: Request body with armState and optional groupId.
        request: The incoming FastAPI request.
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
