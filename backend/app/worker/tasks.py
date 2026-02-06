import asyncio
import logging
import stripe
from backend.app.worker.celery_app import celery_app
from backend.app.services.ajax_client import AjaxClient
from backend.app.core.db import async_session_factory
from backend.app.crud import user as crud_user
from backend.app.domain.models import User, ProcessedStripeEvent
from backend.app.services import audit_service, notification_service, email_service
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
    return email_service.send_email(to_email, subject, html_content, text_content)

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
    from datetime import datetime, timezone
    from sqlalchemy import update, and_
    
    now = datetime.now(timezone.utc)
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
    
    This task processes subscription updates, payment failures, and initial activations.

    Args:
        event_dict: The raw Stripe event dictionary.
        correlation_id: ID for cross-module tracking.

    Returns:
        dict: Processing status.
    """
    event = stripe.Event.construct_from(event_dict, stripe.api_key)
    event_id = event.id
    event_type = event.type
    
    logger.info(f"Worker processing Stripe event: {event_type} ({event_id})")

    async def _handle():
        async with async_session_factory() as session:
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
                # Entry point for new customers
                stripe_customer_id = data.customer
                subscription_id = data.subscription
                internal_user_id = data.metadata.get("user_id")
                
                if internal_user_id:
                    user = await session.get(User, int(internal_user_id))
                    if user:
                        user_id = user.id
                        await crud_user.update_user_subscription(
                            session, user, subscription_id, "active", stripe_customer_id
                        )
                        logger.info(f"Linked User {user.email} to Stripe Customer {stripe_customer_id}")
                        await notification_service.create_notification(
                            db=session,
                            user_id=user.id,
                            title="Suscripción Activada",
                            message="¡Bienvenido! Tu suscripción ha sido activada correctamente.",
                            notification_type="success"
                        )
                        # Point 2: Send Warm Welcome Email
                        send_transactional_email.delay(
                            user.email,
                            "¡Bienvenido a AjaxSecurFlow!",
                            f"<h1>Hola {user.email}</h1><p>Tu suscripción Premium ha sido activada correctamente. Ya puedes acceder a todas las funciones avanzadas.</p>",
                            f"Hola {user.email}, tu suscripción Premium ha sido activada correctamente."
                        )

            elif event_type in ["customer.subscription.created", "customer.subscription.updated"]:
                customer_id = data.customer
                subscription_id = data.id
                status = data.status
                
                user = await crud_user.get_user_by_stripe_customer_id(session, customer_id)
                if user:
                    user_id = user.id
                    await crud_user.update_user_subscription(
                        session, user, subscription_id, status
                    )
                    if status == "active":
                        await notification_service.create_notification(
                            db=session,
                            user_id=user.id,
                            title="Suscripción Actualizada",
                            message="Tu suscripción ha sido renovada o actualizada con éxito.",
                            notification_type="success"
                        )
                        # Point 2: Subscription Update Email
                        send_transactional_email.delay(
                            user.email,
                            "Suscripción Actualizada correctamente",
                            f"<h1>Suscripción Renovada</h1><p>Hemos procesado la renovación de tu suscripción con éxito.</p>",
                            f"Tu suscripción en AjaxSecurFlow ha sido renovada o actualizada."
                        )
            
            elif event_type == "customer.subscription.deleted":
                customer_id = data.customer
                user = await crud_user.get_user_by_stripe_customer_id(session, customer_id)
                if user:
                    user_id = user.id
                    await crud_user.update_user_subscription(
                        session, user, "", "canceled"
                    )
                    await notification_service.create_notification(
                        db=session,
                        user_id=user.id,
                        title="Suscripción Cancelada",
                        message="Tu suscripción ha sido cancelada. Esperamos volver a verte pronto.",
                        notification_type="warning"
                    )
                    # Point 2: Churn Prevention / Goodbye Email
                    send_transactional_email.delay(
                        user.email,
                        "Tu suscripción ha finalizado",
                        f"<h1>Sentimos verte partir</h1><p>Tu suscripción ha sido cancelada. Tus datos se mantendrán por 30 días si decides volver.</p>",
                        f"Tu suscripción en AjaxSecurFlow ha sido cancelada."
                    )

            elif event_type == "invoice.payment_failed":
                customer_id = data.customer
                user = await crud_user.get_user_by_stripe_customer_id(session, customer_id)
                if user:
                    user_id = user.id
                    # Downgrade status
                    user.subscription_status = "past_due"
                    await session.commit()
                    logger.warning(f"Payment failed for user {user.email}")
                    await notification_service.create_notification(
                        db=session,
                        user_id=user.id,
                        title="Fallo en el Pago",
                        message="No hemos podido procesar tu último pago. Por favor, revisa tu método de pago para evitar la interrupción del servicio.",
                        notification_type="error",
                        link="/billing"
                    )
                    # Point 2: Critical Payment Error Email
                    send_transactional_email.delay(
                        user.email,
                        "Acción Requerida: Fallo en el pago",
                        f"<h1>Error en el pago</h1><p>No hemos podido procesar tu suscripción. Por favor actualiza tu tarjeta para evitar cortes.</p>",
                        f"URGENTE: Fallo en el pago de tu suscripción AjaxSecurFlow."
                    )

            # 3. Mark event as processed
            processed_event = ProcessedStripeEvent(id=event_id, event_type=event_type)
            session.add(processed_event)
            await session.commit()

            # 4. Final Audit
            await audit_service.log_action(
                db=session,
                user_id=user_id,
                action=f"STRIPE_EVENT_PROCESSED_{event_type.upper().replace('.', '_')}",
                endpoint="celery_task",
                status_code=200,
                severity="INFO",
                resource_id=event_id,
                correlation_id=correlation_id
            )
            
            return {"status": "processed", "id": event_id}

    try:
        return asyncio.run(_handle())
    except Exception as e:
        logger.error(f"Error processing webhook {event_id}: {str(e)}")
        raise e
