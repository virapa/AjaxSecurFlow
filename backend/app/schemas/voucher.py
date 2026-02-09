from pydantic import BaseModel, Field, ConfigDict
import datetime
from datetime import datetime as dt_datetime
from typing import Optional

class VoucherRedeem(BaseModel):
    code: str = Field(..., description="The unique voucher code to redeem", example="AJAX-2024-X8K2")

class VoucherDetailed(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    duration_days: int
    is_redeemed: bool
    redeemed_at: Optional[dt_datetime] = None
    created_at: Optional[dt_datetime] = None

class VoucherCreate(BaseModel):
    duration_days: int = Field(30, ge=1, le=365)
    count: int = Field(1, ge=1, le=100)
