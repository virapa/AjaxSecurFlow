"""
Builds in-app notification content (title, message, type) from real Ajax SQS events.

Ajax sends arm/disarm and most other actions under broad eventType categories
(SECURITY, ALARM, MALFUNCTION...); what actually happened is in `eventTag`.
"""
import re
from typing import Any, Dict, Optional, Tuple

# Categories shown in the notification bell. Others (COMMON relay automations,
# USER/LIFECYCLE changes...) stay in event logs, SSE and webhooks only.
NOTIFIABLE_TYPES = {"ALARM", "ALARM_RECOVERED", "SECURITY", "MALFUNCTION", "FUNCTION_RECOVERED"}

# Readable labels for the most frequent alarm/malfunction tags
TAG_LABELS = {
    "IntrusionAlarm": "intrusión",
    "MotionDetected": "movimiento detectado",
    "DoorOpened": "puerta abierta",
    "ExtContactOpened": "contacto externo abierto",
    "ShockDetected": "golpe detectado",
    "TiltDetected": "inclinación detectada",
    "GlassBreakDetected": "rotura de cristal",
    "PanicButtonPressed": "botón de pánico pulsado",
    "SmokeDetected": "humo detectado",
    "FireAlarm": "alarma de incendio",
    "LeakDetected": "fuga de agua",
    "TemperatureHighAlarm": "temperatura alta",
    "HumidityHighAlarm": "humedad alta",
    "JewellerNoiseHigh": "nivel de interferencias alto",
    "ServerConnectionLoss": "pérdida de conexión con el servidor",
    "DeviceCommunicationLoss": "pérdida de comunicación con el dispositivo",
    "EthernetCommunicationLoss": "pérdida de comunicación Ethernet",
    "EthernetConnectionLoss": "pérdida de conexión Ethernet",
    "ExternalPowerLoss": "corte de alimentación externa",
    "PowerLow": "batería baja",
    "TamperOpened": "tapa abierta (sabotaje)",
    "Malfunction": "avería",
    "BypassOn": "dispositivo anulado",
    "OnetimeFullBypassOn": "anulación temporal completa",
    "TamperBypassOn": "sabotaje anulado",
    "AutomaticBypassByNumber": "anulación automática",
    "AutomaticBypassOff": "anulación automática desactivada",
    "AutomaticBypassByRestoreTimer": "anulación automática por temporizador",
    "MotionDetectedRight": "movimiento detectado (lado derecho)",
    "MotionDetectedLeft": "movimiento detectado (lado izquierdo)",
    "TemperatureLowAlarm": "temperatura baja",
    "BusShortCircuit": "cortocircuito en el bus",
    "DetectorShortCircuit": "cortocircuito en el detector",
    "ExternalContactOk": "contacto externo normal",
    "BatteryLow": "batería baja",
    "BatteryDisconnected": "batería desconectada",
    "DataChannelCommunicationLoss": "pérdida de comunicación del canal de datos",
    "RelayNotResponding": "el relé no responde",
    "RelayVoltageLow": "tensión del relé baja",
    "RelayVoltageOk": "tensión del relé normal",
    "SmartBracketOpened": "soporte SmartBracket abierto",
}

ALARM_TITLES = {"PanicButtonPressed": "🆘 Botón de pánico"}

ARM_TAGS = {"Arm", "GroupArm"}
ARM_WITH_MALFUNCTIONS_TAGS = {"ArmWithMalfunctions", "GroupArmWithMalfunctions"}
ARM_ATTEMPT_TAGS = {"ArmAttempt", "GroupArmAttempt"}
DISARM_TAGS = {"Disarm", "GroupDisarm"}


def _humanize(tag: str) -> str:
    """'SomeNewThingHappened' -> 'some new thing happened'."""
    return re.sub(r"(?<!^)(?=[A-Z])", " ", tag).lower() if tag else ""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _group_name(event: Dict[str, Any]) -> str:
    add = event.get("additionalData") or {}
    groups = add.get("relatedGroupsInfo") if isinstance(add, dict) else None
    if groups and isinstance(groups, list):
        return _clean(groups[0].get("name"))
    return ""


def _trouble_count(event: Dict[str, Any]) -> int:
    for item in event.get("additionalDataV2") or []:
        if isinstance(item, dict) and item.get("additionalDataV2Type") == "TROUBLED_DEVICES":
            return len(item.get("troubleDevices") or [])
    return 0


def _security(tag: str, hub: str, who: str, group: str, event: Dict[str, Any]) -> Tuple[str, str, str]:
    is_group = tag.startswith("Group") and group
    by = f" por {who}" if who else ""

    if tag in ARM_ATTEMPT_TAGS:
        target = f" del grupo {group}" if is_group else ""
        return "⚠️ Intento de armado", f"{hub}: intento de armado{target}{by}", "warning"

    if tag in DISARM_TAGS:
        what = f"grupo {group} desarmado" if is_group else "desarmado"
        return "🔓 Sistema desarmado", f"{hub}: {what}{by}", "info"

    if tag in ARM_TAGS or tag in ARM_WITH_MALFUNCTIONS_TAGS:
        what = f"grupo {group} armado" if is_group else "armado"
        message = f"{hub}: {what}{by}"
        if tag in ARM_WITH_MALFUNCTIONS_TAGS:
            count = _trouble_count(event)
            if count:
                message += f" ({count} dispositivo{'s' if count != 1 else ''} con avería)"
            return "🔐 Armado con averías", message, "warning"
        return "🔐 Sistema armado", message, "success"

    if tag == "NightModeOn":
        return "🌙 Modo noche activado", f"{hub}: modo noche activado{by}", "info"
    if tag == "NightModeOff":
        return "🌙 Modo noche desactivado", f"{hub}: modo noche desactivado{by}", "info"

    return "🔐 Evento de seguridad", f"{hub}: {_humanize(tag) or 'evento de seguridad'}{by}", "info"


def build_event_notification(event_type: str, event: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
    """
    Returns (title, message, notification_type) for an Ajax event, or None when
    the event category should not appear in the notification bell.
    """
    category = _clean(event_type).upper()
    if category not in NOTIFIABLE_TYPES:
        return None

    tag = _clean(event.get("eventTag"))
    hub = _clean(event.get("hubName")) or _clean(event.get("hubId"))
    source = _clean(event.get("sourceObjectName"))
    source_is_user = _clean(event.get("sourceObjectType")).upper() == "USER"

    if category == "SECURITY":
        return _security(tag, hub, source if source_is_user else "", _group_name(event), event)

    label = TAG_LABELS.get(tag) or _humanize(tag) or category.lower()
    message = f"{hub}: {label}"
    # Name the device (not the hub itself, nor the acting user) and its room
    if source and not source_is_user and source != hub:
        message += f" en {source}"
        room = _clean(event.get("sourceRoomName"))
        if room:
            message += f" ({room})"

    if category == "ALARM":
        return ALARM_TITLES.get(tag, "🛑 ALARMA DETECTADA"), message, "error"
    if category == "ALARM_RECOVERED":
        return "✅ Alarma restablecida", message, "success"
    if category == "MALFUNCTION":
        return "⚠️ Avería detectada", message, "warning"
    return "✅ Avería resuelta", message, "success"
