from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class VoucherRedeem(BaseModel):
    code: str = Field(..., description="The unique voucher code to redeem", example="AJAX-2024-X8K2")

class VoucherDetailed(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    duration_days: int
    is_redeemed: bool
    redeemed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class VoucherCreate(BaseModel):
    duration_days: int = Field(30, ge=1, le=365)
    count: int = Field(1, ge=1, le=100)
