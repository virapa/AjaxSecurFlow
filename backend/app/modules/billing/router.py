import stripe
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from backend.app.core.config import settings
from backend.app.shared.infrastructure.database.session import get_db
from backend.app.shared.infrastructure.redis.deps import get_redis
from backend.app.modules.auth import service as auth_service
from backend.app.modules.billing import service as billing_service
from backend.app.modules.billing.schemas import (
    CheckoutSessionCreate, CheckoutSessionResponse, 
    WebhookResponse, BillingHistoryItem, 
    VoucherRedeem, VoucherDetailed
)

from backend.app.modules.security import service as security_service
from backend.app.worker.tasks import process_stripe_webhook

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    body: CheckoutSessionCreate,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stripe.api_key = settings.STRIPE_SECRET_KEY.get_secret_value()
    
    price_id_map = {
        "basic": settings.STRIPE_PRICE_ID_BASIC,
        "pro": settings.STRIPE_PRICE_ID_PRO,
        "premium": settings.STRIPE_PRICE_ID_PREMIUM
    }
    
    price_id = price_id_map.get(body.plan_type.lower())
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan type")

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            customer_email=current_user.email if not current_user.stripe_customer_id else None,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/billing?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing?canceled=true",
            metadata={"user_id": str(current_user.id), "plan_type": body.plan_type}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        logger.error(f"Stripe Error: {e}")
        raise HTTPException(status_code=500, detail="Could not create checkout session")

@router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET.get_secret_value()
        )
    except Exception as e:
        await security_service.log_request_action(
            db=db, request=request, user_id=None,
            action="STRIPE_WEBHOOK_SIG_FAILED", status_code=400,
            severity="ERROR", payload={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")

    # Process in background to avoid Stripe timeouts
    process_stripe_webhook.delay(event.to_dict())
    
    await security_service.log_request_action(
        db=db, request=request, user_id=None,
        action="STRIPE_WEBHOOK_RECEIVED", status_code=200,
        severity="INFO", payload={"event_id": event["id"], "type": event["type"]}
    )
    
    return {"event_id": event["id"]}

@router.get("/history", response_model=List[BillingHistoryItem])
async def get_billing_history(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await billing_service.get_unified_history(db, current_user)

@router.post("/redeem", response_model=VoucherDetailed)
async def redeem_voucher(
    body: VoucherRedeem,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await billing_service.redeem_voucher(db, current_user, body.code)
    if not success:
        raise HTTPException(status_code=400, detail="Voucher inválido, ya usado o límite alcanzado.")
    
    return VoucherDetailed(detail="Voucher canjeado con éxito")

@router.post("/generate", response_model=List[VoucherDetailed], status_code=status.HTTP_201_CREATED)
async def generate_vouchers(
    duration_days: int,
    count: int = 1,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # This endpoint should be admin-only. For now, we simulate protection
    # In a real app, we would check user.is_admin
    raise HTTPException(status_code=403, detail="Admin access required")
