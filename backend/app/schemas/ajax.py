from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

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
    id: str = Field(..., alias="hubId")
    name: Optional[str] = Field(None, alias="hubName")
    role: Optional[str] = Field(None, alias="hubBindingRole")

class HubDetail(HubBase):
    connection_status: Optional[str] = Field(None, alias="online")
    state: Optional[str] = None # ARMED, DISARMED, etc.
    hub_subtype: Optional[str] = Field(None, alias="hubSubtype")
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
    
    # Original simplified fields (kept for backward compatibility if used)
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
    state: Optional[str] = None
    color: Optional[str] = None
    battery_charge_level: Optional[int] = Field(None, alias="batteryChargeLevelPercentage")
    firmware_version: Optional[str] = Field(None, alias="firmwareVersion")
    temperature: Optional[float] = None
    signal_level: Optional[str] = Field(None, alias="signalLevel")
    tampered: Optional[bool] = None
    night_mode_arm: Optional[bool] = Field(None, alias="nightModeArm")
    
    # Delays
    arm_delay: Optional[int] = Field(None, alias="armDelaySeconds")
    alarm_delay: Optional[int] = Field(None, alias="alarmDelaySeconds")
    
    # CMS/Technical
    cms_index: Optional[int] = Field(None, alias="cmsDeviceIndex")
    malfunctions: List[str] = []
    
    # Legacy/Simplified compatibility (keep if needed)
    battery_level: Optional[int] = None # Will map from batteryChargeLevelPercentage
    signal_strength: Optional[str] = None # Will map from signalLevel

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
