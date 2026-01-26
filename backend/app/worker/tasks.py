import asyncio
import logging
import stripe
from backend.app.worker.celery_app import celery_app
from backend.app.services.ajax_client import AjaxClient
from backend.app.core.db import async_session_factory
from backend.app.core import crud_user

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
def process_stripe_webhook(event_dict: dict):
    """
    Handle Stripe events in the background.
    """
    event = stripe.Event.construct_from(event_dict, stripe.api_key)
    event_type = event.type
    logger.info(f"Processing Stripe webhook event: {event_type}")

    async def _handle():
        async with async_session_factory() as session:
            data = event.data.object
            
            if event_type in ["customer.subscription.created", "customer.subscription.updated"]:
                customer_id = data.customer
                subscription_id = data.id
                status = data.status
                
                user = await crud_user.get_user_by_stripe_customer_id(session, customer_id)
                if user:
                    await crud_user.update_user_subscription(
                        session, user, subscription_id, status
                    )
                    logger.info(f"Updated subscription for user {user.email}")
            
            elif event_type == "customer.subscription.deleted":
                customer_id = data.customer
                user = await crud_user.get_user_by_stripe_customer_id(session, customer_id)
                if user:
                    await crud_user.update_user_subscription(
                        session, user, "", "canceled"
                    )
                    logger.info(f"Canceled subscription for user {user.email}")

    asyncio.run(_handle())
    
    return {"status": "processed", "type": event_type}
