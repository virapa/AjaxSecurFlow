
import pytest
from backend.app.schemas.ajax import DeviceDetail

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
