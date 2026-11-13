
import pytest
from backend.app.modules.ajax.schemas import DeviceDetail

def test_device_detail_bypass_state():
    """Verify that DeviceDetail schema correctly parses the bypassState field."""
    
    payload = {
        "id": "3056A52F",
        "hubId": "0004C602",
        "name": "MotionCam",
        "deviceType": "MotionCam",
        "roomId": "1",
        "groupId": "1",
        "online": True,
        "bypassState": ["BYPASSED"], # The new field we want to test
        "properties": {
             "batteryChargeLevelPercentage": 95,
             "signalLevel": "HIGH"
        }
    }
    
    # Simulate how the API endpoint would construct the model
    # Note: the real endpoint flattens/maps some fields before creating the model or 
    # relies on Pydantic's alias magic if passing the raw dict.
    # Let's test with a dict that mimics what the endpoints/client produce or the raw API response
    # if we rely on aliases.
    
    # Based on existing patterns, we might be passing kwargs that align with the model fields 
    # OR a dict that aligns with aliases.
    
    device = DeviceDetail(**payload)
    
    assert device.id == "3056A52F"
    assert device.bypassState == ["BYPASSED"]

def test_device_detail_bypass_state_none():
    """Verify that bypassState is optional (None by default)."""
    
    payload = {
        "id": "3056A52F",
        "hubId": "0004C602",
        "name": "MotionCam",
    }
    
    device = DeviceDetail(**payload)
    
    assert device.id == "3056A52F"
    assert device.bypassState is None

from backend.app.modules.ajax.schemas import DeviceListItem, HubDetail

# Shape produced by AjaxClient.get_hub_devices (enrich=true, properties flattened)
ENRICHED_DOOR = {
    "deviceId": "AABB0001", "hubId": "0004C602", "deviceName": "Puerta principal",
    "deviceType": "DoorProtect", "roomId": "1", "groupId": "1", "online": True,
    "batteryChargeLevelPercentage": 88, "signalLevel": "STRONG", "temperature": 21.5,
    "tampered": False, "state": "ACTIVE", "malfunctions": [],
    "reedClosed": True, "extraContactAware": True, "extraContactClosed": False,
}
ENRICHED_MOTION = {
    "deviceId": "AABB0002", "hubId": "0004C602", "deviceName": "Salón",
    "deviceType": "MotionProtect", "online": True, "motionDetected": True,
    "batteryChargeLevelPercentage": 100, "signalLevel": "STRONG",
}


def test_device_list_item_exposes_sensor_fields():
    item = DeviceListItem(**ENRICHED_DOOR)
    dumped = item.model_dump(by_alias=True)
    assert dumped["reed_closed"] is True
    assert dumped["extra_contact_aware"] is True
    assert dumped["extra_contact_closed"] is False
    assert dumped["battery_level"] == 88
    assert dumped["signal_level"] == "STRONG"
    assert dumped["temperature"] == 21.5
    assert dumped["tampered"] is False
    assert dumped["malfunctions"] == []


def test_device_list_item_motion_and_missing_fields_are_none():
    item = DeviceListItem(**ENRICHED_MOTION)
    dumped = item.model_dump(by_alias=True)
    assert dumped["motion_detected"] is True
    assert dumped["reed_closed"] is None
    assert dumped["leak_detected"] is None
    assert dumped["smoke_alarm_detected"] is None
    assert dumped["humidity"] is None
    assert dumped["co2"] is None


def test_device_detail_has_same_sensor_fields():
    detail = DeviceDetail(**{**ENRICHED_DOOR, "id": "AABB0001"})
    dumped = detail.model_dump(by_alias=True)
    assert dumped["reed_closed"] is True
    assert dumped["battery_level"] == 88
    assert dumped["firmware_version"] is None


def test_hub_detail_groups_enabled():
    hub = HubDetail(id="0004C602", groupsEnabled=True, state="ARMED_NIGHT_MODE_OFF")
    dumped = hub.model_dump(by_alias=True)
    assert dumped["groups_enabled"] is True
    assert dumped["state"] == "ARMED_NIGHT_MODE_OFF"


def test_hub_detail_groups_enabled_default_none():
    assert HubDetail(id="0004C602").groups_enabled is None
