from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, EmailStr

# --- Shared ---
class AjaxResponseBase(BaseModel):
    """Base schema for Ajax API responses"""
    model_config = ConfigDict(populate_by_name=True)
    success: bool = True
    data: Any

class ImageUrls(BaseModel):
    small: Optional[str] = None
    medium: Optional[str] = None
    big: Optional[str] = None

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
    id: str = Field(..., validation_alias=AliasChoices("id", "deviceId", "DeviceId"), serialization_alias="id")
    hub_id: Optional[str] = Field(None, validation_alias=AliasChoices("hubId", "hub_id"), serialization_alias="hub_id")
    name: Optional[str] = Field(None, validation_alias=AliasChoices("deviceName", "device_name", "name"), serialization_alias="name")
    device_type: Optional[str] = Field(None, validation_alias=AliasChoices("deviceType", "device_type", "type"), serialization_alias="device_type")
    room_id: Optional[str] = Field(None, validation_alias=AliasChoices("roomId", "room_id"), serialization_alias="room_id")
    group_id: Optional[str] = Field(None, validation_alias=AliasChoices("groupId", "group_id"), serialization_alias="group_id")

class DeviceDetail(DeviceBase):
    online: Optional[bool] = Field(True, serialization_alias="online")
    state: Optional[str] = Field(None, serialization_alias="state")
    color: Optional[str] = Field(None, serialization_alias="color")
    battery_level: Optional[int] = Field(None, validation_alias=AliasChoices("battery_level", "batteryChargeLevelPercentage"), serialization_alias="battery_level")
    firmware_version: Optional[str] = Field(None, validation_alias=AliasChoices("firmware_version", "firmwareVersion"), serialization_alias="firmware_version")
    temperature: Optional[float] = Field(None, serialization_alias="temperature")
    signal_level: Optional[str] = Field(None, validation_alias=AliasChoices("signal_level", "signalLevel"), serialization_alias="signal_level")
    tampered: Optional[bool] = Field(None, serialization_alias="tampered")
    night_mode_arm: Optional[bool] = Field(None, validation_alias=AliasChoices("night_mode_arm", "nightModeArm"), serialization_alias="night_mode_arm")
    
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

# --- Rooms ---
class Room(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., validation_alias=AliasChoices("id", "roomId"))
    roomName: str
    imageUrls: Optional[ImageUrls] = None

class AjaxUserInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    phone: Optional[str] = None
    firstName: Optional[str] = None
    language: Optional[str] = None
    login: Optional[EmailStr] = None
    imageUrls: Optional[ImageUrls] = None

# --- Logs/Events ---
class EventLog(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    eventId: str
    hubId: str
    hubName: Optional[str] = None
    eventType: Optional[str] = None
    eventTypeV2: Optional[str] = None
    eventCode: Optional[str] = None
    sourceObjectType: Optional[str] = None
    sourceObjectId: Optional[str] = None
    sourceObjectName: Optional[str] = None
    sourceRoomId: Optional[str] = None
    sourceRoomName: Optional[str] = None
    timestamp: int
    eventTag: Optional[str] = None
    transition: Optional[str] = None
    additionalData: Optional[Dict[str, Any]] = None
    additionalDataV2: Optional[List[Dict[str, Any]]] = None
    eventSource: Optional[str] = None

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
