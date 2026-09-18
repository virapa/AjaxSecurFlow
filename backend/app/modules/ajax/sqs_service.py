import json
import logging
import asyncio
import boto3
import redis.asyncio as aioredis
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings
from backend.app.modules.ajax.models import AjaxSQSEvent, AjaxHubState, UserHub, UserWebhook
from backend.app.modules.auth.models import User
from backend.app.modules.notifications import service as notification_service

logger = logging.getLogger(__name__)

def normalize_ajax_event(
    hub_id: str,
    event_type: str,
    body: Dict[str, Any],
    event_id: Optional[str] = None,
    received_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Normalizes incoming Ajax SQS event into the Hybrid Envelope standard.
    Guarantees stable schema for UI & Home Assistant while preserving the 100% untouched raw payload in `data`.
    """
    event_data = body.get('event') or body.get('data') or {}
    ts = (
        event_data.get('timestamp') 
        or body.get('timestamp') 
        or (received_at.isoformat() if received_at else datetime.now(timezone.utc).isoformat())
    )
    if isinstance(ts, (int, float)):
        try:
            # SQS timestamps from Ajax are in milliseconds (> 1e11)
            ts_sec = (ts / 1000.0) if ts > 1e11 else float(ts)
            ts = datetime.fromtimestamp(ts_sec, tz=timezone.utc).isoformat()
        except Exception:
            ts = datetime.now(timezone.utc).isoformat()

    clean_type = str(event_type).upper()
    tag = str(event_data.get("eventTag") or event_data.get("tag") or "")
    obj_name = str(event_data.get("sourceObjectName") or "")
    room_name = str(event_data.get("sourceRoomName") or "").strip()
    transition = str(event_data.get("transition") or "")
    location = f", {obj_name} en {room_name}" if (obj_name and room_name) else (f", {obj_name}" if obj_name else "")

    # Human-friendly descriptions aligned with Ajax PRO Desktop/Mobile
    if event_data.get("description"):
        desc = event_data.get("description")
    elif tag == "ExtContactOpened":
        if transition == "RECOVERED":
            desc = f"Contacto externo cerrado{location}"
        else:
            desc = f"Contacto externo abierto{location}"
    elif tag == "MotionDetected":
        desc = f"Movimiento detectado{location}"
    elif tag.lower() in ["disarm", "disarmed"] or clean_type in ["DISARM", "DISARMED"]:
        desc = f"Desarmado por {obj_name}" if obj_name else "Desarmado"
    elif tag.lower() in ["arm", "armed"] or clean_type in ["ARM", "ARMED"]:
        desc = f"Armado por {obj_name}" if obj_name else "Armado"
    elif tag == "AutomaticBypassOff":
        desc = f"Restaurado después de la desactivación automática{location}"
    elif tag == "RelayOnByScenario":
        desc = f"{obj_name} en {room_name} activado por escenario" if (obj_name and room_name) else f"{obj_name} activado por escenario"
    else:
        desc = tag or (f"{clean_type}{location}" if location else f"Evento {clean_type}")

    severity = "info"
    title = f"Evento {clean_type}"
    if "RECOVER" in clean_type or transition == "RECOVERED":
        severity = "success"
        title = "Restablecido"
    elif "ALARM" in clean_type:
        severity = "critical"
        title = "🛑 ALARMA DETECTADA"
    elif tag.lower() in ["disarm", "disarmed"] or clean_type in ["DISARM", "DISARMED"]:
        severity = "info"
        title = "🔓 Sistema Desarmado"
    elif tag.lower() in ["arm", "armed"] or clean_type in ["ARM", "ARMED"]:
        severity = "success"
        title = "🔐 Sistema Armado"
    elif any(k in clean_type for k in ["POWER", "BATTERY", "FAIL", "TAMPER", "OFFLINE", "MALFUNCTION"]):
        severity = "warning"
        title = f"⚠️ Advertencia: {clean_type}"

    # Extract ready media URLs (MotionCam photos or scenario media)
    media_urls: List[str] = []
    add_data = event_data.get("additionalData") or {}
    if isinstance(add_data, dict):
        links = add_data.get("orderedResourceLinks") or []
        if isinstance(links, list):
            for item in links:
                if isinstance(item, dict) and item.get("status") == "READY" and item.get("url"):
                    media_urls.append(item["url"])

    if not media_urls:
        add_data_v2 = event_data.get("additionalDataV2") or []
        if isinstance(add_data_v2, list):
            for v2_group in add_data_v2:
                if isinstance(v2_group, dict):
                    v2_links = v2_group.get("orderedResourceLinks") or []
                    if isinstance(v2_links, list):
                        for item in v2_links:
                            if isinstance(item, dict) and item.get("status") == "READY" and item.get("url"):
                                media_urls.append(item["url"])

    return {
        "id": str(event_id or f"evt_{int(datetime.now(timezone.utc).timestamp()*1000)}"),
        "hub_id": str(hub_id),
        "event_type": clean_type,
        "title": title,
        "description": desc,
        "severity": severity,
        "timestamp": str(ts),
        "media_urls": media_urls,
        "source": "sqs",
        "data": body
    }

class AjaxEventsConsumer:
    """
    Dedicated worker to consume events from Ajax SQS queue.

    Processing pipeline per message:
    1. Audit: persist the raw event (idempotent on SQS MessageId).
    2. State: upsert the hub's last known state (every event, always).
    3. Notify: create in-app notifications for active subscribers of the hub.
    4. Cache: invalidate stale hub caches so the REST API reflects the new state.
    5. Ack: delete the message from SQS.
    """
    def __init__(self):
        self._setup_aws()
        self.engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.redis: Optional[aioredis.Redis] = None
        try:
            self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis unavailable for cache invalidation: {e}")
        self._running = True

    def _setup_aws(self):
        if not all([settings.AWS_KEY_ID, settings.AWS_SECRET_KEY, settings.AWS_EVENTS_QUEUE]):
            logger.error("AWS SQS credentials not fully configured.")
            raise RuntimeError("SQS integration requires AWS_KEY_ID, AWS_SECRET_KEY, and AWS_EVENTS_QUEUE")

        self.sqs = boto3.client(
            'sqs',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_KEY_ID.get_secret_value(),
            aws_secret_access_key=settings.AWS_SECRET_KEY.get_secret_value()
        )
        # AWS_EVENTS_QUEUE may be either the full QueueUrl or the queue name.
        if settings.AWS_EVENTS_QUEUE.startswith("http"):
            self.queue_url = settings.AWS_EVENTS_QUEUE
        else:
            try:
                res = self.sqs.get_queue_url(QueueName=settings.AWS_EVENTS_QUEUE)
                self.queue_url = res['QueueUrl']
            except Exception as e:
                logger.error(f"Failed to get SQS Queue URL: {e}")
                raise

    def stop(self):
        self._running = False

    async def poll(self):
        """
        Main long-polling loop. boto3 calls are synchronous, so they run in a
        thread to avoid blocking the event loop.
        """
        logger.info(f"Starting SQS polling for queue: {settings.AWS_EVENTS_QUEUE}")
        while self._running:
            try:
                response = await asyncio.to_thread(
                    self.sqs.receive_message,
                    QueueUrl=self.queue_url,
                    AttributeNames=['All'],
                    MaxNumberOfMessages=settings.SQS_MAX_MESSAGES,
                    WaitTimeSeconds=settings.SQS_WAIT_TIME_SECONDS
                )

                messages = response.get('Messages', [])
                if not messages:
                    continue

                logger.info(f"Received {len(messages)} messages from SQS")
                for msg in messages:
                    await self._process_message(msg)

            except asyncio.CancelledError:
                logger.info("SQS polling cancelled. Shutting down.")
                raise
            except Exception as e:
                logger.error(f"Error in SQS polling loop: {e}")
                await asyncio.sleep(5)

    async def _delete_message(self, receipt_handle: str):
        await asyncio.to_thread(
            self.sqs.delete_message,
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle
        )

    async def _process_message(self, message: Dict[str, Any]):
        message_id = message['MessageId']
        receipt_handle = message['ReceiptHandle']

        try:
            body = json.loads(message['Body'])
            # Real Ajax CAPI payload shape: {"recipient": {...}, "event": {hubId, eventType, eventId, ...}}.
            # Ajax fans out one SQS message per recipient user for the same
            # logical event, so several messages can share the same eventId.
            event_data = body.get('event') or body.get('data') or {}
            hub_id = event_data.get('hubId') or body.get('hubId')
            event_type = (
                event_data.get('eventType') or event_data.get('eventTypeV2')
                or event_data.get('eventTag') or body.get('type') or body.get('event_type') or "UNKNOWN"
            )
            ajax_event_id = event_data.get('eventId')

            if not hub_id:
                logger.warning(f"Message {message_id} missing hubId. Skipping.")
                await self._delete_message(receipt_handle)
                return

            async with self.session_factory() as session:
                # 1. Auditing (OWASP 2025) - idempotency on SQS MessageId
                stmt = select(AjaxSQSEvent).where(AjaxSQSEvent.message_id == message_id)
                result = await session.execute(stmt)
                event = result.scalar_one_or_none()

                if event and event.processed_at:
                    logger.warning(f"Event {message_id} already processed. Skipping.")
                    await self._delete_message(receipt_handle)
                    return

                if not event:
                    event = AjaxSQSEvent(
                        message_id=message_id,
                        event_type=event_type,
                        hub_id=hub_id,
                        ajax_event_id=ajax_event_id,
                        payload=body
                    )
                    session.add(event)

                # 2. Last known state - every incoming event overwrites the hub state
                await self._upsert_hub_state(session, hub_id, event_type, message_id, body)

                # Persist audit + state even if notification dispatch fails later
                await session.commit()

                # Normalize event to Hybrid Envelope
                normalized_event = normalize_ajax_event(
                    hub_id=hub_id,
                    event_type=event_type,
                    body=body,
                    event_id=ajax_event_id or message_id,
                    received_at=event.received_at
                )

                # Real-time streaming: publish to Redis Pub/Sub channel for this hub
                await self._publish_to_redis(hub_id, normalized_event)

                # 3. Notifications - only for hubs owned by ACTIVE subscribers.
                # Ajax fans out one SQS message per recipient for the same event
                # (shared ajax_event_id), so skip if another message already
                # triggered the notification for this exact event.
                users = await self._find_active_users_for_hub(session, hub_id)
                if users and ajax_event_id and await self._already_notified(session, hub_id, ajax_event_id, event.id):
                    logger.info(f"Event {ajax_event_id} for hub {hub_id} already notified via another recipient message. Skipping duplicate.")
                    users = []

                if users:
                    for user in users:
                        await self._dispatch_notification(session, user, event_type, hub_id, body)

                    # External integrations (e.g. Home Assistant): dispatch to active webhooks
                    webhooks = await self._find_webhooks_for_hub(session, hub_id, [u.id for u in users])
                    for wh in webhooks:
                        try:
                            from backend.app.worker.tasks import dispatch_webhook_event
                            dispatch_webhook_event.delay(wh.id, normalized_event)
                        except Exception as wh_err:
                            logger.warning(f"Failed to enqueue webhook {wh.id}: {wh_err}")
                else:
                    logger.info(f"Event {event_type} for hub {hub_id} has no active subscribers.")

                # 4. Mark processed
                event.processed_at = datetime.now(timezone.utc)
                await session.commit()

            # 5. Cache invalidation + SQS ack (outside DB session)
            await self._invalidate_hub_caches(hub_id, [u.email for u in users])
            await self._delete_message(receipt_handle)
            logger.info(f"Event {message_id} ({event_type}) processed for hub {hub_id} ({len(users)} users notified)")

        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}")
            # Do NOT delete if failed, let visibility timeout handle retry

    async def _publish_to_redis(self, hub_id: str, event_data: Dict[str, Any]):
        """
        Publishes the normalized event to Redis Pub/Sub for SSE clients (dashboard/Home Assistant).
        """
        if not self.redis:
            return
        try:
            channel = f"hub_events:{hub_id}"
            payload_str = json.dumps(event_data, default=str)
            await self.redis.publish(channel, payload_str)
            logger.debug(f"Published event to Redis channel {channel}")
        except Exception as e:
            logger.warning(f"Failed to publish event to Redis channel hub_events:{hub_id}: {e}")

    async def _find_webhooks_for_hub(self, session: AsyncSession, hub_id: str, user_ids: List[int]) -> List[UserWebhook]:
        """
        Finds all active user webhooks registered for this hub or for all hubs of the users.
        """
        if not user_ids:
            return []
        try:
            stmt = select(UserWebhook).where(
                UserWebhook.is_active == True,
                UserWebhook.user_id.in_(user_ids),
                or_(UserWebhook.hub_id == hub_id, UserWebhook.hub_id == None)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except (Exception, StopIteration) as e:
            logger.debug(f"Failed to query webhooks for hub {hub_id}: {e}")
            return []

    async def _upsert_hub_state(
        self, session: AsyncSession, hub_id: str, event_type: str, message_id: str, payload: Dict[str, Any]
    ):
        stmt = select(AjaxHubState).where(AjaxHubState.hub_id == hub_id)
        result = await session.execute(stmt)
        state = result.scalar_one_or_none()

        if state:
            state.last_event_type = event_type
            state.last_message_id = message_id
            state.last_payload = payload
            state.updated_at = datetime.now(timezone.utc)
        else:
            session.add(AjaxHubState(
                hub_id=hub_id,
                last_event_type=event_type,
                last_message_id=message_id,
                last_payload=payload
            ))

    async def _already_notified(self, session: AsyncSession, hub_id: str, ajax_event_id: str, exclude_id: int) -> bool:
        """
        Whether another (already fully processed) SQS message already
        triggered notifications for this exact Ajax event on this hub.
        """
        stmt = select(AjaxSQSEvent.id).where(
            AjaxSQSEvent.hub_id == hub_id,
            AjaxSQSEvent.ajax_event_id == ajax_event_id,
            AjaxSQSEvent.id != exclude_id,
            AjaxSQSEvent.processed_at.isnot(None)
        ).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _find_active_users_for_hub(self, session: AsyncSession, hub_id: str) -> List[User]:
        """
        Finds all users associated with the hub who have an active subscription.
        """
        stmt = select(User).join(UserHub, UserHub.user_id == User.id).where(
            UserHub.hub_id == hub_id,
            User.subscription_status.in_(["active", "trialing"])
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def _invalidate_hub_caches(self, hub_id: str, user_emails: List[str]):
        """
        Best-effort invalidation of the REST API Redis cache so hub state
        reflects the latest event immediately.
        """
        if not self.redis or not user_emails:
            return
        try:
            keys = []
            for email in user_emails:
                keys.append(f"ajax:hub:{email}:{hub_id}")
                keys.append(f"ajax:hubs:{email}")
            await self.redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidation failed for hub {hub_id}: {e}")

    async def _dispatch_notification(self, session: AsyncSession, user: User, event_type: str, hub_id: str, payload: Dict[str, Any]):
        """
        Translates Ajax events to human-readable notifications.
        """
        title = "Evento de Seguridad"
        severity = "info"

        # Basic mapping (Should be expanded)
        content_map = {
            "ALARM": ("🛑 ALARMA DETECTADA", "Se ha disparado una alarma en el hub {hub_id}. Por favor, verifique el estado.", "error"),
            "ARMED": ("🔐 Sistema Armado", "El sistema ha sido armado correctamente.", "success"),
            "DISARMED": ("🔓 Sistema Desarmado", "El sistema ha sido desarmado.", "info"),
            "POWER_LOSS": ("⚠️ Corte de Energía", "Se ha detectado una pérdida de alimentación externa en el hub.", "warning"),
        }

        display_title, message_template, n_type = content_map.get(event_type.upper(), (title, f"Nuevo evento técnico: {event_type}", severity))

        message = message_template.format(hub_id=hub_id)

        await notification_service.create_notification(
            db=session,
            user_id=user.id,
            title=display_title,
            message=message,
            notification_type=n_type,
            link=f"/hubs/{hub_id}"
        )

        # If it's an alarm, we might also want to send an email (Celery background)
        if n_type == "error":
            try:
                from backend.app.worker.tasks import send_transactional_email
                send_transactional_email.delay(
                    user.email,
                    f"URGENTE: {display_title}",
                    f"<h1>{display_title}</h1><p>{message}</p>",
                    message
                )
            except Exception as e:
                logger.error(f"Failed to enqueue alarm email for {user.email}: {e}")
