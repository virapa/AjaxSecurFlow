from pydantic import BaseModel, Field
from typing import Optional

class CheckoutSessionCreate(BaseModel):
    price_id: str = Field(..., description="Stripe Price ID to subscribe to")

class CheckoutSessionResponse(BaseModel):
    url: str = Field(..., description="Stripe Checkout URL to redirect the user to")

class WebhookResponse(BaseModel):
    status: str = Field("success", description="Webhook processing status")
    event_id: str = Field(..., description="The Stripe Event ID processed")
