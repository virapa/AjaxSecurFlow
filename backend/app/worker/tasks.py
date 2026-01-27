import asyncio
import logging
import stripe
from backend.app.worker.celery_app import celery_app
from backend.app.services.ajax_client import AjaxClient
from backend.app.core.db import async_session_factory
from backend.app.core import crud_user
from backend.app.domain.models import User, ProcessedStripeEvent
from backend.app.services import audit_service
from sqlalchemy import select

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.sync_ajax_data")
def sync_ajax_data(user_id: int):
    """
    Background task to sync data from Ajax API to our database.
    This prevents blocking the API during heavy requests.
    """
    logger.info(f"Starting data sync for user {user_id}")
    
    # Since we are in a sync worker but using async AjaxClient, 
    # we need to run it in an event loop.
    async def _sync():
        client = AjaxClient()
        # Mocking heavy work: fetching devices, status, etc.
        # response = await client.request("GET", "/devices")
        await asyncio.sleep(2) # Simulate work
        return {"status": "success", "user_id": user_id}

    result = asyncio.run(_sync())
    
    logger.info(f"Sync completed for user {user_id}")
    return result

@celery_app.task(name="tasks.process_stripe_webhook")
def process_stripe_webhook(event_dict: dict, correlation_id: str = "internal"):
    """
    Handle Stripe events with Idempotency and Corporate Auditing.
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
            
            elif event_type == "customer.subscription.deleted":
                customer_id = data.customer
                user = await crud_user.get_user_by_stripe_customer_id(session, customer_id)
                if user:
                    user_id = user.id
                    await crud_user.update_user_subscription(
                        session, user, "", "canceled"
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
