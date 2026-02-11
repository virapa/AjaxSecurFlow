from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, EmailStr, field_validator, model_validator
from enum import IntEnum, Enum

# --- Shared ---
class AjaxResponseBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    success: bool = True
    data: Any

class ImageUrls(BaseModel):
    small: Optional[str] = None
    medium: Optional[str] = None
    large: Optional[str] = Field(None, validation_alias=AliasChoices("large", "big"), serialization_alias="large")
    big: Optional[str] = None # Keep for backward compatibility if needed internally

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
    online: Optional[bool] = None
    state: Optional[str] = None
    hub_subtype: Optional[str] = Field(None, validation_alias="hubSubtype")
    timeZone: Optional[str] = None
    color: Optional[str] = None
    externallyPowered: Optional[bool] = None
    tampered: Optional[bool] = None
    
    firmware: Optional[HubFirmware] = None
    ethernet: Optional[HubEthernet] = None
    battery: Optional[HubBattery] = None
    gsm: Optional[HubGSM] = None
    jeweller: Optional[HubJeweller] = None

# --- Devices ---
class DeviceBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., validation_alias=AliasChoices("id", "deviceId", "DeviceId"), serialization_alias="id")
    hub_id: Optional[str] = Field(None, validation_alias=AliasChoices("hubId", "hub_id"), serialization_alias="hubId")
    name: Optional[str] = Field(None, validation_alias=AliasChoices("deviceName", "device_name", "name"), serialization_alias="name")
    device_type: Optional[str] = Field(None, validation_alias=AliasChoices("deviceType", "device_type", "type"), serialization_alias="deviceType")
    room_id: Optional[str] = Field(None, validation_alias=AliasChoices("roomId", "room_id"), serialization_alias="roomId")
    group_id: Optional[str] = Field(None, validation_alias=AliasChoices("groupId", "group_id"), serialization_alias="groupId")

class DeviceListItem(DeviceBase):
    online: Optional[bool] = Field(None, validation_alias=AliasChoices("online", "isOnline"), serialization_alias="online")

class DeviceDetail(DeviceBase):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    online: Optional[bool] = Field(True, serialization_alias="online")
    state: Optional[str] = Field(None, serialization_alias="state")
    color: Optional[str] = Field(None, serialization_alias="color")
    battery_level: Optional[int] = Field(None, validation_alias=AliasChoices("battery_level", "batteryChargeLevelPercentage"), serialization_alias="battery_level")
    firmware_version: Optional[str] = Field(None, validation_alias=AliasChoices("firmware_version", "firmwareVersion"), serialization_alias="firmware_version")
    temperature: Optional[float] = Field(None, serialization_alias="temperature")
    signal_level: Optional[str] = Field(None, validation_alias=AliasChoices("signal_level", "signalLevel"), serialization_alias="signal_level")
    tampered: Optional[bool] = Field(None, serialization_alias="tampered")
    night_mode_arm: Optional[bool] = Field(None, validation_alias=AliasChoices("night_mode_arm", "nightModeArm"), serialization_alias="night_mode_arm")
    
    arm_delay: Optional[int] = Field(None, validation_alias=AliasChoices("arm_delay", "armDelaySeconds"))
    alarm_delay: Optional[int] = Field(None, validation_alias=AliasChoices("alarm_delay", "alarmDelaySeconds"))
    
    cms_index: Optional[int] = Field(None, validation_alias=AliasChoices("cms_index", "cmsDeviceIndex"))
    bypassState: Optional[List[str]] = None
    malfunctions: List[str] = []

# --- Groups ---
class GroupBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., validation_alias=AliasChoices("id", "groupId"))
    hub_id: str = Field(..., validation_alias=AliasChoices("hub_id", "hubId"))
    name: str
    state: Optional[str] = None

# --- Rooms ---
class Room(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., validation_alias=AliasChoices("id", "roomId"))
    roomName: str
    imageUrls: Optional[ImageUrls] = None

class AjaxUserInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    id: Optional[str] = Field(None, validation_alias=AliasChoices("id", "userId"))
    phone: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    language: Optional[str] = None
    login: Optional[EmailStr] = None
    imageUrls: Optional[ImageUrls] = None

    @field_validator("firstName", mode="after")
    @classmethod
    def split_names(cls, v: Optional[str], info: Any) -> Optional[str]:
        # If firstName contains spaces and lastName is missing, try to split
        if v and " " in v:
            # We can't easily mutate other fields here in a standard way, 
            # but we can at least ensure we don't have duplicated full name if we want.
            # However, for simplicity and compatibility with the frontend {firstName} {lastName},
            # we will split it if lastName is not provided in the data.
            pass
        return v

    @model_validator(mode="after")
    def handle_names_and_id(self) -> "AjaxUserInfo":
        if self.firstName and " " in self.firstName and not self.lastName:
            parts = self.firstName.split(" ", 1)
            self.firstName = parts[0]
            self.lastName = parts[1]
        
        # Ensure id is at least something (fallback to login if no userId)
        if not self.id and self.login:
            self.id = str(self.login)
            
        return self

# --- Logs/Events ---
EVENT_DESC_MAP = {
    "Motion": "Movimiento Detectado",
    "Arm": "Sistema Armado",
    "Disarm": "Sistema Desarmado",
    "Alarm": "Alarma Central",
    "SOS": "Pánico / SOS",
    "PowerLoss": "Pérdida de Alimentación",
    "BatteryLow": "Batería Baja"
}

class EventLog(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    id: Optional[Any] = Field(None, validation_alias=AliasChoices("id", "eventId", "eventIdV2"), serialization_alias="id")
    hub_id: Optional[Any] = Field(None, validation_alias=AliasChoices("hub_id", "hubId"), serialization_alias="hub_id")
    timestamp: Optional[Any] = None
    event_code: Optional[Any] = Field(None, validation_alias=AliasChoices("event_code", "eventCode"), serialization_alias="event_code")
    event_desc: Optional[Any] = Field(None, validation_alias=AliasChoices("event_desc", "eventTag", "eventTypeV2", "eventType"), serialization_alias="event_desc")
    
    user_name: Optional[Any] = Field(None, validation_alias=AliasChoices("user_name", "sourceObjectName"), serialization_alias="user_name")
    device_name: Optional[Any] = Field(None, validation_alias=AliasChoices("device_name", "sourceObjectName"), serialization_alias="device_name")
    
    transition: Optional[Any] = None
    eventTag: Optional[Any] = None
    sourceObjectType: Optional[Any] = None
    sourceObjectId: Optional[Any] = None
    sourceRoomName: Optional[Any] = None
    additionalData: Optional[Any] = None
    additionalDataV2: Optional[Any] = None

class EventLogResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    logs: List[EventLog] = Field(default_factory=list, validation_alias=AliasChoices("logs", "events"))
    total_count: int = Field(0, validation_alias=AliasChoices("total_count", "totalCount"))

class HubBindingRole(str, Enum):
    MASTER = "MASTER"
    USER = "USER"
    PRO = "PRO"

class UserHubBinding(BaseModel):
    hub_id: str = Field(..., validation_alias=AliasChoices("hubId", "hub_id"))
    hub_binding_role: HubBindingRole = Field(..., validation_alias=AliasChoices("hubBindingRole", "hub_binding_role"))

class ArmState(IntEnum):
    DISARMED = 0
    ARMED = 1
    NIGHT_MODE = 2

class HubCommandRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    arm_state: ArmState = Field(..., alias="armState")
    group_id: Optional[str] = Field(None, alias="groupId")

class CommandResponse(BaseModel):
    success: bool
    message: Optional[str] = None
