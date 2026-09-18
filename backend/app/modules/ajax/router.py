import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from redis.asyncio import Redis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import unquote

import json
from fastapi.responses import StreamingResponse
from backend.app.shared.infrastructure.redis.deps import get_redis
from backend.app.shared.infrastructure.redis.rate_limiter import global_ajax_rate_limiter
from backend.app.shared.infrastructure.ajax.deps import get_ajax_client
from backend.app.shared.infrastructure.database.session import get_db
from backend.app.modules.auth import service as auth_service
from backend.app.modules.billing import service as billing_service
from backend.app.modules.ajax import service as ajax_service
from backend.app.modules.ajax.models import AjaxHubState, AjaxSQSEvent, UserHub, UserWebhook
from backend.app.modules.ajax.schemas import (
    HubDetail, DeviceListItem, DeviceDetail,
    HubCommandRequest, CommandResponse, EventLogResponse, EventLog,
    GroupBase, Room,
    HubLastState, SQSEventItem, SQSEventListResponse,
    HybridEventLog, HybridEventListResponse, SyncLogsResponse,
    WebhookCreate, WebhookResponse
)
from backend.app.modules.ajax.sqs_service import normalize_ajax_event

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["AjaxSecurFlow API"],
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
    
    hubs = await ajax.get_hubs(user_email=current_user.email)
    
    # Background sync of UserHub mapping for SQS consumer
    # We don't await this to keep the API response snappy
    asyncio.create_task(ajax.sync_user_hubs(current_user.id, current_user.email))
    
    return hubs

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
    Served primarily from local storage (ingested in real time via Amazon SQS).
    If no local logs exist yet for this hub, falls back to the Ajax Systems API.
    
    **Required Plan**: Basic or higher
    
    **Plan Access**:
    - ❌ Free
    - ✅ Basic
    - ✅ Pro
    - ✅ Premium
    
    **Returns**: Paginated list of events with timestamps, types, and details.
    """,
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
    db: AsyncSession = Depends(get_db),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "read_logs"):
        raise HTTPException(status_code=403, detail="Logs access not included in your plan")

    # 1. Try local PostgreSQL records (ingested via SQS)
    total_count = 0
    try:
        total_q = await db.execute(
            select(func.count(AjaxSQSEvent.id)).where(AjaxSQSEvent.hub_id == hub_id)
        )
        val = total_q.scalar()
        if isinstance(val, (int, float)):
            total_count = int(val)
    except Exception:
        total_count = 0

    if total_count > 0:
        try:
            stmt = (
                select(AjaxSQSEvent)
                .where(AjaxSQSEvent.hub_id == hub_id)
                .order_by(AjaxSQSEvent.received_at.desc())
                .limit(limit)
                .offset(offset)
            )
            events_res = await db.execute(stmt)
            sqs_events = events_res.scalars().all()

            mapped_logs: List[EventLog] = []
            for e in sqs_events:
                normalized = normalize_ajax_event(
                    hub_id=e.hub_id,
                    event_type=e.event_type,
                    body=e.payload or {},
                    event_id=str(e.id),
                    received_at=e.received_at
                )
                payload_dict = e.payload if isinstance(e.payload, dict) else {}
                evt_obj = (payload_dict.get("event") or payload_dict.get("data") or {}) if isinstance(payload_dict, dict) else {}
                recipient_obj = payload_dict.get("recipient", {}) if isinstance(payload_dict, dict) else {}

                user_name = (
                    evt_obj.get("sourceObjectName") 
                    or evt_obj.get("userName") 
                    or recipient_obj.get("name")
                )
                device_name = (
                    evt_obj.get("deviceName") 
                    or evt_obj.get("sourceObjectName") 
                    or evt_obj.get("tag")
                )

                can_view_media = billing_service.can_access_feature(current_user, "read_logs")
                mapped_logs.append(EventLog(
                    id=str(e.id),
                    hub_id=e.hub_id,
                    timestamp=normalized.get("timestamp"),
                    event_code=e.event_type,
                    event_desc=normalized.get("description"),
                    user_name=user_name,
                    device_name=device_name,
                    transition=evt_obj.get("transition"),
                    media_urls=normalized.get("media_urls", []) if can_view_media else []
                ))

            return EventLogResponse(logs=mapped_logs, total_count=total_count)
        except Exception as err:
            logger.warning(f"Error querying local SQS logs for hub {hub_id}: {err}. Falling back to Ajax API.")

    # 2. Fallback to upstream Ajax Systems API
    return await ajax.get_hub_logs(user_email=current_user.email, hub_id=hub_id, limit=limit, offset=offset)


@router.post(
    "/hubs/{hub_id}/logs/sync",
    response_model=SyncLogsResponse,
    summary="Synchronize historical hub logs from Ajax API (Backup)",
    description="""
    Explicit backup sync: queries the official Ajax Systems API for historical logs
    and persists any missing events to the local database.
    
    **Required Plan**: Basic or higher
    """,
    responses={
        200: {"description": "Logs synchronized successfully"},
        403: {"description": "Logs access not included in your plan"},
        404: {"description": "Hub not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def sync_hub_logs(
    hub_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: ajax_service.AjaxClient = Depends(get_ajax_client),
    db: AsyncSession = Depends(get_db),
    _ = Depends(global_ajax_rate_limiter)
):
    if not billing_service.can_access_feature(current_user, "read_logs"):
        raise HTTPException(status_code=403, detail="Logs access not included in your plan")

    ownership = await db.execute(
        select(UserHub.id).where(
            UserHub.user_id == current_user.id,
            UserHub.hub_id == hub_id
        ).limit(1)
    )
    if ownership.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Hub not found")

    # Fetch from Ajax Systems API
    remote_data = await ajax.get_hub_logs(user_email=current_user.email, hub_id=hub_id, limit=limit, offset=0)
    remote_logs = remote_data.logs if hasattr(remote_data, "logs") else []

    imported_count = 0
    from datetime import datetime as dt_datetime, timezone
    
    for r_log in remote_logs:
        sync_msg_id = f"sync_{hub_id}_{r_log.id}"
        # Check if already exists
        exists_stmt = select(AjaxSQSEvent.id).where(AjaxSQSEvent.message_id == sync_msg_id).limit(1)
        existing = await db.execute(exists_stmt)
        if existing.scalar_one_or_none() is None:
            log_dict = r_log.model_dump() if hasattr(r_log, "model_dump") else dict(r_log)
            new_event = AjaxSQSEvent(
                message_id=sync_msg_id,
                event_type=str(r_log.event_code or r_log.event_desc or "HISTORICAL"),
                hub_id=hub_id,
                ajax_event_id=str(r_log.id),
                payload={"event": log_dict, "source": "ajax_api_backup_sync"},
                processed_at=dt_datetime.now(timezone.utc)
            )
            db.add(new_event)
            imported_count += 1

    if imported_count > 0:
        await db.commit()

    return SyncLogsResponse(
        success=True,
        imported_count=imported_count,
        message=f"Synchronized {imported_count} new historical events from Ajax Systems."
    )



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

# --- SQS Events / Last Known Hub State ---

@router.get(
    "/events/state",
    response_model=List[HubLastState],
    summary="Get last known state of user's hubs",
    description="""
    Get the last known state of every hub linked to the authenticated user,
    fed in near real-time by the Ajax SQS events consumer.

    **Required Plan**: Free or higher

    **Returns**: One entry per hub with the last event type and its timestamp.
    """,
    responses={
        200: {"description": "Hub states retrieved successfully"},
        403: {"description": "Hub access not included in your plan"}
    }
)
async def get_hub_states(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not billing_service.can_access_feature(current_user, "list_hubs"):
        raise HTTPException(status_code=403, detail="Hub access not included in your plan")

    stmt = (
        select(AjaxHubState, UserHub.hub_name)
        .join(UserHub, UserHub.hub_id == AjaxHubState.hub_id)
        .where(UserHub.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    return [
        HubLastState(
            hub_id=state.hub_id,
            hub_name=hub_name,
            last_event_type=state.last_event_type,
            updated_at=state.updated_at
        )
        for state, hub_name in result.all()
    ]

@router.get(
    "/hubs/{hub_id}/events",
    response_model=SQSEventListResponse,
    summary="Get stored SQS events for a hub",
    description="""
    Get the history of events received via Amazon SQS for a specific hub,
    newest first. Raw payloads are stored for auditing but never exposed here.

    **Required Plan**: Basic or higher
    """,
    responses={
        200: {"description": "Events retrieved successfully"},
        403: {"description": "Events access not included in your plan"},
        404: {"description": "Hub not found"}
    }
)
async def get_hub_sqs_events(
    hub_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not billing_service.can_access_feature(current_user, "read_logs"):
        raise HTTPException(status_code=403, detail="Events access not included in your plan")

    # Ownership check: the hub must be linked to the requesting user.
    # 404 (not 403) to avoid leaking the existence of other users' hubs.
    ownership = await db.execute(
        select(UserHub.id).where(
            UserHub.user_id == current_user.id,
            UserHub.hub_id == hub_id
        ).limit(1)
    )
    if ownership.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Hub not found")

    total = await db.execute(
        select(func.count(AjaxSQSEvent.id)).where(AjaxSQSEvent.hub_id == hub_id)
    )
    events = await db.execute(
        select(AjaxSQSEvent)
        .where(AjaxSQSEvent.hub_id == hub_id)
        .order_by(AjaxSQSEvent.received_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return SQSEventListResponse(
        events=[SQSEventItem.model_validate(e) for e in events.scalars().all()],
        total_count=total.scalar() or 0
    )

# --- Real-Time Streaming (SSE) ---

@router.get(
    "/events/stream",
    summary="Real-time Server-Sent Events (SSE) Stream",
    description="""
    Streaming endpoint emitting real-time Ajax events for the authenticated user's hubs.
    Uses Redis Pub/Sub channels. Ideal for dashboard real-time updates and lightweight consumers.
    
    **Required Plan**: Basic or higher
    """,
    responses={
        200: {"description": "SSE stream established"},
        403: {"description": "Streaming access not included in your plan"}
    }
)
async def stream_events(
    request: Request,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    redis_client: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db)
):
    if not billing_service.can_access_feature(current_user, "read_logs"):
        raise HTTPException(status_code=403, detail="Events streaming not included in your plan")

    # Find hubs belonging to this user
    hubs_q = await db.execute(select(UserHub.hub_id).where(UserHub.user_id == current_user.id))
    user_hub_ids = list(hubs_q.scalars().all())

    if not user_hub_ids:
        async def empty_stream():
            yield f": connected, no hubs found for user {current_user.email}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                await asyncio.sleep(15)
                yield ": ping\n\n"
        return StreamingResponse(
            empty_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    channels = [f"hub_events:{hid}" for hid in user_hub_ids]
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(*channels)

    async def event_generator():
        try:
            yield f": connected to {len(channels)} hub channels\n\n"
            while True:
                if await request.is_disconnected():
                    logger.debug(f"Client disconnected from SSE stream: {current_user.email}")
                    break

                try:
                    message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=15.0)
                    if message and message.get("type") == "message":
                        data_str = message.get("data")
                        if isinstance(data_str, bytes):
                            data_str = data_str.decode("utf-8")
                        yield f"event: ajax_event\ndata: {data_str}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# --- User Webhooks (Home Assistant & External Integrations) ---

@router.get(
    "/webhooks",
    response_model=List[WebhookResponse],
    summary="List registered webhooks",
    description="""
    List external webhooks configured for this user account.
    
    **Required Plan**: Pro or higher
    """
)
async def list_webhooks(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not billing_service.can_access_feature(current_user, "manage_webhooks"):
        raise HTTPException(status_code=403, detail="Webhook management requires a PRO or PREMIUM subscription.")

    result = await db.execute(
        select(UserWebhook)
        .where(UserWebhook.user_id == current_user.id)
        .order_by(UserWebhook.created_at.desc())
    )
    return result.scalars().all()

@router.post(
    "/webhooks",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new external webhook",
    description="""
    Register a webhook URL (e.g. Home Assistant) to receive real-time event notifications.
    
    **Required Plan**: Pro or higher
    """
)
async def create_webhook(
    webhook_in: WebhookCreate,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not billing_service.can_access_feature(current_user, "manage_webhooks"):
        raise HTTPException(status_code=403, detail="Webhook management requires a PRO or PREMIUM subscription.")

    if webhook_in.hub_id:
        ownership = await db.execute(
            select(UserHub.id).where(
                UserHub.user_id == current_user.id,
                UserHub.hub_id == webhook_in.hub_id
            ).limit(1)
        )
        if ownership.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail=f"Hub {webhook_in.hub_id} not found in your account.")

    new_webhook = UserWebhook(
        user_id=current_user.id,
        hub_id=webhook_in.hub_id,
        target_url=webhook_in.target_url.strip(),
        secret_token=webhook_in.secret_token.strip() if webhook_in.secret_token else None,
        description=webhook_in.description.strip() if webhook_in.description else None,
        is_active=True
    )
    db.add(new_webhook)
    await db.commit()
    await db.refresh(new_webhook)
    return new_webhook

@router.delete(
    "/webhooks/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a webhook",
    description="""
    Delete an existing webhook.
    
    **Required Plan**: Pro or higher
    """
)
async def delete_webhook(
    webhook_id: int,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not billing_service.can_access_feature(current_user, "manage_webhooks"):
        raise HTTPException(status_code=403, detail="Webhook management requires a PRO or PREMIUM subscription.")

    webhook = await db.get(UserWebhook, webhook_id)
    if not webhook or webhook.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Webhook not found.")

    await db.delete(webhook)
    await db.commit()
    return None

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
