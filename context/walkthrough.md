# Walkthrough: Enriched Hub Metadata & Secure Auth

We have enhanced the Ajax Hub details to include all technical metadata and hardened the authentication security.

## Enriched Hub Metadata
The `/ajax/hubs/{hub_id}` endpoint now returns the complete state of the Hub, including:
- **State**: ARMED/DISARMED/NIGHT_MODE.
- **Hardware Info**: Model, Color, Subtype.
- **Connectivity**: Detailed Ethernet, GSM, and Jeweller signal info.
- **Battery**: Real-time charge level and charging state.

### [PREVIEW] Updated Hub Schema
```json
{
  "hubId": "0004C602",
  "hubName": "HUB 2 PRUEBAS SATYA",
  "state": "ARMED",
  "online": true,
  "battery": {
    "chargeLevelPercentage": 100,
    "state": "CHARGED"
  },
  "firmware": {
    "version": "2.35.131",
    "newVersionAvailable": true
  }
}
```

## Enriched Device Details
We have added a new dedicated endpoint to get deep telemetry from any device:
**`GET /api/v1/ajax/hubs/{hub_id}/devices/{device_id}`**

This returns the schema you provided, including:
- **Environment**: Temperature, Signal Level.
- **Hardware**: Color, Firmware, Tamper state.
- **Power**: Detailed battery charge percentage.
- **Config**: Arming delays, Night mode settings, Malfunctions list.

## Generic Proxy Access (Catch-all)
For advanced development, we have a dynamic route that allows calling ANY Ajax API endpoint:
**`ANY /api/v1/ajax/{path:path}`**

- **Why use it?**: To access features not yet explicitly mapped in this backend.
- **How it works**: You call our proxy, and it automatically injects your Ajax session tokens, logs the action for audit, and enforces your Stripe subscription limits.

## Secure Authentication Hardening
- **Generic Error Messages**: All auth failures now return "Invalid credentials" to prevent information leakage.
- **Unified Login**: Simplified Swagger UI with a single API Key header input.
- **Fingerprinting**: Internal security logs still track the exact reason for failure (UA mismatch, IP change, etc.) while keeping the user response opaque.

## Developer Experience
- **ENABLE_DEVELOPER_MODE**: New bypass for Stripe during development.
- **Clean Swagger UI**: Removed unnecessary OAuth2 fields for a streamlined experience.

## Verification Results
- All 40 unit and integration tests passed.
- Redundant `flower` container removed for a leaner stack.
