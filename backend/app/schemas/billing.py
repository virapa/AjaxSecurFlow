from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import datetime
from datetime import datetime as dt_datetime

class CheckoutSessionCreate(BaseModel):
    price_id: str = Field(..., description="Stripe Price ID to subscribe to")

class CheckoutSessionResponse(BaseModel):
    url: str = Field(..., description="Stripe Checkout URL to redirect the user to")

class WebhookResponse(BaseModel):
    status: str = Field("success", description="Webhook processing status")
    event_id: str = Field(..., description="The Stripe Event ID processed")

class BillingHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: dt_datetime
    type: str # 'voucher' | 'payment'
    description: str
    amount: Optional[str] = None
    status: str
    download_url: Optional[str] = None
