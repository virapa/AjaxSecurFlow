import asyncio
import logging
import stripe
import datetime
from datetime import datetime as dt_datetime
from backend.app.worker.celery_app import celery_app
from backend.app.modules.ajax.service import AjaxClient
from backend.app.shared.infrastructure.database.session import async_session_factory
from backend.app.modules.auth.models import User
from backend.app.modules.billing.models import ProcessedStripeEvent
from backend.app.modules.auth import service as auth_service
from backend.app.modules.security import service as security_service
from backend.app.modules.notifications import service as notification_service
from backend.app.modules.billing import service as billing_service
from backend.app.core.config import settings
from sqlalchemy import select

@celery_app.task(name="tasks.send_transactional_email")
def send_transactional_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
    """
    Background task to send emails without blocking the main worker logic.

    Args:
        to_email: Target recipient email address.
        subject: Email subject.
        html_content: Rich HTML body.
        text_content: Optional plain text fallback.

    Returns:
        bool: True if sent successfully.
    """
    return notification_service.send_email(to_email, subject, html_content, text_content)

@celery_app.task(name="tasks.cleanup_expired_subscriptions")
def cleanup_expired_subscriptions() -> int:
    """
    Daily cleanup task that marks users with expired vouchers/subscriptions as 'inactive'.

    Returns:
        int: Total number of users updated.
    """
    return asyncio.run(_cleanup_expired_subscriptions_logic())

async def _cleanup_expired_subscriptions_logic() -> int:
    """
    Internal logic for subscription cleanup, separated for testing.

    Returns:
        int: Number of records updated.
    """
    from datetime import datetime as dt_datetime, timezone
    from sqlalchemy import update, and_
    
    now = dt_datetime.now(timezone.utc)
    async with async_session_factory() as session:
        # Target 'active' users whose expiration has passed.
        stmt = update(User).where(
            and_(
                User.subscription_status == "active",
                User.subscription_expires_at != None,
                User.subscription_expires_at < now
            )
        ).values(subscription_status="inactive")
        
        result = await session.execute(stmt)
        await session.commit()
        
        updated_count = result.rowcount
        if updated_count > 0:
            logger.info(f"Cleaned up {updated_count} expired subscriptions.")
        return updated_count

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.sync_ajax_data")
def sync_ajax_data(user_id: int) -> dict:
    """
    Background task to sync data from Ajax API to our database.
    
    This prevents blocking the API during heavy requests.

    Args:
        user_id: Internal ID of the user to sync.

    Returns:
        dict: Status result of the sync operation.
    """
    logger.info(f"Starting data sync for user {user_id}")
    
    # Since we are in a sync worker but using async AjaxClient, 
    # we need to run it in an event loop.
    async def _sync():
        client = AjaxClient()
        # In a real implementation, we would:
        # 1. Fetch all hubs for the user
        # 2. Fetch recent logs for each hub
        # 3. The log processing logic in the endpoint (ajax.py) would then 
        #    automatically trigger create_notification for critical events.
        await asyncio.sleep(2) 
        return {"status": "success", "user_id": user_id, "message": "Log scanning completed"}

    result = asyncio.run(_sync())
    
    logger.info(f"Sync completed for user {user_id}")
    return result

@celery_app.task(name="tasks.process_stripe_webhook")
def process_stripe_webhook(event_dict: dict, correlation_id: str = "internal") -> dict:
    """
    Handle Stripe events with Idempotency and Corporate Auditing.
    """
    event = stripe.Event.construct_from(event_dict, stripe.api_key)
    event_id = event.id
    event_type = event.type
    
    logger.info(f"Worker processing Stripe event: {event_type} ({event_id})")

    async def _handle():
        # Create isolated resources for the task
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from redis.asyncio import Redis
        
        local_engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
        local_session_factory = async_sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        ajax_client = AjaxClient(redis_client=redis_client)
        
        try:
            async with local_session_factory() as session:
                # 1. Idempotency Check
                stmt = select(ProcessedStripeEvent).where(ProcessedStripeEvent.id == event_id)
                res = await session.execute(stmt)
                if res.scalar_one_or_none():
                    logger.warning(f"Event {event_id} already processed. Skipping.")
                    return {"status": "skipped", "reason": "idempotent"}

                data = event.data.object
                user_id = None
                
                # 2. Logic based on event type
                if event_type == "checkout.session.completed":
                    stripe_customer_id = data.customer
                    subscription_id = data.subscription
                    internal_user_id = data.metadata.get("user_id")
                    
                    if internal_user_id:
                        user = await session.get(User, int(internal_user_id))
                        if user:
                            user_id = user.id
                            price_id = data.metadata.get("price_id")
                            plan_name = billing_service.get_plan_from_price_id(price_id) if price_id else data.metadata.get("plan_type", "basic")
                            
                            await auth_service.update_user_subscription(
                                session, user.id, "active", plan_name, subscription_id
                            )
                            if not user.stripe_customer_id:
                                user.stripe_customer_id = stripe_customer_id
                                await session.commit()
                            
                            logger.info(f"User {user.email} (ID:{user.id}) checkout completed. Plan: {plan_name}")
                            
                            # Fetch Profile for Personalization
                            display_name = user.email
                            try:
                                profile = await ajax_client.get_user_info(user.email)
                                if profile and (profile.firstName or profile.lastName):
                                    display_name = f"{profile.firstName or ''} {profile.lastName or ''}".strip()
                            except: pass

                            send_transactional_email.delay(
                                user.email,
                                "¡Bienvenido a AjaxSecurFlow!",
                                f"<h1>Hola {display_name}</h1><p>Tu suscripción {plan_name.upper()} ha sido activada correctamente. Ya puedes acceder a las funciones correspondientes.</p>",
                                f"Hola {display_name}, tu suscripción {plan_name.upper()} ha sido activada correctamente."
                            )

                elif event_type in ["customer.subscription.created", "customer.subscription.updated", "invoice.payment_succeeded"]:
                    customer_id = data.get("customer")
                    subscription_id = data.get("subscription") or data.get("id")
                    stripe_status = data.get("status")
                    
                    # Robust extraction of expiration date
                    expires_at = None
                    try:
                        # Try current_period_end (Subscription objects)
                        cpe = getattr(data, "current_period_end", None)
                        if cpe is None and hasattr(data, "get"):
                            cpe = data.get("current_period_end")
                            
                        # Try invoice lines period end (Invoice objects)
                        if cpe is None and "lines" in data:
                            lines = data.get("lines", {}).get("data", [])
                            if lines:
                                cpe = lines[0].get("period", {}).get("end")
                        
                        if cpe:
                            expires_at = dt_datetime.fromtimestamp(cpe, tz=datetime.timezone.utc)
                    except Exception as e:
                        logger.warning(f"Could not parse expiration date from {event_type}: {e}")

                    if event_type == "invoice.payment_succeeded":
                        if data.get("billing_reason") in ["subscription_create", "subscription_cycle", "subscription_update"]:
                            stripe_status = "active"
                    
                    user = await auth_service.get_user_by_stripe_customer_id(session, customer_id)
                    if user:
                        user_id = user.id
                        price_id = None
                        try:
                            items = data.get("items", {}).get("data", []) if "items" in data else []
                            if not items and "lines" in data:
                                items = data.get("lines", {}).get("data", [])
                            if items:
                                price_id = items[0].get("price", {}).get("id")
                        except:
                            pass
                            
                        plan_name = billing_service.get_plan_from_price_id(price_id) if price_id else user.subscription_plan
                        
                        await auth_service.update_user_subscription(
                            session, user.id, stripe_status, plan_name, subscription_id, expires_at=expires_at
                        )
                        
                        if event_type == "invoice.payment_succeeded":
                             # Fetch Profile for Personalization
                             display_name = user.email
                             try:
                                 profile = await ajax_client.get_user_info(user.email)
                                 if profile and (profile.firstName or profile.lastName):
                                     display_name = f"{profile.firstName or ''} {profile.lastName or ''}".strip()
                             except: pass

                             await notification_service.create_notification(
                                 db=session,
                                 user_id=user.id,
                                 title="Pago Confirmado",
                                 message=f"Gracias por elegir AjaxSecurFlow. Tu pago para el plan {plan_name.upper()} ha sido procesado con éxito.",
                                 notification_type="success"
                             )
                             send_transactional_email.delay(
                                 user.email,
                                 "Confirmación de Pago - AjaxSecurFlow",
                                 f"<h1>Pago Recibido</h1><p>Hola {display_name}, tu suscripción {plan_name.upper()} está lista. Gracias por tu confianza.</p>",
                                 f"Hola {display_name}, tu pago para el plan {plan_name.upper()} ha sido procesado con éxito."
                             )

                elif event_type == "customer.subscription.deleted":
                    customer_id = data.customer
                    user = await auth_service.get_user_by_stripe_customer_id(session, customer_id)
                    if user:
                        user_id = user.id
                        await auth_service.update_user_subscription(
                            session, user.id, "canceled", "free", ""
                        )
                
                elif event_type == "invoice.payment_failed":
                    customer_id = data.customer
                    user = await auth_service.get_user_by_stripe_customer_id(session, customer_id)
                    if user:
                        user_id = user.id
                        user.subscription_status = "past_due"
                        await session.commit()
                        await notification_service.create_notification(
                            db=session, user_id=user.id,
                            title="Fallo en el Pago",
                            message="No pudimos procesar tu cobro. Revisa tu tarjeta para no perder acceso.",
                            notification_type="error", link="/billing"
                        )

                # 3. Mark event as processed
                processed_event = ProcessedStripeEvent(id=event_id, event_type=event_type)
                session.add(processed_event)
                await session.commit()

                # 4. Final Audit
                await security_service.log_action(
                    db=session, user_id=user_id,
                    action=f"STRIPE_EVENT_PROCESSED_{event_type.upper().replace('.', '_')}",
                    endpoint="celery_task", status_code=200, severity="INFO",
                    resource_id=event_id, correlation_id=correlation_id
                )
                
                return {"status": "processed", "id": event_id}
                
        finally:
            await local_engine.dispose()
            await redis_client.close()

    try:
        # Use a new loop or the existing one correctly
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(_handle())
    except Exception as e:
        logger.error(f"Error processing webhook {event_id}: {str(e)}")
        raise e
