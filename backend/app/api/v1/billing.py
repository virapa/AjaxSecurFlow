import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.api.v1.auth import get_current_user, get_current_admin
from backend.app.domain.models import User
from backend.app.services import audit_service
from backend.app.worker.tasks import process_stripe_webhook
from backend.app.schemas.billing import CheckoutSessionResponse, WebhookResponse, CheckoutSessionCreate
from backend.app.schemas.voucher import VoucherRedeem, VoucherCreate, VoucherDetailed
from backend.app.schemas.auth import ErrorMessage
from backend.app.services import voucher_service

router = APIRouter()

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY.get_secret_value()

@router.post(
    "/create-checkout-session", 
    response_model=CheckoutSessionResponse,
    summary="Create Stripe Checkout Session",
    responses={
        400: {"model": ErrorMessage, "description": "Payment configuration error"},
        501: {"model": ErrorMessage, "description": "Stripe not configured on server"}
    }
)
async def create_checkout_session(
    payload: CheckoutSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Initiates a new Stripe Checkout session for the specified price ID.
    The response will contain a URL to which the application should redirect the user.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=501, detail="Stripe not configured")

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": payload.price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"http://localhost:3000/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url="http://localhost:3000/cancel",
            metadata={"user_id": current_user.id}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/webhook",
    response_model=WebhookResponse,
    summary="Stripe Event Webhook",
    include_in_schema=False # Optional: usually webhooks are for Stripe, not public
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(None)
):
    """
    Public entry point for Stripe to report event updates (payments, failures, etc).
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=501, detail="Webhook secret not configured")

    payload = await request.body()
    correlation_id = getattr(request.state, "correlation_id", "internal")
    
    try:
        # 1. Validate signature
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET.get_secret_value()
        )
        
        # 2. Audit Log (Receipt of Event)
        await audit_service.log_request_action(
            db=db,
            request=request,
            user_id=None,
            action="STRIPE_WEBHOOK_RECEIVED",
            status_code=200,
            severity="INFO",
            resource_id=event.id,
            correlation_id=correlation_id,
            payload={"type": event.type}
        )
        
        # 3. Offload to worker
        process_stripe_webhook.delay(event.to_dict(), correlation_id)
        
        return {"status": "success", "event_id": event.id}
    except stripe.error.SignatureVerificationError:
        await audit_service.log_request_action(
            db=db,
            request=request,
            user_id=None,
            action="STRIPE_SIGNATURE_ERROR",
            status_code=400,
            severity="CRITICAL",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Voucher Management ---

@router.post(
    "/vouchers/redeem",
    summary="Redeem an activation code",
    description="Allows a user to activate or extend their subscription using a unique voucher code."
)
async def redeem_voucher(
    request: Request,
    payload: VoucherRedeem,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await voucher_service.redeem_voucher(db, current_user, payload.code)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid, expired or already redeemed voucher code.")
    
    await audit_service.log_request_action(
        db=db,
        request=request, 
        user_id=current_user.id,
        action="VOUCHER_REDEEMED",
        status_code=200,
        severity="INFO",
        payload={"code": payload.code}
    )
    
    return {"status": "success", "message": "Voucher redeemed successfully. Your access has been extended."}

@router.post(
    "/vouchers/generate",
    response_model=list[VoucherDetailed],
    summary="Generate new activation codes (Admin Only)",
    include_in_schema=True
)
async def generate_vouchers(
    request: Request,
    payload: VoucherCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    x_admin_secret: str = Header(..., description="Secondary secret key for administrative operations")
):
    """
    Mass generate vouchers for distributors or offline sales.
    Requires Admin privileges AND a valid secondary secret key.
    """
    # 1. Verify Secondary Secret
    if x_admin_secret != settings.ADMIN_SECRET_KEY.get_secret_value():
        await audit_service.log_request_action(
            db=db,
            request=request,
            user_id=admin_user.id,
            action="VOUCHER_GEN_SECRET_FAILURE",
            status_code=403,
            severity="CRITICAL"
        )
        raise HTTPException(status_code=403, detail="Invalid administrative secret key.")

    # 2. Generate
    vouchers = await voucher_service.create_vouchers(db, payload.count, payload.duration_days)
    
    # 3. Enhanced Audit
    await audit_service.log_request_action(
        db=db,
        request=request,
        user_id=admin_user.id,
        action="VOUCHER_BATCH_GENERATED",
        status_code=200,
        severity="WARNING", # High visibility
        payload={"count": payload.count, "duration": payload.duration_days}
    )
    
    return vouchers
