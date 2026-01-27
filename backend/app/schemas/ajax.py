from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

# --- Shared ---
class AjaxResponseBase(BaseModel):
    """Base schema for Ajax API responses"""
    model_config = ConfigDict(populate_by_name=True)
    success: bool = True
    data: Any

# --- Hubs ---
class HubBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., alias="hubId")
    name: Optional[str] = Field(None, alias="hubName")
    role: Optional[str] = Field(None, alias="hubBindingRole")

class HubDetail(HubBase):
    connection_status: Optional[str] = Field(None, alias="online")
    battery_level: Optional[int] = None
    gsm_signal: Optional[str] = None
    ethernet_ip: Optional[str] = None
    firmware_version: Optional[str] = None

# --- Devices ---
class DeviceBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    hub_id: Optional[str] = Field(None, alias="hubId")
    name: Optional[str] = Field(None, alias="deviceName")
    device_type: Optional[str] = Field(None, alias="deviceType")
    room_id: Optional[str] = Field(None, alias="roomId")
    group_id: Optional[str] = Field(None, alias="groupId")

class DeviceDetail(DeviceBase):
    online: Optional[bool] = True
    battery_level: Optional[int] = None
    signal_level: Optional[str] = None
    temp: Optional[float] = None
    cms_index: Optional[int] = None # Will map from model.cmsDeviceIndex if needed manually

# --- Groups ---
class GroupBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    hub_id: str
    name: str
    state: Optional[str] = None # armed, disarmed, etc.

# --- Logs/Events ---
class EventLog(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    hub_id: str
    timestamp: str # ISO format
    event_code: str
    event_desc: Optional[str] = None
    user_name: Optional[str] = None
    group_name: Optional[str] = None
    room_name: Optional[str] = None
    device_name: Optional[str] = None
    
class EventLogList(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    logs: List[EventLog]
    total_count: int

from enum import IntEnum

# --- Commands ---
class ArmState(IntEnum):
    """Possible arm states for a hub or group."""
    DISARMED = 0
    ARMED = 1
    NIGHT_MODE = 2  # Partial arming/Stay mode

class HubCommandRequest(BaseModel):
    """Schema for sending an arm/disarm command."""
    model_config = ConfigDict(populate_by_name=True)
    arm_state: ArmState = Field(..., alias="armState")
    group_id: Optional[str] = Field(None, alias="groupId") # Optional if arming the whole hub

class CommandResponse(BaseModel):
    """Response from a command execution."""
    model_config = ConfigDict(populate_by_name=True)
    success: bool
    message: Optional[str] = None
