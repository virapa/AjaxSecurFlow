"""Human-readable in-app notification content built from real Ajax SQS events."""
from backend.app.modules.ajax.notification_content import build_event_notification


def _event(event_type, tag, source_name="Raul Palacios", source_type="USER", room=" ", **extra):
    data = {
        "hubId": "0004C602",
        "hubName": "HUB 2 PRUEBAS SATYA",
        "eventType": event_type,
        "eventTag": tag,
        "sourceObjectType": source_type,
        "sourceObjectName": source_name,
        "sourceRoomName": room,
        "additionalData": {"relatedGroupsInfo": [{"id": "00000001", "name": "AREA1"}]},
    }
    data.update(extra)
    return data


def test_disarm_names_user_and_hub():
    title, message, n_type = build_event_notification("SECURITY", _event("SECURITY", "Disarm"))
    assert title == "🔓 Sistema desarmado"
    assert message == "HUB 2 PRUEBAS SATYA: desarmado por Raul Palacios"
    assert n_type == "info"


def test_group_arm_with_malfunctions_names_group_and_trouble_count():
    event = _event(
        "SECURITY", "GroupArmWithMalfunctions",
        additionalDataV2=[{"additionalDataV2Type": "TROUBLED_DEVICES", "troubleDevices": [{}, {}, {}, {}]}],
    )
    title, message, n_type = build_event_notification("SECURITY", event)
    assert title == "🔐 Armado con averías"
    assert message == "HUB 2 PRUEBAS SATYA: grupo AREA1 armado por Raul Palacios (4 dispositivos con avería)"
    assert n_type == "warning"


def test_arm_attempt_is_a_warning():
    title, message, n_type = build_event_notification("SECURITY", _event("SECURITY", "GroupArmAttempt"))
    assert title == "⚠️ Intento de armado"
    assert message == "HUB 2 PRUEBAS SATYA: intento de armado del grupo AREA1 por Raul Palacios"
    assert n_type == "warning"


def test_intrusion_alarm_names_device_and_room_and_is_error():
    event = _event("ALARM", "IntrusionAlarm", source_name="Puerta entrada", source_type="DOOR_PROTECT", room="Recibidor")
    title, message, n_type = build_event_notification("ALARM", event)
    assert "ALARMA" in title
    assert message == "HUB 2 PRUEBAS SATYA: intrusión en Puerta entrada (Recibidor)"
    assert n_type == "error"


def test_malfunction_and_recovery():
    event = _event("MALFUNCTION", "ServerConnectionLoss", source_name="HUB 2 PRUEBAS SATYA", source_type="HUB")
    title, message, n_type = build_event_notification("MALFUNCTION", event)
    assert title == "⚠️ Avería detectada"
    assert message == "HUB 2 PRUEBAS SATYA: pérdida de conexión con el servidor"
    assert n_type == "warning"

    title, _, n_type = build_event_notification("FUNCTION_RECOVERED", {**event, "eventType": "FUNCTION_RECOVERED"})
    assert title == "✅ Avería resuelta"
    assert n_type == "success"


def test_unknown_tag_falls_back_to_readable_text():
    event = _event("MALFUNCTION", "SomeNewThingHappened", source_name="Sensor X", source_type="MOTION_PROTECT")
    _, message, _ = build_event_notification("MALFUNCTION", event)
    assert message == "HUB 2 PRUEBAS SATYA: some new thing happened en Sensor X"


def test_noisy_categories_do_not_notify():
    # Relay automations, user/lifecycle changes stay in logs/SSE/webhooks, not in the bell
    for event_type, tag in [("COMMON", "RelayOnByArming"), ("USER", "ObjectAdded"), ("LIFECYCLE", "ObjectAdded")]:
        assert build_event_notification(event_type, _event(event_type, tag)) is None
