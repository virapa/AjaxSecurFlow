# API Permissions by Plan

## Overview

AjaxSecurFlow uses a tiered subscription model. Each endpoint requires a specific plan level or higher.

## Plan Tiers

| Plan        | Features                                               |
| ----------- | ------------------------------------------------------ |
| **Free**    | Read-only access to hubs only                          |
| **Basic**   | Free + Devices, rooms, groups + Event logs & telemetry |
| **Pro**     | Basic + Send commands (arm/disarm)                     |
| **Premium** | Pro + Full API proxy access                            |

## Permission Matrix

### Read-Only Endpoints (Free+)

Free tier users can access hub information only:

| Endpoint                     | Method | Feature     | Description                               |
| ---------------------------- | ------ | ----------- | ----------------------------------------- |
| `/api/v1/ajax/hubs`          | GET    | `list_hubs` | List all hubs accessible to user          |
| `/api/v1/ajax/hubs/{hub_id}` | GET    | `list_hubs` | Get detailed information for specific hub |

### Device/Room/Group Endpoints (Basic+)

Requires **Basic** plan or higher:

| Endpoint                                         | Method | Feature        | Description                                  |
| ------------------------------------------------ | ------ | -------------- | -------------------------------------------- |
| `/api/v1/ajax/hubs/{hub_id}/devices`             | GET    | `read_devices` | List all devices in a hub                    |
| `/api/v1/ajax/hubs/{hub_id}/devices/{device_id}` | GET    | `read_devices` | Get detailed information for specific device |
| `/api/v1/ajax/hubs/{hub_id}/rooms`               | GET    | `read_rooms`   | List all rooms in a hub                      |
| `/api/v1/ajax/hubs/{hub_id}/rooms/{room_id}`     | GET    | `read_rooms`   | Get detailed information for specific room   |
| `/api/v1/ajax/hubs/{hub_id}/groups`              | GET    | `read_groups`  | List all groups in a hub                     |

### Monitoring Endpoints (Basic+)

Requires **Basic** plan or higher (in addition to devices/rooms/groups):

| Endpoint                          | Method | Feature     | Description                    |
| --------------------------------- | ------ | ----------- | ------------------------------ |
| `/api/v1/ajax/hubs/{hub_id}/logs` | GET    | `read_logs` | Get event logs with pagination |

### Control Endpoints (Pro+)

Requires **Pro** plan or higher:

| Endpoint                               | Method | Feature         | Description              |
| -------------------------------------- | ------ | --------------- | ------------------------ |
| `/api/v1/ajax/hubs/{hub_id}/arm-state` | POST   | `send_commands` | Set hub arm/disarm state |

### Advanced Endpoints (Premium Only)

Requires **Premium** plan:

| Endpoint         | Method | Feature        | Description                                    |
| ---------------- | ------ | -------------- | ---------------------------------------------- |
| `/api/v1/ajax/*` | ALL    | `access_proxy` | Full Ajax API proxy - access any Ajax endpoint |

## Feature Breakdown by Plan

### Free Plan
✅ **Included Features:**
- `list_hubs` - View all your hubs and their basic information

❌ **Not Included:**
- Device details (devices, rooms, groups)
- Event logs and telemetry
- Command execution (arm/disarm)
- Full API proxy access

**Use Case**: Basic hub overview to see what you have. Upgrade to Basic to see device details.

---

### Basic Plan
✅ **Included Features:**
- All Free features (hubs)
- `read_devices` - View all devices and their status
- `read_rooms` - View room organization
- `read_groups` - View security groups
- `read_telemetry` - Access device telemetry data
- `read_logs` - View event history and logs

❌ **Not Included:**
- Command execution (arm/disarm)
- Full API proxy access

**Use Case**: Complete monitoring with device details, historical data, and event tracking.

---

### Pro Plan
✅ **Included Features:**
- All Basic features (hubs, devices, rooms, groups, logs, telemetry)
- `send_commands` - Arm/disarm your system remotely

❌ **Not Included:**
- Full API proxy access

**Use Case**: Full control over your Ajax system with remote arm/disarm.

---

### Premium Plan
✅ **Included Features:**
- All Pro features (hubs, devices, rooms, groups, logs, telemetry, commands)
- `access_proxy` - Direct access to entire Ajax API

**Use Case**: Advanced integrations and custom automation requiring full API access.

## Error Responses

### 403 Forbidden - Insufficient Permissions

When accessing an endpoint without the required plan, you'll receive:

```json
{
  "detail": "Device access not included in your plan"
}
```

**Common error messages:**
- `"Hub access not included in your plan"` - Requires Free+
- `"Device access not included in your plan"` - Requires Free+
- `"Room access not included in your plan"` - Requires Free+
- `"Group access not included in your plan"` - Requires Free+
- `"Logs access not included in your plan"` - Requires Basic+
- `"Command execution not included in your plan"` - Requires Pro+
- `"PREMIUM subscription required to access Proxy API"` - Requires Premium

### 401 Unauthorized

Missing or invalid authentication token:

```json
{
  "detail": "Not authenticated"
}
```

**Solution**: Include valid Bearer token in Authorization header.

### 429 Too Many Requests

Rate limit exceeded:

```json
{
  "detail": "Rate limit exceeded"
}
```

**Rate Limits by Plan:**
- Free: 100 requests/hour
- Basic: 500 requests/hour
- Pro: 1000 requests/hour
- Premium: 5000 requests/hour

## Plan Migration

### Upgrading Your Plan

Users can upgrade their plan at any time through:

1. **Web Dashboard**: Navigate to `/billing` and select your desired plan
2. **API**: `POST /api/v1/billing/checkout` with plan selection

**Upgrade Process:**
- ✅ Immediate access to new features
- ✅ Prorated billing for remaining period
- ✅ No service interruption

### Downgrading Your Plan

**Downgrade Process:**
- ⏰ Takes effect at end of current billing period
- ✅ Access to premium features maintained until period ends
- ❌ No prorated refunds for downgrades

**Example:**
- Current: Premium plan (renews Feb 15)
- Action: Downgrade to Basic on Feb 1
- Result: Premium access until Feb 15, then Basic starts

### Trial Period

**New User Benefits:**
- 🎁 14-day trial of **Premium** plan
- ✅ Full access to all features during trial
- 🔄 Automatically downgrades to **Free** if no payment method added
- 💳 Add payment method anytime during trial to continue Premium

## Authentication

All endpoints require authentication via Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.ajaxsecurflow.com/api/v1/ajax/hubs
```

### Getting Your Token

**Endpoint**: `POST /api/v1/auth/token`

**Request:**
```json
{
  "username": "your-email@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "your-email@example.com",
    "subscription_plan": "premium",
    "subscription_status": "active"
  }
}
```

## Example Usage

### Free Plan Example

```bash
# ✅ List hubs (Free+)
curl -H "Authorization: Bearer FREE_TOKEN" \
  http://localhost:8000/api/v1/ajax/hubs

# ❌ Get devices (Basic+ required)
curl -H "Authorization: Bearer FREE_TOKEN" \
  http://localhost:8000/api/v1/ajax/hubs/00022777/devices
# Response: 403 {"detail": "Device access not included in your plan"}

# ❌ Get logs (Basic+ required)
curl -H "Authorization: Bearer FREE_TOKEN" \
  http://localhost:8000/api/v1/ajax/hubs/00022777/logs
# Response: 403 {"detail": "Logs access not included in your plan"}
```

### Basic Plan Example

```bash
# ✅ Get logs (Basic+)
curl -H "Authorization: Bearer BASIC_TOKEN" \
  http://localhost:8000/api/v1/ajax/hubs/00022777/logs

# ❌ Send command (Pro+ required)
curl -X POST -H "Authorization: Bearer BASIC_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"armState": 1}' \
  http://localhost:8000/api/v1/ajax/hubs/00022777/arm-state
# Response: 403 {"detail": "Command execution not included in your plan"}
```

### Pro Plan Example

```bash
# ✅ Send arm command (Pro+)
curl -X POST -H "Authorization: Bearer PRO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"armState": 1, "groupId": "group123"}' \
  http://localhost:8000/api/v1/ajax/hubs/00022777/arm-state

# ❌ Access proxy (Premium required)
curl -H "Authorization: Bearer PRO_TOKEN" \
  http://localhost:8000/api/v1/ajax/custom-ajax-endpoint
# Response: 403 {"detail": "PREMIUM subscription required to access Proxy API"}
```

### Premium Plan Example

```bash
# ✅ Full proxy access (Premium)
curl -H "Authorization: Bearer PREMIUM_TOKEN" \
  http://localhost:8000/api/v1/ajax/user/12345/custom-endpoint
```

## Support

For questions about plan features or billing:
- 📧 Email: support@ajaxsecurflow.com
- 📱 Support Portal: `/support`
- 📚 Full API Documentation: `/docs`

## Changelog

### 2026-02-12
- Added granular permission system
- Introduced Free tier with read-only access
- Updated error messages to specify required plan
- Added plan migration documentation
