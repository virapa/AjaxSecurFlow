from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, AliasChoices

# --- Shared ---
class AjaxResponseBase(BaseModel):
    """Base schema for Ajax API responses"""
    model_config = ConfigDict(populate_by_name=True)
    success: bool = True
    data: Any

# --- Hub Nested Models ---
class HubFirmware(BaseModel):
    version: Optional[str] = None
    newVersionAvailable: Optional[bool] = None
    latestAvailableVersion: Optional[str] = None
    autoupdateEnabled: Optional[bool] = None

class HubEthernet(BaseModel):
    enabled: Optional[bool] = None
    ip: Optional[str] = None
    mask: Optional[str] = None
    gate: Optional[str] = None
    dns: Optional[str] = None
    dhcp: Optional[bool] = None

class HubBattery(BaseModel):
    chargeLevelPercentage: Optional[int] = None
    state: Optional[str] = None

class HubGSM(BaseModel):
    signalLevel: Optional[str] = None
    gprsEnabled: Optional[bool] = None
    simCardState: Optional[str] = None
    networkStatus: Optional[str] = None
    activeSimCard: Optional[int] = None

class HubJeweller(BaseModel):
    detectorPingIntervalSeconds: Optional[int] = None
    lostHeartbeatsThreshold: Optional[int] = None

# --- Hubs ---
class HubBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., validation_alias=AliasChoices("id", "hubId"))
    name: Optional[str] = Field(None, validation_alias="hubName")
    role: Optional[str] = Field(None, validation_alias="hubBindingRole")

class HubDetail(HubBase):
    online: Optional[bool] = None # Map directly to 'online' boolean from Ajax
    state: Optional[str] = None # ARMED, DISARMED, etc.
    hub_subtype: Optional[str] = Field(None, validation_alias="hubSubtype")
    timeZone: Optional[str] = None
    color: Optional[str] = None
    externallyPowered: Optional[bool] = None
    tampered: Optional[bool] = None
    
    # Nested Info
    firmware: Optional[HubFirmware] = None
    ethernet: Optional[HubEthernet] = None
    battery: Optional[HubBattery] = None
    gsm: Optional[HubGSM] = None
    jeweller: Optional[HubJeweller] = None

# --- Devices ---
class DeviceBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., validation_alias=AliasChoices("id", "deviceId"))
    hub_id: Optional[str] = Field(None, validation_alias="hubId")
    name: Optional[str] = Field(None, validation_alias="deviceName")
    device_type: Optional[str] = Field(None, validation_alias="deviceType")
    room_id: Optional[str] = Field(None, validation_alias="roomId")
    group_id: Optional[str] = Field(None, validation_alias="groupId")

class DeviceDetail(DeviceBase):
    online: Optional[bool] = True
    state: Optional[str] = None
    color: Optional[str] = None
    battery_level: Optional[int] = Field(None, validation_alias=AliasChoices("battery_level", "batteryChargeLevelPercentage"))
    firmware_version: Optional[str] = Field(None, validation_alias=AliasChoices("firmware_version", "firmwareVersion"))
    temperature: Optional[float] = None
    signal_level: Optional[str] = Field(None, validation_alias=AliasChoices("signal_level", "signalLevel"))
    tampered: Optional[bool] = None
    night_mode_arm: Optional[bool] = Field(None, validation_alias=AliasChoices("night_mode_arm", "nightModeArm"))
    
    # Delays
    arm_delay: Optional[int] = Field(None, validation_alias=AliasChoices("arm_delay", "armDelaySeconds"))
    alarm_delay: Optional[int] = Field(None, validation_alias=AliasChoices("alarm_delay", "alarmDelaySeconds"))
    
    # CMS/Technical
    cms_index: Optional[int] = Field(None, validation_alias=AliasChoices("cms_index", "cmsDeviceIndex"))
    malfunctions: List[str] = []
    
    # Legacy compatibility fields
    signal_strength: Optional[str] = None 

# --- Groups ---
class GroupBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., validation_alias=AliasChoices("id", "groupId"))
    hub_id: str = Field(..., validation_alias=AliasChoices("hub_id", "hubId"))
    name: str
    state: Optional[str] = None # armed, disarmed, etc.

# --- Logs/Events ---
class EventLog(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., validation_alias=AliasChoices("id", "logId", "timestamp"))
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
    total_count: int = Field(..., validation_alias="totalCount")

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
    arm_state: ArmState = Field(
        ..., 
        alias="armState",
        description="Target arming state: 0 (DISARMED), 1 (ARMED), 2 (NIGHT_MODE)",
        example=1
    )
    group_id: Optional[str] = Field(
        None, 
        alias="groupId",
        description="Optional ID of the specific security group to arm/disarm. If omitted, the whole hub is controlled.",
        example="1"
    )

class CommandResponse(BaseModel):
    """Response from a command execution."""
    model_config = ConfigDict(populate_by_name=True)
    success: bool
    message: Optional[str] = None
