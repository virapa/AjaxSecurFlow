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

## B2B Voucher System (New Rules)
- **Voucher Model**: Unique codes (AJAX-XXXX-XXXX) that grant **Premium** plan access for a fixed term (30-365 days).
- **Redemption Limit**: Maximum **5 vouchers** can be redeemed per account to prevent abuse.
- **Additive Time**: Redeeming multiple vouchers extends the expiration date incrementally.
- **Automatic Fallback**: Users revert to the **Free** plan immediately upon expiration if no active Stripe subscription exists.
- **Hybrid Security**: Generation is blinded and requires `ADMIN_EMAILS` membership plus `X-Admin-Secret` header.

## Background Maintenance
- **Celery Beat Execution**: A daily cron job (`cleanup_expired_subscriptions`) runs at midnight to synchronize the database states.

## Communication & Notifications System
- **In-App Dashboard Alerts**: Real-time notifications for billing, security, and account status.
- **Transactional Emails (Celery + SMTP)**: Automated professional emails for:
    - Welcome (Subscription Activation).
    - Renewals (Subscription Updated).
    - Cancellations (Subscription Deleted).
    - Urgent Action (Payment Failed).
- **Security Awareness**: Proactive notifications if a session IP change is detected.

## Verification Results
- All 42 unit and integration tests passed (including new Notification & Voucher suites).
- SMTP Connectivity verified with Mailgun (diag script `test_smtp.py`).
- No vulnerabilities found via `pip-audit` or `bandit`.
- Q&A Standards applied: Google-style Docstrings & Strict Type Hinting.
- Database upgraded: New migration for `notifications` table.
