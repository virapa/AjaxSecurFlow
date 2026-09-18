import pytest
from datetime import datetime, timezone
from backend.app.modules.ajax.sqs_service import normalize_ajax_event

def test_normalize_ajax_event_alarm():
    body = {
        "event": {
            "hubId": "hub_123",
            "eventType": "ALARM_MOTION",
            "tag": "MotionProtect",
            "description": "Movimiento en salón",
            "timestamp": 1756730000
        },
        "recipient": {"name": "Juan Pérez"}
    }

    normalized = normalize_ajax_event(
        hub_id="hub_123",
        event_type="ALARM_MOTION",
        body=body,
        event_id="evt_test_1"
    )

    assert normalized["id"] == "evt_test_1"
    assert normalized["hub_id"] == "hub_123"
    assert normalized["event_type"] == "ALARM_MOTION"
    assert normalized["severity"] == "critical"
    assert "ALARMA" in normalized["title"]
    assert normalized["description"] == "Movimiento en salón"
    assert normalized["source"] == "sqs"
    # Raw payload must be intact
    assert normalized["data"] == body

def test_normalize_ajax_event_armed():
    body = {
        "event": {
            "hubId": "hub_123",
            "eventType": "ARMED",
            "sourceObjectName": "Mando SpaceControl"
        }
    }

    normalized = normalize_ajax_event(
        hub_id="hub_123",
        event_type="ARMED",
        body=body
    )

    assert normalized["event_type"] == "ARMED"
    assert normalized["severity"] == "success"
    assert "Armado" in normalized["title"]
    assert normalized["data"] == body

def test_normalize_ajax_event_warning():
    body = {
        "event": {
            "hubId": "hub_123",
            "eventType": "POWER_LOSS",
            "tag": "Hub 2 Plus"
        }
    }

    normalized = normalize_ajax_event(
        hub_id="hub_123",
        event_type="POWER_LOSS",
        body=body
    )

    assert normalized["severity"] == "warning"
    assert "POWER_LOSS" in normalized["title"]
    assert normalized["data"] == body

def test_normalize_ajax_event_motion_cam_media_urls():
    body = {
        "event": {
            "hubId": "000E7305",
            "eventType": "ALARM",
            "eventTag": "MotionDetected",
            "sourceObjectName": "Cámara",
            "sourceRoomName": "Cabina",
            "sourceObjectType": "MOTION_CAM",
            "timestamp": 1788343882215,
            "additionalData": {
                "orderedResourceLinks": [
                    {"url": "https://s3.amazonaws.com/photo1.jpg", "status": "READY"},
                    {"url": "https://s3.amazonaws.com/photo2.jpg", "status": "READY"},
                    {"url": None, "status": "IN_PROGRESS"}
                ]
            }
        }
    }

    normalized = normalize_ajax_event(
        hub_id="000E7305",
        event_type="ALARM",
        body=body,
        event_id="evt_motion_1"
    )

    assert normalized["event_type"] == "ALARM"
    assert normalized["severity"] == "critical"
    assert normalized["description"] == "Movimiento detectado, Cámara en Cabina"
    assert len(normalized["media_urls"]) == 2
    assert normalized["media_urls"][0] == "https://s3.amazonaws.com/photo1.jpg"
    assert normalized["media_urls"][1] == "https://s3.amazonaws.com/photo2.jpg"
