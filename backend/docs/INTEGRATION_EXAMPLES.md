# Integration Examples

## Overview

This guide provides real-world integration examples for AjaxSecurFlow API across all subscription tiers. Each example includes code in multiple languages (Python, JavaScript, cURL) and demonstrates best practices for error handling, rate limiting, and authentication.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Free Tier Examples](#free-tier-examples)
3. [Basic Tier Examples](#basic-tier-examples)
4. [Pro Tier Examples](#pro-tier-examples)
5. [Premium Tier Examples](#premium-tier-examples)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Webhooks](#webhooks)

---

## Authentication

All API requests require a Bearer token obtained through the authentication endpoint.

### Getting an Access Token

#### cURL
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-email@example.com",
    "password": "your-password"
  }'
```

#### Python
```python
import requests

def get_access_token(email: str, password: str) -> str:
    """Authenticate and get access token"""
    response = requests.post(
        "http://localhost:8000/api/v1/auth/token",
        json={"username": email, "password": password}
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"]

# Usage
token = get_access_token("your-email@example.com", "your-password")
print(f"Token: {token}")
```

#### JavaScript (Node.js)
```javascript
const axios = require('axios');

async function getAccessToken(email, password) {
  const response = await axios.post(
    'http://localhost:8000/api/v1/auth/token',
    { username: email, password: password }
  );
  return response.data.access_token;
}

// Usage
const token = await getAccessToken('your-email@example.com', 'your-password');
console.log(`Token: ${token}`);
```

#### Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "your-email@example.com",
    "subscription_plan": "basic",
    "subscription_status": "active",
    "subscription_expires_at": "2026-03-15T00:00:00Z"
  }
}
```

---

## Free Tier Examples

Free tier provides read-only access to hub information.

### Example 1: List All Hubs

#### cURL
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/ajax/hubs
```

#### Python
```python
import requests

def list_hubs(token: str):
    """List all hubs (Free+)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "http://localhost:8000/api/v1/ajax/hubs",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# Usage
hubs = list_hubs(token)
for hub in hubs:
    print(f"Hub: {hub['name']} (ID: {hub['id']}) - Status: {hub['status']}")
```

#### JavaScript
```javascript
async function listHubs(token) {
  const response = await axios.get(
    'http://localhost:8000/api/v1/ajax/hubs',
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

// Usage
const hubs = await listHubs(token);
hubs.forEach(hub => {
  console.log(`Hub: ${hub.name} (ID: ${hub.id}) - Status: ${hub.status}`);
});
```

#### Response
```json
[
  {
    "id": "00022777",
    "name": "Home Security",
    "status": "armed",
    "online": true,
    "role": "MASTER"
  }
]
```

### Example 2: Get Hub Details

#### Python
```python
def get_hub_details(token: str, hub_id: str):
    """Get detailed hub information (Free+)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"http://localhost:8000/api/v1/ajax/hubs/{hub_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# Usage
hub = get_hub_details(token, "00022777")
print(f"Hub: {hub['name']}")
print(f"Armed: {hub['status'] == 'armed'}")
print(f"Online: {hub['online']}")
```

### Example 3: Free Tier Limitation

```python
# This will fail with 403 Forbidden
try:
    response = requests.get(
        f"http://localhost:8000/api/v1/ajax/hubs/00022777/devices",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
except requests.HTTPError as e:
    if e.response.status_code == 403:
        print("❌ Device access requires Basic plan or higher")
        print(f"Error: {e.response.json()['detail']}")
```

---

## Basic Tier Examples

Basic tier adds access to devices, rooms, groups, and event logs.

### Example 1: List Devices

#### Python
```python
def list_devices(token: str, hub_id: str):
    """List all devices in a hub (Basic+)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"http://localhost:8000/api/v1/ajax/hubs/{hub_id}/devices",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# Usage
devices = list_devices(token, "00022777")
for device in devices:
    print(f"Device: {device['name']}")
    print(f"  Type: {device['type']}")
    print(f"  Battery: {device.get('battery', 'N/A')}%")
    print(f"  Signal: {device.get('signal', 'N/A')}")
```

#### JavaScript
```javascript
async function listDevices(token, hubId) {
  const response = await axios.get(
    `http://localhost:8000/api/v1/ajax/hubs/${hubId}/devices`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

// Usage
const devices = await listDevices(token, '00022777');
devices.forEach(device => {
  console.log(`Device: ${device.name}`);
  console.log(`  Type: ${device.type}`);
  console.log(`  Battery: ${device.battery || 'N/A'}%`);
});
```

### Example 2: Get Event Logs

#### Python
```python
def get_event_logs(token: str, hub_id: str, limit: int = 10):
    """Get event logs for a hub (Basic+)"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": limit}
    response = requests.get(
        f"http://localhost:8000/api/v1/ajax/hubs/{hub_id}/logs",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    return response.json()

# Usage
logs = get_event_logs(token, "00022777", limit=20)
for log in logs:
    print(f"[{log['timestamp']}] {log['event_desc']}")
    print(f"  Device: {log.get('device_name', 'System')}")
    print(f"  User: {log.get('user_name', 'N/A')}")
```

### Example 3: Monitor Device Telemetry

#### Python
```python
import time

def monitor_devices(token: str, hub_id: str, interval: int = 60):
    """Monitor device telemetry in real-time (Basic+)"""
    while True:
        devices = list_devices(token, hub_id)
        
        print(f"\n=== Device Status at {time.strftime('%H:%M:%S')} ===")
        for device in devices:
            battery = device.get('battery', 'N/A')
            signal = device.get('signal', 'N/A')
            
            # Alert on low battery
            if isinstance(battery, (int, float)) and battery < 20:
                print(f"⚠️  {device['name']}: LOW BATTERY ({battery}%)")
            else:
                print(f"✅ {device['name']}: Battery {battery}%, Signal {signal}")
        
        time.sleep(interval)

# Usage
monitor_devices(token, "00022777", interval=300)  # Check every 5 minutes
```

### Example 4: List Rooms and Groups

#### Python
```python
def get_hub_structure(token: str, hub_id: str):
    """Get complete hub structure (rooms and groups) - Basic+"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get rooms
    rooms_response = requests.get(
        f"http://localhost:8000/api/v1/ajax/hubs/{hub_id}/rooms",
        headers=headers
    )
    rooms = rooms_response.json()
    
    # Get groups
    groups_response = requests.get(
        f"http://localhost:8000/api/v1/ajax/hubs/{hub_id}/groups",
        headers=headers
    )
    groups = groups_response.json()
    
    return {"rooms": rooms, "groups": groups}

# Usage
structure = get_hub_structure(token, "00022777")
print("Rooms:")
for room in structure['rooms']:
    print(f"  - {room['name']}")

print("\nGroups:")
for group in structure['groups']:
    print(f"  - {group['name']}")
```

---

## Pro Tier Examples

Pro tier adds command execution capabilities (arm/disarm).

### Example 1: Arm System

#### Python
```python
def arm_system(token: str, hub_id: str, mode: str = "full"):
    """Arm the security system (Pro+)
    
    Args:
        mode: 'full' (arm all), 'night' (night mode), or 'partial' (partial arm)
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    # Map modes to arm states
    arm_states = {
        "full": 1,      # Armed (full)
        "night": 2,     # Night mode
        "partial": 3    # Partial arm
    }
    
    payload = {"armState": arm_states.get(mode, 1)}
    
    response = requests.post(
        f"http://localhost:8000/api/v1/ajax/hubs/{hub_id}/arm-state",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()

# Usage
result = arm_system(token, "00022777", mode="full")
print(f"System armed: {result['success']}")
```

#### JavaScript
```javascript
async function armSystem(token, hubId, mode = 'full') {
  const armStates = {
    full: 1,
    night: 2,
    partial: 3
  };
  
  const response = await axios.post(
    `http://localhost:8000/api/v1/ajax/hubs/${hubId}/arm-state`,
    { armState: armStates[mode] || 1 },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  
  return response.data;
}

// Usage
const result = await armSystem(token, '00022777', 'full');
console.log(`System armed: ${result.success}`);
```

### Example 2: Disarm System

#### Python
```python
def disarm_system(token: str, hub_id: str):
    """Disarm the security system (Pro+)"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"armState": 0}  # 0 = Disarmed
    
    response = requests.post(
        f"http://localhost:8000/api/v1/ajax/hubs/{hub_id}/arm-state",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()

# Usage
result = disarm_system(token, "00022777")
print(f"System disarmed: {result['success']}")
```

### Example 3: Automated Arm/Disarm Schedule

#### Python
```python
from datetime import datetime, time as dt_time
import schedule

def auto_arm_disarm(token: str, hub_id: str):
    """Automatically arm at night and disarm in morning (Pro+)"""
    
    def morning_disarm():
        print(f"[{datetime.now()}] Disarming system...")
        disarm_system(token, hub_id)
    
    def evening_arm():
        print(f"[{datetime.now()}] Arming system...")
        arm_system(token, hub_id, mode="night")
    
    # Schedule tasks
    schedule.every().day.at("07:00").do(morning_disarm)
    schedule.every().day.at("23:00").do(evening_arm)
    
    print("Automated schedule started:")
    print("  - Disarm at 07:00")
    print("  - Arm (night mode) at 23:00")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Usage
auto_arm_disarm(token, "00022777")
```

### Example 4: Conditional Arming Based on Sensors

#### Python
```python
def smart_arm(token: str, hub_id: str):
    """Arm system only if all windows/doors are closed (Pro+)"""
    
    # Get all devices
    devices = list_devices(token, hub_id)
    
    # Check for open doors/windows
    open_sensors = [
        d for d in devices 
        if d['type'] in ['DoorProtect', 'DoorProtectPlus'] 
        and d.get('status') == 'open'
    ]
    
    if open_sensors:
        print("❌ Cannot arm: The following sensors are open:")
        for sensor in open_sensors:
            print(f"  - {sensor['name']}")
        return False
    
    # All clear, arm the system
    print("✅ All sensors closed. Arming system...")
    result = arm_system(token, hub_id, mode="full")
    return result['success']

# Usage
smart_arm(token, "00022777")
```

---

## Premium Tier Examples

Premium tier provides full Ajax API proxy access for custom integrations.

### Example 1: Direct Ajax API Access

#### Python
```python
def ajax_proxy_request(token: str, endpoint: str, method: str = "GET", data: dict = None):
    """Make direct Ajax API requests via proxy (Premium only)"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"http://localhost:8000/api/v1/ajax/{endpoint}"
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    
    response.raise_for_status()
    return response.json()

# Usage - Access any Ajax endpoint
custom_data = ajax_proxy_request(token, "user/12345/custom-endpoint")
```

### Example 2: Advanced Automation

#### Python
```python
def advanced_automation(token: str, hub_id: str):
    """Complex automation using full API access (Premium only)"""
    
    # Get detailed system state via proxy
    system_state = ajax_proxy_request(token, f"hubs/{hub_id}/state")
    
    # Custom logic based on multiple factors
    if system_state['temperature'] > 30 and system_state['humidity'] < 40:
        # Fire risk conditions
        print("⚠️  Fire risk detected - activating enhanced monitoring")
        ajax_proxy_request(
            token,
            f"hubs/{hub_id}/monitoring/mode",
            method="POST",
            data={"mode": "enhanced"}
        )
    
    # Access custom Ajax features not exposed in standard API
    ajax_proxy_request(
        token,
        f"hubs/{hub_id}/custom-feature",
        method="POST",
        data={"setting": "value"}
    )
```

### Example 3: Bulk Operations

#### Python
```python
def bulk_device_configuration(token: str, hub_id: str, config: dict):
    """Configure multiple devices at once (Premium only)"""
    devices = list_devices(token, hub_id)
    
    results = []
    for device in devices:
        try:
            # Use proxy to access device configuration endpoint
            result = ajax_proxy_request(
                token,
                f"devices/{device['id']}/config",
                method="PUT",
                data=config
            )
            results.append({"device": device['name'], "success": True})
        except Exception as e:
            results.append({"device": device['name'], "success": False, "error": str(e)})
    
    return results

# Usage
config = {"sensitivity": "high", "led_enabled": False}
results = bulk_device_configuration(token, "00022777", config)
for r in results:
    status = "✅" if r['success'] else "❌"
    print(f"{status} {r['device']}")
```

---

## Error Handling

### Handling 403 Forbidden (Insufficient Plan)

#### Python
```python
def safe_api_call(token: str, endpoint: str, required_plan: str):
    """Make API call with plan-aware error handling"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"http://localhost:8000/api/v1/ajax/{endpoint}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            error_detail = e.response.json().get('detail', '')
            print(f"❌ Access Denied: {error_detail}")
            print(f"💡 Upgrade to {required_plan} plan to access this feature")
            print(f"   Visit: http://localhost:3000/billing")
            return None
        raise

# Usage
devices = safe_api_call(token, "hubs/00022777/devices", "Basic")
```

### Handling 401 Unauthorized (Token Expired)

#### Python
```python
def api_call_with_retry(email: str, password: str, endpoint: str):
    """API call with automatic token refresh on 401"""
    token = get_access_token(email, password)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"http://localhost:8000/api/v1/ajax/{endpoint}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            # Token expired, get new one
            print("Token expired, refreshing...")
            token = get_access_token(email, password)
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"http://localhost:8000/api/v1/ajax/{endpoint}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        raise
```

---

## Rate Limiting

### Rate Limits by Plan

| Plan | Requests/Hour | Burst Limit |
|------|---------------|-------------|
| Free | 100 | 10/minute |
| Basic | 500 | 50/minute |
| Pro | 1000 | 100/minute |
| Premium | 5000 | 500/minute |

### Handling Rate Limits

#### Python
```python
import time
from functools import wraps

def rate_limited(max_per_minute: int):
    """Decorator to enforce rate limiting"""
    min_interval = 60.0 / max_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

# Usage
@rate_limited(max_per_minute=50)  # Basic plan limit
def get_devices(token: str, hub_id: str):
    return list_devices(token, hub_id)

# This will automatically throttle to 50 requests/minute
for i in range(100):
    devices = get_devices(token, "00022777")
    print(f"Request {i+1}: {len(devices)} devices")
```

### Handling 429 Too Many Requests

#### Python
```python
def api_call_with_backoff(token: str, endpoint: str, max_retries: int = 3):
    """API call with exponential backoff on rate limit"""
    for attempt in range(max_retries):
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"http://localhost:8000/api/v1/ajax/{endpoint}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception("Max retries exceeded")
```

---

## Webhooks

### Stripe Webhook Integration

#### Python (Flask)
```python
from flask import Flask, request
import stripe

app = Flask(__name__)
stripe.api_key = "your_stripe_secret_key"
webhook_secret = "your_webhook_secret"

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle subscription events
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        print(f"New subscription: {subscription['id']}")
        # Update user plan in your database
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        print(f"Subscription updated: {subscription['id']}")
        # Update user plan
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        print(f"Subscription cancelled: {subscription['id']}")
        # Downgrade user to Free
    
    return 'Success', 200

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Complete Integration Example

### Full-Featured Monitoring Dashboard

#### Python
```python
import requests
import time
from datetime import datetime

class AjaxSecurFlowClient:
    def __init__(self, email: str, password: str, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = self._authenticate(email, password)
        self.plan = self._get_user_plan()
    
    def _authenticate(self, email: str, password: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/v1/auth/token",
            json={"username": email, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    
    def _get_user_plan(self) -> str:
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
        return response.json()["subscription_plan"]
    
    def _request(self, method: str, endpoint: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        
        response = requests.request(
            method,
            f"{self.base_url}/api/v1/ajax/{endpoint}",
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def list_hubs(self):
        return self._request("GET", "hubs")
    
    def list_devices(self, hub_id: str):
        if self.plan == "free":
            raise PermissionError("Device access requires Basic plan or higher")
        return self._request("GET", f"hubs/{hub_id}/devices")
    
    def get_logs(self, hub_id: str, limit: int = 10):
        if self.plan == "free":
            raise PermissionError("Log access requires Basic plan or higher")
        return self._request("GET", f"hubs/{hub_id}/logs", params={"limit": limit})
    
    def arm_system(self, hub_id: str, mode: str = "full"):
        if self.plan not in ["pro", "premium"]:
            raise PermissionError("Command execution requires Pro plan or higher")
        
        arm_states = {"full": 1, "night": 2, "partial": 3}
        return self._request(
            "POST",
            f"hubs/{hub_id}/arm-state",
            json={"armState": arm_states.get(mode, 1)}
        )
    
    def monitor(self, hub_id: str, interval: int = 60):
        """Real-time monitoring loop"""
        print(f"Starting monitoring for hub {hub_id} (Plan: {self.plan})")
        
        while True:
            try:
                # Get hub status
                hubs = self.list_hubs()
                hub = next((h for h in hubs if h['id'] == hub_id), None)
                
                if not hub:
                    print(f"Hub {hub_id} not found")
                    break
                
                print(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
                print(f"Hub: {hub['name']}")
                print(f"Status: {hub['status']}")
                print(f"Online: {hub['online']}")
                
                # Get devices (if Basic+)
                if self.plan in ["basic", "pro", "premium"]:
                    devices = self.list_devices(hub_id)
                    print(f"\nDevices ({len(devices)}):")
                    for device in devices[:5]:  # Show first 5
                        battery = device.get('battery', 'N/A')
                        print(f"  - {device['name']}: Battery {battery}%")
                
                # Get recent logs (if Basic+)
                if self.plan in ["basic", "pro", "premium"]:
                    logs = self.get_logs(hub_id, limit=3)
                    print(f"\nRecent Events:")
                    for log in logs:
                        print(f"  - [{log['timestamp']}] {log['event_desc']}")
                
                time.sleep(interval)
            
            except KeyboardInterrupt:
                print("\nMonitoring stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(interval)

# Usage
client = AjaxSecurFlowClient("your-email@example.com", "your-password")
client.monitor("00022777", interval=300)  # Monitor every 5 minutes
```

---

## Related Documentation

- [API Permissions](./API_PERMISSIONS.md) - Detailed permission matrix
- [Plan Migration Guide](./PLAN_MIGRATION_GUIDE.md) - Upgrading/downgrading plans
- [OpenAPI Documentation](http://localhost:8000/docs) - Interactive API explorer
