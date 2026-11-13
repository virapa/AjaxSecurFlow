# Home Assistant Integration: `ajaxsecurflow-hass` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A HACS-installable Home Assistant integration (`ajaxsecurflow` domain) that authenticates with an AjaxSecurFlow integration token, polls hubs/devices/groups, receives real-time events over SSE, and exposes alarm panels, binary sensors and sensors.

**Architecture:** Config flow validates the token against `/auth/me`. One `DataUpdateCoordinator` per entry polls the REST endpoints; an `SSEListener` background task applies partial updates from `/ajax/events/stream` through a pure `apply_event` function and fires `ajaxsecurflow_event` on the HA bus. Entities are thin `CoordinatorEntity` subclasses driven by entity descriptions.

**Tech Stack:** Home Assistant ≥ 2025.1 (Python 3.13), aiohttp (bundled with HA), voluptuous, pytest + `pytest-homeassistant-custom-component`, `aioresponses`.

**Spec:** `AjaxSecurFlow/docs/superpowers/specs/2026-09-18-home-assistant-integration-design.md` (sections 6, 7, 8).

**Prerequisite:** The backend plan (`2026-09-18-ha-integration-backend.md`) deployed, or a local backend on `feat/ha-integration`, so a real token can be used for the smoke test in the last task. All automated tests here mock the API.

**Conventions:**
- Repo lives at `../ajaxsecurflow-hass` (sibling of `AjaxSecurFlow`). All paths below are relative to that repo root.
- Run tests from the repo root: `python -m pytest tests -v` (create a venv first, Task 1).
- Code, comments, identifiers and commit messages in English. User-facing strings in `strings.json` (English) and `translations/es.json`.

---

## File map

| Path | Responsibility |
|---|---|
| `hacs.json`, `README.md`, `LICENSE`, `.gitignore`, `pyproject.toml`, `requirements_test.txt` | repo scaffold |
| `.github/workflows/validate.yml` | hassfest + HACS validation |
| `custom_components/ajaxsecurflow/manifest.json` | integration metadata |
| `custom_components/ajaxsecurflow/const.py` | domain, config keys, defaults, event-tag sets |
| `custom_components/ajaxsecurflow/api.py` | `AjaxSecurFlowClient`, errors, `SSEParser` |
| `custom_components/ajaxsecurflow/models.py` | `HubData` dataclass |
| `custom_components/ajaxsecurflow/events.py` | `apply_event(data, envelope)` pure state update |
| `custom_components/ajaxsecurflow/coordinator.py` | `AjaxSecurFlowCoordinator` |
| `custom_components/ajaxsecurflow/sse.py` | `SSEListener` background task with backoff |
| `custom_components/ajaxsecurflow/config_flow.py` | user / reauth / options flows |
| `custom_components/ajaxsecurflow/__init__.py` | setup / unload, runtime data |
| `custom_components/ajaxsecurflow/entity.py` | base hub/device entities with device_info |
| `custom_components/ajaxsecurflow/alarm_control_panel.py` | hub + group panels |
| `custom_components/ajaxsecurflow/binary_sensor.py` | device + hub binary sensors |
| `custom_components/ajaxsecurflow/sensor.py` | device + hub sensors |
| `custom_components/ajaxsecurflow/diagnostics.py` | redacted dump |
| `custom_components/ajaxsecurflow/strings.json`, `translations/en.json`, `translations/es.json` | UI strings |
| `tests/conftest.py` | fixtures: mocked client, config entry |
| `tests/test_api.py`, `test_events.py`, `test_config_flow.py`, `test_init.py`, `test_alarm_control_panel.py`, `test_binary_sensor.py`, `test_sensor.py`, `test_sse.py` | tests |

---

### Task 1: Repository scaffold

**Files:**
- Create: `hacs.json`, `.gitignore`, `pyproject.toml`, `requirements_test.txt`, `LICENSE`, `.github/workflows/validate.yml`
- Create: `custom_components/ajaxsecurflow/manifest.json`, `custom_components/ajaxsecurflow/const.py`, `custom_components/ajaxsecurflow/__init__.py` (placeholder, replaced in Task 8)
- Create: `tests/__init__.py`, `tests/conftest.py` (minimal, extended in Task 8)

- [ ] **Step 1: Create the repo and venv**

```bash
cd ..
mkdir ajaxsecurflow-hass && cd ajaxsecurflow-hass
git init -b main
python -m venv venv
# Windows: venv\Scripts\activate ; Unix: source venv/bin/activate
```

- [ ] **Step 2: Scaffold files**

`.gitignore`:
```
venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
.vscode/
```

`hacs.json`:
```json
{
  "name": "AjaxSecurFlow",
  "render_readme": true,
  "homeassistant": "2025.1.0"
}
```

`requirements_test.txt`:
```
pytest-homeassistant-custom-component>=0.13.200
aioresponses>=0.7.6
```

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

`LICENSE`: copy `AjaxSecurFlow/LICENSE` verbatim (same proprietary license and copyright holder).

`.github/workflows/validate.yml`:
```yaml
name: Validate
on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master
  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements_test.txt
      - run: python -m pytest tests -q
```

`custom_components/ajaxsecurflow/manifest.json`:
```json
{
  "domain": "ajaxsecurflow",
  "name": "AjaxSecurFlow",
  "codeowners": ["@virapa"],
  "config_flow": true,
  "documentation": "https://github.com/virapa/ajaxsecurflow-hass",
  "integration_type": "hub",
  "iot_class": "cloud_push",
  "issue_tracker": "https://github.com/virapa/ajaxsecurflow-hass/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

`custom_components/ajaxsecurflow/const.py`:
```python
"""Constants for the AjaxSecurFlow integration."""
from typing import Final

DOMAIN: Final = "ajaxsecurflow"
VERSION: Final = "0.1.0"
USER_AGENT: Final = f"ajaxsecurflow-hass/{VERSION}"
API_PREFIX: Final = "/api/v1"

CONF_BASE_URL: Final = "base_url"
CONF_TOKEN: Final = "token"
CONF_SCAN_INTERVAL: Final = "scan_interval"

DEFAULT_BASE_URL: Final = "https://api.ajaxsecurflow.com"
DEFAULT_SCAN_INTERVAL: Final = 60
MIN_SCAN_INTERVAL: Final = 30
MAX_SCAN_INTERVAL: Final = 600

REQUEST_TIMEOUT: Final = 15
STREAM_READ_TIMEOUT: Final = 90  # backend pings every 15 s
SSE_BACKOFF_MIN: Final = 5
SSE_BACKOFF_MAX: Final = 300

EVENT_NAME: Final = "ajaxsecurflow_event"

PLANS_WITH_DEVICES: Final = frozenset({"basic", "pro", "premium"})
PLANS_WITH_CONTROL: Final = frozenset({"pro", "premium"})

ARM_STATE_DISARM: Final = 0
ARM_STATE_ARM: Final = 1
ARM_STATE_NIGHT: Final = 2

SIGNAL_LEVELS: Final = ["NO_SIGNAL", "WEAK", "NORMAL", "STRONG"]

# Event tags (Ajax `eventTag`, matched case-insensitively) → which device flag they drive.
ARM_TAGS: Final = frozenset({"arm", "armed"})
DISARM_TAGS: Final = frozenset({"disarm", "disarmed"})
NIGHT_ON_TAGS: Final = frozenset({"nightmodeon", "nightmode", "night_mode_on"})
NIGHT_OFF_TAGS: Final = frozenset({"nightmodeoff", "night_mode_off"})
OPENING_TAGS: Final = frozenset({"opened", "reedopened", "contactopened", "dooropened"})
EXT_CONTACT_TAGS: Final = frozenset({"extcontactopened"})
MOTION_TAGS: Final = frozenset({"motiondetected", "motion"})
GLASS_TAGS: Final = frozenset({"glassbreak", "glassbreakdetected"})
LEAK_TAGS: Final = frozenset({"leak", "leakdetected", "leakagedetected"})
SMOKE_TAGS: Final = frozenset({"smoke", "smokedetected", "smokealarm", "firealarm"})
OFFLINE_TAGS: Final = frozenset({"offline", "devicelost", "lostconnection", "connectionlost"})
```

Placeholder `custom_components/ajaxsecurflow/__init__.py` (replaced in Task 8):
```python
"""AjaxSecurFlow integration for Home Assistant."""
```

`tests/__init__.py`: empty file.

`tests/conftest.py` (minimal; extended in Task 8):
```python
"""Shared fixtures."""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield
```

- [ ] **Step 3: Install and verify the test harness loads**

```bash
pip install -r requirements_test.txt
python -m pytest tests -q
```
Expected: `no tests ran` with exit code 5 and no import errors.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: scaffold ajaxsecurflow HACS integration"
```

---

### Task 2: API client and SSE parser

**Files:**
- Create: `custom_components/ajaxsecurflow/api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_api.py
import pytest
from aioresponses import aioresponses
from yarl import URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.ajaxsecurflow.api import (
    AjaxSecurFlowClient, ApiError, AuthError, PlanError, RateLimitError, SSEParser,
)

BASE = "https://api.test"


def _client(hass):
    return AjaxSecurFlowClient(async_get_clientsession(hass), BASE, "asf_abc")


async def test_get_hubs_sends_bearer_and_user_agent(hass):
    with aioresponses() as m:
        m.get(f"{BASE}/api/v1/ajax/hubs", payload=[{"id": "HUB1"}])
        hubs = await _client(hass).get_hubs()
        call = m.requests[("GET", URL(f"{BASE}/api/v1/ajax/hubs"))][0]
    assert hubs == [{"id": "HUB1"}]
    assert call.kwargs["headers"]["Authorization"] == "Bearer asf_abc"
    assert call.kwargs["headers"]["User-Agent"].startswith("ajaxsecurflow-hass/")


async def test_base_url_trailing_slash_is_normalized(hass):
    client = AjaxSecurFlowClient(async_get_clientsession(hass), BASE + "/", "asf_abc")
    with aioresponses() as m:
        m.get(f"{BASE}/api/v1/auth/me", payload={"email": "u@x.com"})
        assert (await client.get_me())["email"] == "u@x.com"


@pytest.mark.parametrize("status,exc", [(401, AuthError), (403, PlanError), (429, RateLimitError), (500, ApiError)])
async def test_status_mapping(hass, status, exc):
    with aioresponses() as m:
        m.get(f"{BASE}/api/v1/ajax/hubs", status=status)
        with pytest.raises(exc):
            await _client(hass).get_hubs()


async def test_set_arm_state_body(hass):
    with aioresponses() as m:
        m.post(f"{BASE}/api/v1/ajax/hubs/HUB1/arm-state", payload={"success": True})
        await _client(hass).set_arm_state("HUB1", 1, "G1")
        call = m.requests[("POST", URL(f"{BASE}/api/v1/ajax/hubs/HUB1/arm-state"))][0]
    assert call.kwargs["json"] == {"armState": 1, "groupId": "G1"}


async def test_set_arm_state_without_group(hass):
    with aioresponses() as m:
        m.post(f"{BASE}/api/v1/ajax/hubs/HUB1/arm-state", payload={"success": True})
        await _client(hass).set_arm_state("HUB1", 0)
        call = m.requests[("POST", URL(f"{BASE}/api/v1/ajax/hubs/HUB1/arm-state"))][0]
    assert call.kwargs["json"] == {"armState": 0}


def test_sse_parser_yields_only_complete_ajax_events():
    p = SSEParser()
    assert p.feed(": connected to 2 hub channels\n") is None
    assert p.feed("event: ajax_event\n") is None
    assert p.feed('data: {"hub_id": "HUB1", "event_type": "ALARM"}\n') is None
    out = p.feed("\n")
    assert out == {"hub_id": "HUB1", "event_type": "ALARM"}


def test_sse_parser_ignores_pings_and_other_events():
    p = SSEParser()
    assert p.feed(": ping\n") is None
    assert p.feed("\n") is None
    p.feed("event: other\n")
    p.feed('data: {"x": 1}\n')
    assert p.feed("\n") is None


def test_sse_parser_data_without_event_name_is_accepted():
    p = SSEParser()
    p.feed('data: {"hub_id": "HUB1"}\n')
    assert p.feed("\n") == {"hub_id": "HUB1"}


def test_sse_parser_invalid_json_is_dropped():
    p = SSEParser()
    p.feed("event: ajax_event\n")
    p.feed("data: not-json\n")
    assert p.feed("\n") is None


async def test_stream_events_yields_envelopes(hass):
    body = (
        b": connected\n\n"
        b"event: ajax_event\n"
        b'data: {"hub_id": "HUB1", "event_type": "SECURITY"}\n\n'
        b": ping\n\n"
    )
    with aioresponses() as m:
        m.get(f"{BASE}/api/v1/ajax/events/stream", body=body)
        events = [e async for e in _client(hass).stream_events()]
    assert events == [{"hub_id": "HUB1", "event_type": "SECURITY"}]


async def test_stream_events_403_raises_plan_error(hass):
    with aioresponses() as m:
        m.get(f"{BASE}/api/v1/ajax/events/stream", status=403)
        with pytest.raises(PlanError):
            async for _ in _client(hass).stream_events():
                pass
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'custom_components.ajaxsecurflow.api'`

- [ ] **Step 3: Write the client**

```python
# custom_components/ajaxsecurflow/api.py
"""HTTP client for the AjaxSecurFlow API."""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import aiohttp

from .const import API_PREFIX, REQUEST_TIMEOUT, STREAM_READ_TIMEOUT, USER_AGENT

_LOGGER = logging.getLogger(__name__)


class AjaxSecurFlowError(Exception):
    """Base error."""


class AuthError(AjaxSecurFlowError):
    """401: token invalid or revoked."""


class PlanError(AjaxSecurFlowError):
    """403: feature not in the user's plan."""


class RateLimitError(AjaxSecurFlowError):
    """429: rate limited."""


class ApiError(AjaxSecurFlowError):
    """Any other transport or HTTP error."""


class SSEParser:
    """Incremental text/event-stream parser. Feed one line at a time; get an envelope on blank line."""

    def __init__(self) -> None:
        self._event: str | None = None
        self._data: list[str] = []

    def feed(self, line: str) -> dict[str, Any] | None:
        line = line.rstrip("\r\n")
        if line == "":
            return self._flush()
        if line.startswith(":"):
            return None
        field, _, value = line.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if field == "event":
            self._event = value
        elif field == "data":
            self._data.append(value)
        return None

    def _flush(self) -> dict[str, Any] | None:
        event, data = self._event, self._data
        self._event, self._data = None, []
        if not data or event not in (None, "ajax_event"):
            return None
        try:
            parsed = json.loads("\n".join(data))
        except json.JSONDecodeError:
            _LOGGER.debug("Dropping non-JSON SSE payload")
            return None
        return parsed if isinstance(parsed, dict) else None


class AjaxSecurFlowClient:
    """Async client over Home Assistant's shared aiohttp session."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, token: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self._base_url}{API_PREFIX}{path}"

    @staticmethod
    def _raise_for_status(resp: aiohttp.ClientResponse) -> None:
        if resp.status == 401:
            raise AuthError("Invalid or revoked token")
        if resp.status == 403:
            raise PlanError("Not available in your plan")
        if resp.status == 429:
            raise RateLimitError("Rate limit exceeded")
        if resp.status >= 400:
            raise ApiError(f"HTTP {resp.status}")

    async def _request(self, method: str, path: str, json_body: dict[str, Any] | None = None) -> Any:
        try:
            async with self._session.request(
                method,
                self._url(path),
                headers=self._headers,
                json=json_body,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                self._raise_for_status(resp)
                return await resp.json()
        except aiohttp.ClientError as err:
            raise ApiError(str(err)) from err
        except TimeoutError as err:
            raise ApiError("Request timed out") from err

    async def get_me(self) -> dict[str, Any]:
        return await self._request("GET", "/auth/me")

    async def get_hubs(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/ajax/hubs")

    async def get_hub(self, hub_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/ajax/hubs/{hub_id}")

    async def get_devices(self, hub_id: str) -> list[dict[str, Any]]:
        return await self._request("GET", f"/ajax/hubs/{hub_id}/devices")

    async def get_groups(self, hub_id: str) -> list[dict[str, Any]]:
        return await self._request("GET", f"/ajax/hubs/{hub_id}/groups")

    async def get_rooms(self, hub_id: str) -> list[dict[str, Any]]:
        return await self._request("GET", f"/ajax/hubs/{hub_id}/rooms")

    async def set_arm_state(self, hub_id: str, arm_state: int, group_id: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"armState": arm_state}
        if group_id:
            body["groupId"] = group_id
        return await self._request("POST", f"/ajax/hubs/{hub_id}/arm-state", body)

    async def stream_events(self) -> AsyncIterator[dict[str, Any]]:
        """Yield hybrid-envelope dicts from the SSE stream until the connection closes."""
        headers = {**self._headers, "Accept": "text/event-stream"}
        try:
            async with self._session.get(
                self._url("/ajax/events/stream"),
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=None, sock_read=STREAM_READ_TIMEOUT),
            ) as resp:
                self._raise_for_status(resp)
                parser = SSEParser()
                async for raw_line in resp.content:
                    envelope = parser.feed(raw_line.decode("utf-8", "ignore"))
                    if envelope is not None:
                        yield envelope
        except aiohttp.ClientError as err:
            raise ApiError(str(err)) from err
        except TimeoutError as err:
            raise ApiError("Stream read timed out") from err
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_api.py -v`
Expected: 14 PASSED

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajaxsecurflow/api.py tests/test_api.py
git commit -m "feat: add AjaxSecurFlow API client and SSE parser"
```

---

### Task 3: Data model and `apply_event`

**Files:**
- Create: `custom_components/ajaxsecurflow/models.py`
- Create: `custom_components/ajaxsecurflow/events.py`
- Test: `tests/test_events.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_events.py
import copy
from custom_components.ajaxsecurflow.events import apply_event
from custom_components.ajaxsecurflow.models import HubData


def _data():
    return {
        "HUB1": HubData(
            hub={"id": "HUB1", "name": "Casa", "state": "DISARMED", "online": True},
            groups={"G1": {"id": "G1", "name": "Planta baja", "state": "DISARMED"}},
            devices={
                "D1": {"id": "D1", "name": "Puerta", "deviceType": "DoorProtect", "reed_closed": True,
                       "extra_contact_aware": True, "extra_contact_closed": True, "online": True, "malfunctions": []},
                "D2": {"id": "D2", "name": "Salón", "deviceType": "MotionProtect", "motion_detected": False, "online": True},
            },
        )
    }


def _env(hub_id="HUB1", event_type="SECURITY", tag="", transition="TRIGGERED", source_id="", source_type="DEVICE", ts="2026-09-18T10:00:00+00:00"):
    return {
        "id": "1", "hub_id": hub_id, "event_type": event_type, "title": "t", "description": "d",
        "severity": "info", "timestamp": ts, "media_urls": [], "source": "sqs",
        "data": {"event": {"eventTag": tag, "transition": transition, "sourceObjectId": source_id,
                           "sourceObjectType": source_type, "hubId": hub_id}},
    }


def test_unknown_hub_returns_false_and_leaves_data():
    data = _data()
    before = copy.deepcopy(data["HUB1"].hub)
    assert apply_event(data, _env(hub_id="NOPE")) is False
    assert data["HUB1"].hub == before


def test_arm_updates_hub_state():
    data = _data()
    assert apply_event(data, _env(tag="Arm")) is True
    assert data["HUB1"].hub["state"] == "ARMED"


def test_disarm_clears_triggered():
    data = _data()
    data["HUB1"].triggered = True
    apply_event(data, _env(tag="Disarm"))
    assert data["HUB1"].hub["state"] == "DISARMED"
    assert data["HUB1"].triggered is False


def test_night_mode_on():
    data = _data()
    apply_event(data, _env(tag="NightModeOn"))
    assert data["HUB1"].hub["state"] == "NIGHT_MODE"


def test_group_arm_updates_group_not_hub():
    data = _data()
    apply_event(data, _env(tag="Arm", source_id="G1", source_type="GROUP"))
    assert data["HUB1"].groups["G1"]["state"] == "ARMED"
    assert data["HUB1"].hub["state"] == "DISARMED"


def test_alarm_sets_triggered():
    data = _data()
    apply_event(data, _env(event_type="ALARM", tag="MotionDetected", source_id="D2"))
    assert data["HUB1"].triggered is True
    assert data["HUB1"].devices["D2"]["motion_detected"] is True


def test_motion_recovered_clears_flag():
    data = _data()
    data["HUB1"].devices["D2"]["motion_detected"] = True
    apply_event(data, _env(tag="MotionDetected", transition="RECOVERED", source_id="D2"))
    assert data["HUB1"].devices["D2"]["motion_detected"] is False


def test_ext_contact_opened_and_recovered():
    data = _data()
    apply_event(data, _env(tag="ExtContactOpened", source_id="D1"))
    assert data["HUB1"].devices["D1"]["extra_contact_closed"] is False
    apply_event(data, _env(tag="ExtContactOpened", transition="RECOVERED", source_id="D1"))
    assert data["HUB1"].devices["D1"]["extra_contact_closed"] is True


def test_reed_opened_updates_reed_closed():
    data = _data()
    apply_event(data, _env(tag="Opened", source_id="D1"))
    assert data["HUB1"].devices["D1"]["reed_closed"] is False


def test_tamper_and_offline():
    data = _data()
    apply_event(data, _env(tag="TamperOpened", source_id="D1"))
    assert data["HUB1"].devices["D1"]["tampered"] is True
    apply_event(data, _env(tag="Offline", source_id="D1"))
    assert data["HUB1"].devices["D1"]["online"] is False
    apply_event(data, _env(tag="Offline", transition="RECOVERED", source_id="D1"))
    assert data["HUB1"].devices["D1"]["online"] is True


def test_malfunction_added_and_recovered():
    data = _data()
    apply_event(data, _env(event_type="MALFUNCTION", tag="BatteryLow", source_id="D1"))
    assert data["HUB1"].devices["D1"]["malfunctions"] == ["BatteryLow"]
    apply_event(data, _env(event_type="FUNCTION_RECOVERED", tag="BatteryLow", transition="RECOVERED", source_id="D1"))
    assert data["HUB1"].devices["D1"]["malfunctions"] == []


def test_unknown_device_only_records_last_event():
    data = _data()
    assert apply_event(data, _env(tag="MotionDetected", source_id="NOPE")) is True
    assert data["HUB1"].last_event["tag"] == "MotionDetected"


def test_idempotent_on_duplicate():
    data = _data()
    env = _env(event_type="ALARM", tag="MotionDetected", source_id="D2")
    apply_event(data, env)
    snapshot = copy.deepcopy(data["HUB1"])
    apply_event(data, env)
    assert data["HUB1"] == snapshot
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_events.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the model**

```python
# custom_components/ajaxsecurflow/models.py
"""In-memory state shared by the coordinator, the SSE listener and the entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HubData:
    """Everything known about one hub. Dict payloads are the backend's JSON as-is."""

    hub: dict[str, Any]
    groups: dict[str, dict[str, Any]] = field(default_factory=dict)
    devices: dict[str, dict[str, Any]] = field(default_factory=dict)
    triggered: bool = False
    last_event: dict[str, Any] | None = None
```

- [ ] **Step 4: Write `apply_event`**

```python
# custom_components/ajaxsecurflow/events.py
"""Pure functions that fold an SSE hybrid envelope into HubData. No I/O."""
from __future__ import annotations

from typing import Any

from .const import (
    ARM_TAGS, DISARM_TAGS, EXT_CONTACT_TAGS, GLASS_TAGS, LEAK_TAGS, MOTION_TAGS,
    NIGHT_OFF_TAGS, NIGHT_ON_TAGS, OFFLINE_TAGS, OPENING_TAGS, SMOKE_TAGS,
)
from .models import HubData


def _arming_state(tag: str, event_type: str) -> str | None:
    if tag in ARM_TAGS or event_type in ("ARM", "ARMED"):
        return "ARMED"
    if tag in DISARM_TAGS or event_type in ("DISARM", "DISARMED"):
        return "DISARMED"
    if tag in NIGHT_ON_TAGS:
        return "NIGHT_MODE"
    if tag in NIGHT_OFF_TAGS:
        return "DISARMED"
    return None


def _apply_device(device: dict[str, Any], tag: str, raw_tag: str, event_type: str, recovered: bool) -> None:
    if tag in EXT_CONTACT_TAGS:
        device["extra_contact_closed"] = recovered
    elif tag in OPENING_TAGS:
        device["reed_closed"] = recovered
    elif tag in MOTION_TAGS:
        device["motion_detected"] = not recovered
    elif tag in GLASS_TAGS:
        device["glass_break_detected"] = not recovered
    elif tag in LEAK_TAGS:
        device["leak_detected"] = not recovered
    elif tag in SMOKE_TAGS:
        device["smoke_alarm_detected"] = not recovered
    elif "tamper" in tag:
        device["tampered"] = not recovered
    elif tag in OFFLINE_TAGS:
        device["online"] = recovered
    elif event_type == "MALFUNCTION" and raw_tag:
        malfunctions = list(device.get("malfunctions") or [])
        if raw_tag not in malfunctions:
            malfunctions.append(raw_tag)
        device["malfunctions"] = malfunctions
    elif event_type == "FUNCTION_RECOVERED" and raw_tag:
        device["malfunctions"] = [m for m in (device.get("malfunctions") or []) if m != raw_tag]


def apply_event(data: dict[str, HubData], envelope: dict[str, Any]) -> bool:
    """Mutate `data` with one envelope. Returns False when the hub is unknown (caller should refresh)."""
    hub_id = str(envelope.get("hub_id") or "")
    hub_data = data.get(hub_id)
    if hub_data is None:
        return False

    event = ((envelope.get("data") or {}).get("event")) or {}
    event_type = str(envelope.get("event_type") or "").upper()
    raw_tag = str(event.get("eventTag") or "")
    tag = raw_tag.lower()
    recovered = str(event.get("transition") or "").upper() == "RECOVERED"
    source_id = str(event.get("sourceObjectId") or "")
    source_type = str(event.get("sourceObjectType") or "").upper()

    hub_data.last_event = {
        "event_type": event_type,
        "tag": raw_tag,
        "timestamp": envelope.get("timestamp"),
        "description": envelope.get("description"),
        "severity": envelope.get("severity"),
    }

    new_state = _arming_state(tag, event_type)
    if new_state is not None:
        if source_type == "GROUP" and source_id in hub_data.groups:
            hub_data.groups[source_id]["state"] = new_state
        else:
            hub_data.hub["state"] = new_state
        if new_state == "DISARMED":
            hub_data.triggered = False
        return True

    if event_type == "ALARM":
        hub_data.triggered = True

    device = hub_data.devices.get(source_id)
    if device is not None:
        _apply_device(device, tag, raw_tag, event_type, recovered)
    return True
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_events.py -v`
Expected: 13 PASSED

- [ ] **Step 6: Commit**

```bash
git add custom_components/ajaxsecurflow/models.py custom_components/ajaxsecurflow/events.py tests/test_events.py
git commit -m "feat: add HubData model and apply_event state folding"
```

---

### Task 4: Coordinator

**Files:**
- Create: `custom_components/ajaxsecurflow/coordinator.py`
- Test: `tests/test_coordinator.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_coordinator.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ajaxsecurflow.api import ApiError, AuthError, RateLimitError
from custom_components.ajaxsecurflow.const import CONF_BASE_URL, CONF_SCAN_INTERVAL, CONF_TOKEN, DOMAIN
from custom_components.ajaxsecurflow.coordinator import AjaxSecurFlowCoordinator

HUBS = [{"id": "HUB1", "name": "Casa", "role": "MASTER"}]
HUB = {"id": "HUB1", "state": "ARMED", "online": True, "groups_enabled": True}
DEVICES = [{"id": "D1", "name": "Puerta", "reed_closed": True}]
GROUPS = [{"id": "G1", "name": "Planta baja", "state": "ARMED"}]


def _client(**overrides):
    client = MagicMock()
    client.get_hubs = AsyncMock(return_value=HUBS)
    client.get_hub = AsyncMock(return_value=HUB)
    client.get_devices = AsyncMock(return_value=DEVICES)
    client.get_groups = AsyncMock(return_value=GROUPS)
    for name, value in overrides.items():
        setattr(client, name, value)
    return client


def _entry(hass, options=None):
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_BASE_URL: "https://api.test", CONF_TOKEN: "asf_x"}, options=options or {})
    entry.add_to_hass(hass)
    return entry


async def test_update_builds_hub_data(hass):
    coordinator = AjaxSecurFlowCoordinator(hass, _entry(hass), _client())
    data = await coordinator._async_update_data()
    hub = data["HUB1"]
    assert hub.hub["name"] == "Casa"          # merged from list
    assert hub.hub["state"] == "ARMED"        # from detail
    assert hub.devices["D1"]["reed_closed"] is True
    assert hub.groups["G1"]["name"] == "Planta baja"
    assert hub.triggered is False


async def test_scan_interval_from_options(hass):
    coordinator = AjaxSecurFlowCoordinator(hass, _entry(hass, {CONF_SCAN_INTERVAL: 120}), _client())
    assert coordinator.update_interval.total_seconds() == 120


async def test_auth_error_raises_reauth(hass):
    coordinator = AjaxSecurFlowCoordinator(hass, _entry(hass), _client(get_hubs=AsyncMock(side_effect=AuthError())))
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


@pytest.mark.parametrize("exc", [RateLimitError(), ApiError("boom")])
async def test_transport_errors_raise_update_failed(hass, exc):
    coordinator = AjaxSecurFlowCoordinator(hass, _entry(hass), _client(get_hubs=AsyncMock(side_effect=exc)))
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_triggered_persists_until_disarmed(hass):
    coordinator = AjaxSecurFlowCoordinator(hass, _entry(hass), _client())
    coordinator.data = await coordinator._async_update_data()
    coordinator.data["HUB1"].triggered = True

    data = await coordinator._async_update_data()
    assert data["HUB1"].triggered is True  # hub still ARMED

    coordinator.client.get_hub = AsyncMock(return_value={**HUB, "state": "DISARMED"})
    coordinator.data = data
    data = await coordinator._async_update_data()
    assert data["HUB1"].triggered is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_coordinator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the coordinator**

```python
# custom_components/ajaxsecurflow/coordinator.py
"""Polling coordinator: hubs → (hub detail, devices, groups) per hub."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AjaxSecurFlowClient, ApiError, AuthError, PlanError, RateLimitError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import HubData

_LOGGER = logging.getLogger(__name__)


class AjaxSecurFlowCoordinator(DataUpdateCoordinator[dict[str, HubData]]):
    """Fetches the full state of every hub on a fixed interval."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: AjaxSecurFlowClient) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, HubData]:
        try:
            hubs = await self.client.get_hubs()
            loaded = await asyncio.gather(*(self._load_hub(summary) for summary in hubs))
        except AuthError as err:
            raise ConfigEntryAuthFailed("Integration token rejected") from err
        except (RateLimitError, ApiError, PlanError) as err:
            raise UpdateFailed(f"AjaxSecurFlow API error: {err}") from err

        previous = self.data or {}
        data: dict[str, HubData] = {}
        for hub_data in loaded:
            hub_id = hub_data.hub["id"]
            prev = previous.get(hub_id)
            if prev is not None:
                hub_data.last_event = prev.last_event
                still_armed = not str(hub_data.hub.get("state") or "").upper().startswith("DISARMED")
                hub_data.triggered = prev.triggered and still_armed
            data[hub_id] = hub_data
        return data

    async def _load_hub(self, summary: dict[str, Any]) -> HubData:
        hub_id = str(summary["id"])
        detail, devices, groups = await asyncio.gather(
            self.client.get_hub(hub_id),
            self.client.get_devices(hub_id),
            self.client.get_groups(hub_id),
        )
        return HubData(
            hub={**summary, **detail},
            groups={str(g["id"]): g for g in groups},
            devices={str(d["id"]): d for d in devices},
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_coordinator.py -v`
Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajaxsecurflow/coordinator.py tests/test_coordinator.py
git commit -m "feat: add polling coordinator"
```

---

### Task 5: SSE listener

**Files:**
- Create: `custom_components/ajaxsecurflow/sse.py`
- Test: `tests/test_sse.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_sse.py
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.ajaxsecurflow.api import AuthError, PlanError
from custom_components.ajaxsecurflow.const import EVENT_NAME
from custom_components.ajaxsecurflow.models import HubData
from custom_components.ajaxsecurflow.sse import SSEListener


def _coordinator():
    coordinator = MagicMock()
    coordinator.data = {"HUB1": HubData(hub={"id": "HUB1", "state": "DISARMED"}, devices={"D1": {"id": "D1", "motion_detected": False}})}
    coordinator.async_set_updated_data = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def _stream_of(*envelopes, then=None):
    async def gen():
        for env in envelopes:
            yield env
        if then is not None:
            raise then
        await asyncio.Event().wait()  # keep the connection "open"
    return gen


async def _spin(n=10):
    for _ in range(n):
        await asyncio.sleep(0)


async def test_event_updates_state_and_fires_bus_event(hass):
    coordinator = _coordinator()
    client = MagicMock()
    envelope = {"hub_id": "HUB1", "event_type": "ALARM", "data": {"event": {"eventTag": "MotionDetected", "sourceObjectId": "D1", "transition": "TRIGGERED"}}}
    client.stream_events = _stream_of(envelope)
    captured = async_capture_events(hass, EVENT_NAME)

    listener = SSEListener(hass, coordinator, client)
    listener.start()
    await _spin()

    assert coordinator.data["HUB1"].devices["D1"]["motion_detected"] is True
    assert coordinator.data["HUB1"].triggered is True
    coordinator.async_set_updated_data.assert_called_once_with(coordinator.data)
    assert len(captured) == 1
    assert captured[0].data["hub_id"] == "HUB1"
    await listener.stop()


async def test_unknown_hub_requests_refresh(hass):
    coordinator = _coordinator()
    client = MagicMock()
    client.stream_events = _stream_of({"hub_id": "NEW", "event_type": "SECURITY", "data": {}})

    listener = SSEListener(hass, coordinator, client)
    listener.start()
    await _spin()

    coordinator.async_request_refresh.assert_awaited_once()
    coordinator.async_set_updated_data.assert_not_called()
    await listener.stop()


async def test_plan_error_stops_listener_without_retry(hass):
    coordinator = _coordinator()
    client = MagicMock()
    client.stream_events = _stream_of(then=PlanError())
    with patch("custom_components.ajaxsecurflow.sse.asyncio.sleep", AsyncMock()) as sleep:
        listener = SSEListener(hass, coordinator, client)
        listener.start()
        await _spin()
        assert listener.running is False
        sleep.assert_not_awaited()


async def test_auth_error_stops_listener(hass):
    coordinator = _coordinator()
    client = MagicMock()
    client.stream_events = _stream_of(then=AuthError())
    listener = SSEListener(hass, coordinator, client)
    listener.start()
    await _spin()
    assert listener.running is False


async def test_transport_error_backs_off_exponentially(hass):
    coordinator = _coordinator()
    client = MagicMock()
    attempts = 0

    async def failing():
        nonlocal attempts
        attempts += 1
        if attempts <= 3:
            raise ConnectionError("down")
        await asyncio.Event().wait()
        yield  # pragma: no cover

    client.stream_events = failing
    with patch("custom_components.ajaxsecurflow.sse.asyncio.sleep", AsyncMock()) as sleep:
        listener = SSEListener(hass, coordinator, client)
        listener.start()
        await _spin(30)
        delays = [call.args[0] for call in sleep.await_args_list]
        assert delays[:3] == [5, 10, 20]
        await listener.stop()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_sse.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the listener**

```python
# custom_components/ajaxsecurflow/sse.py
"""Background task that keeps an SSE connection open and folds events into the coordinator."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .api import AjaxSecurFlowClient, AuthError, PlanError
from .const import DOMAIN, EVENT_NAME, SSE_BACKOFF_MAX, SSE_BACKOFF_MIN
from .coordinator import AjaxSecurFlowCoordinator
from .events import apply_event

_LOGGER = logging.getLogger(__name__)


class SSEListener:
    """Consumes /ajax/events/stream with exponential backoff. Stops for good on 401/403."""

    def __init__(self, hass: HomeAssistant, coordinator: AjaxSecurFlowCoordinator, client: AjaxSecurFlowClient) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._client = client
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self) -> None:
        if self._task is None:
            self._task = self._hass.async_create_background_task(self._run(), name=f"{DOMAIN}_sse")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        delay = SSE_BACKOFF_MIN
        while True:
            try:
                async for envelope in self._client.stream_events():
                    delay = SSE_BACKOFF_MIN
                    self._handle(envelope)
                _LOGGER.debug("SSE stream closed by server; reconnecting")
            except asyncio.CancelledError:
                raise
            except PlanError:
                _LOGGER.info("Real-time stream not included in your plan; using polling only")
                return
            except AuthError:
                _LOGGER.warning("Integration token rejected by the stream; polling will trigger re-authentication")
                return
            except Exception as err:  # noqa: BLE001 - keep the loop alive on any transport error
                _LOGGER.debug("SSE connection error: %s", err)
            await asyncio.sleep(delay)
            delay = min(delay * 2, SSE_BACKOFF_MAX)

    def _handle(self, envelope: dict[str, Any]) -> None:
        data = self._coordinator.data
        if data is None:
            return
        if not apply_event(data, envelope):
            _LOGGER.debug("Event for unknown hub %s; scheduling full refresh", envelope.get("hub_id"))
            self._hass.async_create_task(self._coordinator.async_request_refresh())
            return
        self._coordinator.async_set_updated_data(data)
        self._hass.bus.async_fire(EVENT_NAME, envelope)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_sse.py -v`
Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajaxsecurflow/sse.py tests/test_sse.py
git commit -m "feat: add SSE listener with backoff"
```

---

### Task 6: Config flow, strings and translations

**Files:**
- Create: `custom_components/ajaxsecurflow/config_flow.py`
- Create: `custom_components/ajaxsecurflow/strings.json`
- Create: `custom_components/ajaxsecurflow/translations/en.json`, `translations/es.json`
- Test: `tests/test_config_flow.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config_flow.py
from unittest.mock import AsyncMock, patch

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ajaxsecurflow.api import AjaxSecurFlowClient, ApiError, AuthError
from custom_components.ajaxsecurflow.const import (
    CONF_BASE_URL, CONF_SCAN_INTERVAL, CONF_TOKEN, DEFAULT_BASE_URL, DOMAIN,
)

ME_PRO = {"id": 1, "email": "User@Example.com", "subscription_plan": "pro"}
USER_INPUT = {CONF_BASE_URL: "https://api.test/", CONF_TOKEN: "asf_abc"}


def _patch_me(result):
    return patch.object(AjaxSecurFlowClient, "get_me", AsyncMock(**result))


async def _start(hass):
    return await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})


async def test_form_defaults_base_url(hass):
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    schema_defaults = {
        k.schema: k.default()
        for k in result["data_schema"].schema
        if isinstance(k, vol.Marker) and k.default is not vol.UNDEFINED
    }
    assert schema_defaults[CONF_BASE_URL] == DEFAULT_BASE_URL


async def test_user_flow_creates_entry(hass):
    result = await _start(hass)
    with _patch_me({"return_value": ME_PRO}), patch("custom_components.ajaxsecurflow.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "User@Example.com"
    assert result["data"] == {CONF_BASE_URL: "https://api.test", CONF_TOKEN: "asf_abc"}
    assert result["result"].unique_id == "user@example.com"


async def test_basic_plan_creates_entry_with_no_control_notice(hass):
    result = await _start(hass)
    with _patch_me({"return_value": {**ME_PRO, "subscription_plan": "basic"}}), patch("custom_components.ajaxsecurflow.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["description"] == "no_control"


async def test_free_plan_shows_error(hass):
    result = await _start(hass)
    with _patch_me({"return_value": {**ME_PRO, "subscription_plan": "free"}}):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "plan_free"}


async def test_invalid_auth(hass):
    result = await _start(hass)
    with _patch_me({"side_effect": AuthError()}):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "invalid_auth"}


async def test_cannot_connect(hass):
    result = await _start(hass)
    with _patch_me({"side_effect": ApiError("down")}):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "cannot_connect"}


async def test_duplicate_account_aborts(hass):
    MockConfigEntry(domain=DOMAIN, data=USER_INPUT, unique_id="user@example.com").add_to_hass(hass)
    result = await _start(hass)
    with _patch_me({"return_value": ME_PRO}):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_updates_token(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_BASE_URL: "https://api.test", CONF_TOKEN: "asf_old"}, unique_id="user@example.com")
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    with _patch_me({"return_value": ME_PRO}), patch("custom_components.ajaxsecurflow.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_TOKEN: "asf_new"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_TOKEN] == "asf_new"


async def test_options_flow_sets_scan_interval(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_BASE_URL: "https://api.test", CONF_TOKEN: "asf_x"}, unique_id="u")
    entry.add_to_hass(hass)
    with patch("custom_components.ajaxsecurflow.async_setup_entry", return_value=True):
        await hass.config_entries.async_setup(entry.entry_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {CONF_SCAN_INTERVAL: 120})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL] == 120
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: FAIL (no config flow registered / `async_setup_entry` missing)

- [ ] **Step 3: Write the config flow**

```python
# custom_components/ajaxsecurflow/config_flow.py
"""Config, reauth and options flows."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AjaxSecurFlowClient, AjaxSecurFlowError, AuthError
from .const import (
    CONF_BASE_URL, CONF_SCAN_INTERVAL, CONF_TOKEN, DEFAULT_BASE_URL, DEFAULT_SCAN_INTERVAL,
    DOMAIN, MAX_SCAN_INTERVAL, MIN_SCAN_INTERVAL, PLANS_WITH_CONTROL, PLANS_WITH_DEVICES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema({
    vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    vol.Required(CONF_TOKEN): str,
})
STEP_REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_TOKEN): str})


async def _fetch_me(hass: HomeAssistant, base_url: str, token: str) -> dict[str, Any]:
    client = AjaxSecurFlowClient(async_get_clientsession(hass), base_url, token)
    return await client.get_me()


def _plan_of(me: dict[str, Any]) -> str:
    return str(me.get("subscription_plan") or "free").lower()


class AjaxSecurFlowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Token-based setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].strip().rstrip("/")
            token = user_input[CONF_TOKEN].strip()
            try:
                me = await _fetch_me(self.hass, base_url, token)
            except AuthError:
                errors["base"] = "invalid_auth"
            except AjaxSecurFlowError:
                errors["base"] = "cannot_connect"
            else:
                plan = _plan_of(me)
                if plan not in PLANS_WITH_DEVICES:
                    errors["base"] = "plan_free"
                else:
                    email = str(me["email"])
                    await self.async_set_unique_id(email.lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=email,
                        data={CONF_BASE_URL: base_url, CONF_TOKEN: token},
                        description=None if plan in PLANS_WITH_CONTROL else "no_control",
                    )
        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            try:
                await _fetch_me(self.hass, entry.data[CONF_BASE_URL], token)
            except AuthError:
                errors["base"] = "invalid_auth"
            except AjaxSecurFlowError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_TOKEN: token})
        return self.async_show_form(step_id="reauth_confirm", data_schema=STEP_REAUTH_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> AjaxSecurFlowOptionsFlow:
        return AjaxSecurFlowOptionsFlow()


class AjaxSecurFlowOptionsFlow(OptionsFlow):
    """Polling interval."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
            ),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
```

- [ ] **Step 4: Write `strings.json`**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Connect to AjaxSecurFlow",
        "description": "Create an integration token in the AjaxSecurFlow dashboard (Profile → Integraciones) and paste it here.",
        "data": {
          "base_url": "API base URL",
          "token": "Integration token"
        }
      },
      "reauth_confirm": {
        "title": "Token no longer valid",
        "description": "Paste a new integration token from the AjaxSecurFlow dashboard.",
        "data": {
          "token": "Integration token"
        }
      }
    },
    "error": {
      "cannot_connect": "Could not reach the AjaxSecurFlow API.",
      "invalid_auth": "The token was rejected. Check it or create a new one.",
      "plan_free": "The Free plan does not include device access. Upgrade to Basic or higher."
    },
    "abort": {
      "already_configured": "This account is already configured.",
      "reauth_successful": "Token updated."
    },
    "create_entry": {
      "default": "Connected.",
      "no_control": "Connected. Your Basic plan allows monitoring only; arm/disarm needs Pro or higher."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "AjaxSecurFlow options",
        "data": {
          "scan_interval": "Polling interval (seconds)"
        }
      }
    }
  },
  "entity": {
    "alarm_control_panel": {
      "group": { "name": "{group}" }
    },
    "binary_sensor": {
      "opening": { "name": "Opening" },
      "extra_contact": { "name": "External contact" },
      "motion": { "name": "Motion" },
      "glass_break": { "name": "Glass break" },
      "moisture": { "name": "Leak" },
      "smoke": { "name": "Smoke" },
      "connectivity": { "name": "Online" },
      "tamper": { "name": "Tamper" },
      "problem": { "name": "Problem" },
      "power": { "name": "External power" }
    },
    "sensor": {
      "battery": { "name": "Battery" },
      "signal_level": {
        "name": "Signal",
        "state": { "no_signal": "No signal", "weak": "Weak", "normal": "Normal", "strong": "Strong" }
      },
      "temperature": { "name": "Temperature" },
      "humidity": { "name": "Humidity" },
      "co2": { "name": "CO2" },
      "gsm_signal": {
        "name": "GSM signal",
        "state": { "no_signal": "No signal", "weak": "Weak", "normal": "Normal", "strong": "Strong" }
      },
      "firmware_version": { "name": "Firmware" },
      "last_event": { "name": "Last event" }
    }
  },
  "exceptions": {
    "plan_required": { "message": "Arming commands require a Pro or Premium AjaxSecurFlow plan." },
    "command_failed": { "message": "AjaxSecurFlow rejected the command: {error}" }
  }
}
```

- [ ] **Step 5: Write translations**

`translations/en.json`: identical content to `strings.json` (copy the file).

`translations/es.json`:
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Conectar con AjaxSecurFlow",
        "description": "Crea un token de integración en el panel de AjaxSecurFlow (Perfil → Integraciones) y pégalo aquí.",
        "data": {
          "base_url": "URL base de la API",
          "token": "Token de integración"
        }
      },
      "reauth_confirm": {
        "title": "El token ya no es válido",
        "description": "Pega un token de integración nuevo desde el panel de AjaxSecurFlow.",
        "data": {
          "token": "Token de integración"
        }
      }
    },
    "error": {
      "cannot_connect": "No se pudo conectar con la API de AjaxSecurFlow.",
      "invalid_auth": "El token ha sido rechazado. Revísalo o crea uno nuevo.",
      "plan_free": "El plan Free no incluye acceso a dispositivos. Necesitas Basic o superior."
    },
    "abort": {
      "already_configured": "Esta cuenta ya está configurada.",
      "reauth_successful": "Token actualizado."
    },
    "create_entry": {
      "default": "Conectado.",
      "no_control": "Conectado. Tu plan Basic solo permite monitorizar; armar/desarmar requiere Pro o superior."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Opciones de AjaxSecurFlow",
        "data": {
          "scan_interval": "Intervalo de sondeo (segundos)"
        }
      }
    }
  },
  "entity": {
    "alarm_control_panel": {
      "group": { "name": "{group}" }
    },
    "binary_sensor": {
      "opening": { "name": "Apertura" },
      "extra_contact": { "name": "Contacto externo" },
      "motion": { "name": "Movimiento" },
      "glass_break": { "name": "Rotura de cristal" },
      "moisture": { "name": "Fuga" },
      "smoke": { "name": "Humo" },
      "connectivity": { "name": "En línea" },
      "tamper": { "name": "Sabotaje" },
      "problem": { "name": "Problema" },
      "power": { "name": "Alimentación externa" }
    },
    "sensor": {
      "battery": { "name": "Batería" },
      "signal_level": {
        "name": "Señal",
        "state": { "no_signal": "Sin señal", "weak": "Débil", "normal": "Normal", "strong": "Fuerte" }
      },
      "temperature": { "name": "Temperatura" },
      "humidity": { "name": "Humedad" },
      "co2": { "name": "CO2" },
      "gsm_signal": {
        "name": "Señal GSM",
        "state": { "no_signal": "Sin señal", "weak": "Débil", "normal": "Normal", "strong": "Fuerte" }
      },
      "firmware_version": { "name": "Firmware" },
      "last_event": { "name": "Último evento" }
    }
  },
  "exceptions": {
    "plan_required": { "message": "Los comandos de armado requieren un plan Pro o Premium de AjaxSecurFlow." },
    "command_failed": { "message": "AjaxSecurFlow rechazó el comando: {error}" }
  }
}
```

- [ ] **Step 6: Temporary `async_setup_entry` so the flow can register**

The tests patch `custom_components.ajaxsecurflow.async_setup_entry`, which must exist. Replace `__init__.py` with this stub (fully implemented in Task 8):

```python
"""AjaxSecurFlow integration for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: 9 PASSED

- [ ] **Step 8: Commit**

```bash
git add custom_components/ajaxsecurflow/config_flow.py custom_components/ajaxsecurflow/strings.json custom_components/ajaxsecurflow/translations custom_components/ajaxsecurflow/__init__.py tests/test_config_flow.py
git commit -m "feat: add config, reauth and options flows with translations"
```

---

### Task 7: Base entities

**Files:**
- Create: `custom_components/ajaxsecurflow/entity.py`

No standalone test: behaviour is covered by the platform tests in Tasks 9-11.

- [ ] **Step 1: Write the base entities**

```python
# custom_components/ajaxsecurflow/entity.py
"""Base entities carrying device_info for hubs and Ajax devices."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AjaxSecurFlowCoordinator
from .models import HubData

MANUFACTURER = "Ajax Systems"


class AjaxSecurFlowHubEntity(CoordinatorEntity[AjaxSecurFlowCoordinator]):
    """Entity attached to a hub device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AjaxSecurFlowCoordinator, hub_id: str) -> None:
        super().__init__(coordinator)
        self.hub_id = hub_id
        hub = self.hub_data.hub
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, hub_id)},
            name=hub.get("name") or f"Hub {hub_id}",
            manufacturer=MANUFACTURER,
            model=hub.get("hub_subtype") or "Hub",
            sw_version=(hub.get("firmware") or {}).get("version"),
        )

    @property
    def hub_data(self) -> HubData:
        return self.coordinator.data[self.hub_id]

    @property
    def available(self) -> bool:
        return super().available and self.hub_id in (self.coordinator.data or {})


class AjaxSecurFlowDeviceEntity(AjaxSecurFlowHubEntity):
    """Entity attached to an Ajax device (child of the hub device)."""

    def __init__(self, coordinator: AjaxSecurFlowCoordinator, hub_id: str, device_id: str, rooms: dict[str, str]) -> None:
        super().__init__(coordinator, hub_id)
        self.device_id = device_id
        device = self.device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{hub_id}:{device_id}")},
            name=device.get("name") or device_id,
            manufacturer=MANUFACTURER,
            model=device.get("deviceType"),
            via_device=(DOMAIN, hub_id),
            suggested_area=rooms.get(f"{hub_id}:{device.get('roomId')}"),
        )

    @property
    def device(self) -> dict[str, Any]:
        return self.hub_data.devices[self.device_id]

    @property
    def available(self) -> bool:
        return super().available and self.device_id in self.hub_data.devices
```

- [ ] **Step 2: Import check**

Run: `python -c "import custom_components.ajaxsecurflow.entity"`
Expected: no output, exit 0

- [ ] **Step 3: Commit**

```bash
git add custom_components/ajaxsecurflow/entity.py
git commit -m "feat: add base hub/device entities"
```

---

### Task 8: Integration setup and shared test fixtures

**Files:**
- Modify: `custom_components/ajaxsecurflow/__init__.py`
- Modify: `tests/conftest.py`
- Test: `tests/test_init.py`

- [ ] **Step 1: Extend the fixtures**

Replace `tests/conftest.py` with:

```python
"""Shared fixtures: a fully mocked API client and a configured entry."""
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ajaxsecurflow.api import AjaxSecurFlowClient, PlanError
from custom_components.ajaxsecurflow.const import CONF_BASE_URL, CONF_TOKEN, DOMAIN

ME = {"id": 1, "email": "user@example.com", "subscription_plan": "pro"}
HUBS = [{"id": "HUB1", "name": "Casa", "role": "MASTER"}]
HUB = {
    "id": "HUB1", "name": "Casa", "online": True, "state": "DISARMED", "hub_subtype": "HUB_2_PLUS",
    "groups_enabled": True, "tampered": False, "externallyPowered": True,
    "firmware": {"version": "2.20.1"}, "battery": {"chargeLevelPercentage": 100, "state": "OK"},
    "gsm": {"signalLevel": "STRONG"},
}
DEVICE_DOOR = {
    "id": "D1", "hubId": "HUB1", "name": "Puerta principal", "deviceType": "DoorProtect", "roomId": "1",
    "online": True, "battery_level": 88, "signal_level": "STRONG", "temperature": 21.5, "tampered": False,
    "malfunctions": [], "reed_closed": True, "extra_contact_aware": True, "extra_contact_closed": True,
}
DEVICE_MOTION = {
    "id": "D2", "hubId": "HUB1", "name": "Salón", "deviceType": "MotionProtect", "roomId": "1",
    "online": True, "battery_level": 100, "signal_level": "NORMAL", "motion_detected": False,
    "malfunctions": ["BATTERY_MALFUNCTION"],
}
DEVICES = [DEVICE_DOOR, DEVICE_MOTION]
GROUPS = [{"id": "G1", "hub_id": "HUB1", "name": "Planta baja", "state": "DISARMED"}]
ROOMS = [{"id": "1", "roomName": "Salón"}]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def _no_stream(self):
    raise PlanError("no stream in tests")
    yield  # pragma: no cover


@pytest.fixture
def mock_api():
    """Patch every client method. `stream_events` ends immediately so no background task lingers."""
    mocks = SimpleNamespace(
        get_me=AsyncMock(return_value=ME),
        get_hubs=AsyncMock(return_value=HUBS),
        get_hub=AsyncMock(return_value=HUB),
        get_devices=AsyncMock(return_value=DEVICES),
        get_groups=AsyncMock(return_value=GROUPS),
        get_rooms=AsyncMock(return_value=ROOMS),
        set_arm_state=AsyncMock(return_value={"success": True}),
    )
    with ExitStack() as stack:
        for name, mock in vars(mocks).items():
            stack.enter_context(patch.object(AjaxSecurFlowClient, name, mock))
        stack.enter_context(patch.object(AjaxSecurFlowClient, "stream_events", _no_stream))
        yield mocks


@pytest.fixture
def config_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="user@example.com",
        data={CONF_BASE_URL: "https://api.test", CONF_TOKEN: "asf_test"},
        unique_id="user@example.com",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def init_integration(hass, mock_api, config_entry):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_init.py
from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr

from custom_components.ajaxsecurflow.api import ApiError, AuthError
from custom_components.ajaxsecurflow.const import DOMAIN


async def test_setup_and_unload(hass, init_integration):
    entry = init_integration
    assert entry.state is ConfigEntryState.LOADED
    rt = entry.runtime_data
    assert rt.plan == "pro"
    assert rt.rooms == {"HUB1:1": "Salón"}
    assert "HUB1" in rt.coordinator.data

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_devices_registered_with_via_device(hass, init_integration):
    registry = dr.async_get(hass)
    hub = registry.async_get_device(identifiers={(DOMAIN, "HUB1")})
    door = registry.async_get_device(identifiers={(DOMAIN, "HUB1:D1")})
    assert hub is not None and hub.manufacturer == "Ajax Systems" and hub.model == "HUB_2_PLUS"
    assert door is not None and door.via_device_id == hub.id and door.model == "DoorProtect"


async def test_auth_error_on_setup_triggers_reauth(hass, mock_api, config_entry):
    mock_api.get_me.side_effect = AuthError()
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert flows and flows[0]["context"]["source"] == "reauth"


async def test_api_error_on_setup_retries(hass, mock_api, config_entry):
    mock_api.get_me.side_effect = ApiError("down")
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_rooms_failure_is_not_fatal(hass, mock_api, config_entry):
    mock_api.get_rooms.side_effect = ApiError("rooms down")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.runtime_data.rooms == {}
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_init.py -v`
Expected: FAIL (`runtime_data` missing, no devices registered)

- [ ] **Step 4: Write `__init__.py`**

```python
# custom_components/ajaxsecurflow/__init__.py
"""AjaxSecurFlow integration for Home Assistant."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AjaxSecurFlowClient, AjaxSecurFlowError, AuthError
from .const import CONF_BASE_URL, CONF_TOKEN
from .coordinator import AjaxSecurFlowCoordinator
from .models import HubData
from .sse import SSEListener

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL, Platform.BINARY_SENSOR, Platform.SENSOR]


@dataclass
class AjaxSecurFlowRuntimeData:
    client: AjaxSecurFlowClient
    coordinator: AjaxSecurFlowCoordinator
    listener: SSEListener
    plan: str
    rooms: dict[str, str]  # "<hub_id>:<room_id>" -> room name


type AjaxSecurFlowConfigEntry = ConfigEntry[AjaxSecurFlowRuntimeData]


async def _load_room_names(client: AjaxSecurFlowClient, data: dict[str, HubData]) -> dict[str, str]:
    rooms: dict[str, str] = {}
    for hub_id in data:
        try:
            for room in await client.get_rooms(hub_id):
                rooms[f"{hub_id}:{room.get('id')}"] = str(room.get("roomName") or "")
        except AjaxSecurFlowError as err:
            _LOGGER.debug("Rooms unavailable for hub %s: %s", hub_id, err)
    return rooms


async def async_setup_entry(hass: HomeAssistant, entry: AjaxSecurFlowConfigEntry) -> bool:
    client = AjaxSecurFlowClient(async_get_clientsession(hass), entry.data[CONF_BASE_URL], entry.data[CONF_TOKEN])
    try:
        me = await client.get_me()
    except AuthError as err:
        raise ConfigEntryAuthFailed("Integration token rejected") from err
    except AjaxSecurFlowError as err:
        raise ConfigEntryNotReady(f"Cannot reach AjaxSecurFlow: {err}") from err

    plan = str(me.get("subscription_plan") or "free").lower()
    coordinator = AjaxSecurFlowCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    rooms = await _load_room_names(client, coordinator.data)

    listener = SSEListener(hass, coordinator, client)
    entry.runtime_data = AjaxSecurFlowRuntimeData(client, coordinator, listener, plan, rooms)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    listener.start()
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: AjaxSecurFlowConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: AjaxSecurFlowConfigEntry) -> bool:
    await entry.runtime_data.listener.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

- [ ] **Step 5: Add empty platform modules so forwarding succeeds**

Create `alarm_control_panel.py`, `binary_sensor.py`, `sensor.py` each with this placeholder (replaced in Tasks 9-11):

```python
"""Platform placeholder; implemented in a later task."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    return None
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_init.py tests/test_config_flow.py -v`
Expected: `test_devices_registered_with_via_device` FAILS (no entities yet, so no devices); all others PASS. That one test turns green in Task 10.

- [ ] **Step 7: Commit**

```bash
git add custom_components/ajaxsecurflow tests/conftest.py tests/test_init.py
git commit -m "feat: integration setup/unload with runtime data and room names"
```

---

### Task 9: Alarm control panel

**Files:**
- Modify: `custom_components/ajaxsecurflow/alarm_control_panel.py`
- Test: `tests/test_alarm_control_panel.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_alarm_control_panel.py
import pytest
from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN, AlarmControlPanelEntityFeature, AlarmControlPanelState,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.ajaxsecurflow.alarm_control_panel import map_state
from custom_components.ajaxsecurflow.api import PlanError
from custom_components.ajaxsecurflow.const import DOMAIN

from .conftest import ME


@pytest.mark.parametrize("raw,triggered,expected", [
    ("DISARMED", False, AlarmControlPanelState.DISARMED),
    ("ARMED", False, AlarmControlPanelState.ARMED_AWAY),
    ("NIGHT_MODE", False, AlarmControlPanelState.ARMED_NIGHT),
    ("ARMED_NIGHT_MODE_ON", False, AlarmControlPanelState.ARMED_NIGHT),
    ("ARMED_NIGHT_MODE_OFF", False, AlarmControlPanelState.ARMED_AWAY),
    ("DISARMED_NIGHT_MODE_ON", False, AlarmControlPanelState.ARMED_NIGHT),
    ("DISARMED_NIGHT_MODE_OFF", False, AlarmControlPanelState.DISARMED),
    ("PARTIALLY_ARMED_NIGHT_MODE_OFF", False, AlarmControlPanelState.ARMED_CUSTOM_BYPASS),
    ("ARMED", True, AlarmControlPanelState.TRIGGERED),
    (None, False, None),
    ("WEIRD", False, None),
])
def test_map_state(raw, triggered, expected):
    assert map_state(raw, triggered) == expected


def _eid(hass, unique_id):
    return er.async_get(hass).async_get_entity_id(ALARM_DOMAIN, DOMAIN, unique_id)


async def test_hub_and_group_panels_created(hass, init_integration):
    hub_eid = _eid(hass, "HUB1_panel")
    group_eid = _eid(hass, "HUB1_G1_panel")
    assert hub_eid and group_eid
    assert hass.states.get(hub_eid).state == AlarmControlPanelState.DISARMED
    assert hass.states.get(group_eid).state == AlarmControlPanelState.DISARMED
    features = hass.states.get(hub_eid).attributes["supported_features"]
    assert features == AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.ARM_NIGHT


async def test_no_group_panels_when_groups_disabled(hass, mock_api, config_entry):
    mock_api.get_hub.return_value = {**mock_api.get_hub.return_value, "groups_enabled": False}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert _eid(hass, "HUB1_panel")
    assert _eid(hass, "HUB1_G1_panel") is None


async def test_arm_away_sends_command(hass, init_integration, mock_api):
    await hass.services.async_call(ALARM_DOMAIN, "alarm_arm_away", {"entity_id": _eid(hass, "HUB1_panel")}, blocking=True)
    mock_api.set_arm_state.assert_awaited_once_with("HUB1", 1, None)


async def test_group_disarm_sends_group_id(hass, init_integration, mock_api):
    await hass.services.async_call(ALARM_DOMAIN, "alarm_disarm", {"entity_id": _eid(hass, "HUB1_G1_panel")}, blocking=True)
    mock_api.set_arm_state.assert_awaited_once_with("HUB1", 0, "G1")


async def test_arm_night_sends_command(hass, init_integration, mock_api):
    await hass.services.async_call(ALARM_DOMAIN, "alarm_arm_night", {"entity_id": _eid(hass, "HUB1_panel")}, blocking=True)
    mock_api.set_arm_state.assert_awaited_once_with("HUB1", 2, None)


async def test_plan_error_raises_translated_error(hass, init_integration, mock_api):
    mock_api.set_arm_state.side_effect = PlanError()
    with pytest.raises(HomeAssistantError) as excinfo:
        await hass.services.async_call(ALARM_DOMAIN, "alarm_arm_away", {"entity_id": _eid(hass, "HUB1_panel")}, blocking=True)
    assert excinfo.value.translation_key == "plan_required"


async def test_basic_plan_has_no_control_features(hass, mock_api, config_entry):
    mock_api.get_me.return_value = {**ME, "subscription_plan": "basic"}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(_eid(hass, "HUB1_panel")).attributes["supported_features"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_alarm_control_panel.py -v`
Expected: FAIL with `ImportError: cannot import name 'map_state'`

- [ ] **Step 3: Write the platform**

```python
# custom_components/ajaxsecurflow/alarm_control_panel.py
"""Alarm panels: one per hub, plus one per group when groups mode is enabled."""
from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity, AlarmControlPanelEntityFeature, AlarmControlPanelState,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AjaxSecurFlowConfigEntry
from .api import AjaxSecurFlowError, PlanError
from .const import ARM_STATE_ARM, ARM_STATE_DISARM, ARM_STATE_NIGHT, DOMAIN, PLANS_WITH_CONTROL
from .coordinator import AjaxSecurFlowCoordinator
from .entity import AjaxSecurFlowHubEntity

CONTROL_FEATURES = AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.ARM_NIGHT


def map_state(raw: str | None, triggered: bool) -> AlarmControlPanelState | None:
    """Ajax hub/group state string → HA alarm state."""
    if triggered:
        return AlarmControlPanelState.TRIGGERED
    if not raw:
        return None
    state = raw.upper()
    if state.startswith("PARTIALLY_ARMED"):
        return AlarmControlPanelState.ARMED_CUSTOM_BYPASS
    if state == "NIGHT_MODE" or state.endswith("NIGHT_MODE_ON"):
        return AlarmControlPanelState.ARMED_NIGHT
    if state.startswith("ARMED"):
        return AlarmControlPanelState.ARMED_AWAY
    if state.startswith("DISARMED"):
        return AlarmControlPanelState.DISARMED
    return None


async def async_setup_entry(hass: HomeAssistant, entry: AjaxSecurFlowConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    rt = entry.runtime_data
    control = rt.plan in PLANS_WITH_CONTROL
    entities: list[AjaxSecurFlowAlarmPanel] = []
    for hub_id, hub_data in rt.coordinator.data.items():
        entities.append(AjaxSecurFlowAlarmPanel(rt.coordinator, hub_id, None, control))
        if hub_data.hub.get("groups_enabled"):
            entities.extend(AjaxSecurFlowAlarmPanel(rt.coordinator, hub_id, group_id, control) for group_id in hub_data.groups)
    async_add_entities(entities)


class AjaxSecurFlowAlarmPanel(AjaxSecurFlowHubEntity, AlarmControlPanelEntity):
    _attr_code_arm_required = False
    _attr_code_format = None

    def __init__(self, coordinator: AjaxSecurFlowCoordinator, hub_id: str, group_id: str | None, control: bool) -> None:
        super().__init__(coordinator, hub_id)
        self.group_id = group_id
        self._attr_supported_features = CONTROL_FEATURES if control else AlarmControlPanelEntityFeature(0)
        if group_id is None:
            self._attr_unique_id = f"{hub_id}_panel"
            self._attr_name = None  # takes the hub device name
        else:
            self._attr_unique_id = f"{hub_id}_{group_id}_panel"
            self._attr_translation_key = "group"
            self._attr_translation_placeholders = {"group": self.hub_data.groups[group_id].get("name") or group_id}

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        return self.group_id is None or self.group_id in self.hub_data.groups

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        if self.group_id is None:
            return map_state(self.hub_data.hub.get("state"), self.hub_data.triggered)
        return map_state(self.hub_data.groups[self.group_id].get("state"), False)

    async def _send(self, arm_state: int) -> None:
        try:
            await self.coordinator.client.set_arm_state(self.hub_id, arm_state, self.group_id)
        except PlanError as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="plan_required") from err
        except AjaxSecurFlowError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="command_failed", translation_placeholders={"error": str(err)}
            ) from err
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._send(ARM_STATE_DISARM)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._send(ARM_STATE_ARM)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._send(ARM_STATE_NIGHT)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_alarm_control_panel.py -v`
Expected: 18 PASSED

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajaxsecurflow/alarm_control_panel.py tests/test_alarm_control_panel.py
git commit -m "feat: add hub and group alarm control panels"
```

---

### Task 10: Binary sensors

**Files:**
- Modify: `custom_components/ajaxsecurflow/binary_sensor.py`
- Test: `tests/test_binary_sensor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_binary_sensor.py
from homeassistant.components.binary_sensor import DOMAIN as BS_DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers import entity_registry as er

from custom_components.ajaxsecurflow.const import DOMAIN


def _state(hass, unique_id):
    eid = er.async_get(hass).async_get_entity_id(BS_DOMAIN, DOMAIN, unique_id)
    return hass.states.get(eid) if eid else None


async def test_door_sensors(hass, init_integration):
    assert _state(hass, "HUB1_D1_opening").state == STATE_OFF          # reed_closed True → not open
    assert _state(hass, "HUB1_D1_extra_contact").state == STATE_OFF
    assert _state(hass, "HUB1_D1_connectivity").state == STATE_ON
    assert _state(hass, "HUB1_D1_tamper").state == STATE_OFF
    assert _state(hass, "HUB1_D1_problem").state == STATE_OFF
    assert _state(hass, "HUB1_D1_motion") is None                       # DoorProtect reports no motion field


async def test_motion_sensor_and_problem_attribute(hass, init_integration):
    assert _state(hass, "HUB1_D2_motion").state == STATE_OFF
    assert _state(hass, "HUB1_D2_opening") is None
    problem = _state(hass, "HUB1_D2_problem")
    assert problem.state == STATE_ON
    assert problem.attributes["malfunctions"] == ["BATTERY_MALFUNCTION"]


async def test_hub_sensors(hass, init_integration):
    assert _state(hass, "HUB1_connectivity").state == STATE_ON
    assert _state(hass, "HUB1_tamper").state == STATE_OFF
    assert _state(hass, "HUB1_power").state == STATE_ON


async def test_extra_contact_not_created_when_unaware(hass, mock_api, config_entry):
    devices = mock_api.get_devices.return_value
    mock_api.get_devices.return_value = [{**devices[0], "extra_contact_aware": False}, devices[1]]
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert _state(hass, "HUB1_D1_extra_contact") is None


async def test_state_follows_coordinator_update(hass, init_integration):
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["HUB1"].devices["D1"]["reed_closed"] = False
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()
    assert _state(hass, "HUB1_D1_opening").state == STATE_ON
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_binary_sensor.py -v`
Expected: FAIL with `AttributeError: 'NoneType' object has no attribute 'state'`

- [ ] **Step 3: Write the platform**

```python
# custom_components/ajaxsecurflow/binary_sensor.py
"""Binary sensors for Ajax devices and hubs. An entity exists only when its source field is present."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AjaxSecurFlowConfigEntry
from .coordinator import AjaxSecurFlowCoordinator
from .entity import AjaxSecurFlowDeviceEntity, AjaxSecurFlowHubEntity


@dataclass(frozen=True, kw_only=True)
class AjaxBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None]
    exists_fn: Callable[[dict[str, Any]], bool]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _present(field: str) -> Callable[[dict[str, Any]], bool]:
    return lambda payload: payload.get(field) is not None


def _flag(field: str) -> Callable[[dict[str, Any]], bool | None]:
    return lambda payload: payload.get(field)


def _inverted(field: str) -> Callable[[dict[str, Any]], bool | None]:
    return lambda payload: None if payload.get(field) is None else not payload[field]


DEVICE_DESCRIPTIONS: tuple[AjaxBinarySensorDescription, ...] = (
    AjaxBinarySensorDescription(key="opening", translation_key="opening", device_class=BinarySensorDeviceClass.OPENING,
                                value_fn=_inverted("reed_closed"), exists_fn=_present("reed_closed")),
    AjaxBinarySensorDescription(key="extra_contact", translation_key="extra_contact", device_class=BinarySensorDeviceClass.OPENING,
                                value_fn=_inverted("extra_contact_closed"),
                                exists_fn=lambda d: d.get("extra_contact_aware") is True and d.get("extra_contact_closed") is not None),
    AjaxBinarySensorDescription(key="motion", translation_key="motion", device_class=BinarySensorDeviceClass.MOTION,
                                value_fn=_flag("motion_detected"), exists_fn=_present("motion_detected")),
    AjaxBinarySensorDescription(key="glass_break", translation_key="glass_break", device_class=BinarySensorDeviceClass.SOUND,
                                value_fn=_flag("glass_break_detected"), exists_fn=_present("glass_break_detected")),
    AjaxBinarySensorDescription(key="moisture", translation_key="moisture", device_class=BinarySensorDeviceClass.MOISTURE,
                                value_fn=_flag("leak_detected"), exists_fn=_present("leak_detected")),
    AjaxBinarySensorDescription(key="smoke", translation_key="smoke", device_class=BinarySensorDeviceClass.SMOKE,
                                value_fn=_flag("smoke_alarm_detected"), exists_fn=_present("smoke_alarm_detected")),
    AjaxBinarySensorDescription(key="connectivity", translation_key="connectivity", device_class=BinarySensorDeviceClass.CONNECTIVITY,
                                entity_category=EntityCategory.DIAGNOSTIC, value_fn=_flag("online"), exists_fn=_present("online")),
    AjaxBinarySensorDescription(key="tamper", translation_key="tamper", device_class=BinarySensorDeviceClass.TAMPER,
                                entity_category=EntityCategory.DIAGNOSTIC, value_fn=_flag("tampered"), exists_fn=_present("tampered")),
    AjaxBinarySensorDescription(key="problem", translation_key="problem", device_class=BinarySensorDeviceClass.PROBLEM,
                                entity_category=EntityCategory.DIAGNOSTIC,
                                value_fn=lambda d: bool(d.get("malfunctions")), exists_fn=lambda d: True,
                                attributes_fn=lambda d: {"malfunctions": list(d.get("malfunctions") or [])}),
)

HUB_DESCRIPTIONS: tuple[AjaxBinarySensorDescription, ...] = (
    AjaxBinarySensorDescription(key="connectivity", translation_key="connectivity", device_class=BinarySensorDeviceClass.CONNECTIVITY,
                                entity_category=EntityCategory.DIAGNOSTIC, value_fn=_flag("online"), exists_fn=_present("online")),
    AjaxBinarySensorDescription(key="tamper", translation_key="tamper", device_class=BinarySensorDeviceClass.TAMPER,
                                entity_category=EntityCategory.DIAGNOSTIC, value_fn=_flag("tampered"), exists_fn=_present("tampered")),
    AjaxBinarySensorDescription(key="power", translation_key="power", device_class=BinarySensorDeviceClass.POWER,
                                entity_category=EntityCategory.DIAGNOSTIC, value_fn=_flag("externallyPowered"), exists_fn=_present("externallyPowered")),
)


async def async_setup_entry(hass: HomeAssistant, entry: AjaxSecurFlowConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    rt = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for hub_id, hub_data in rt.coordinator.data.items():
        entities.extend(AjaxHubBinarySensor(rt.coordinator, hub_id, desc) for desc in HUB_DESCRIPTIONS if desc.exists_fn(hub_data.hub))
        for device_id, device in hub_data.devices.items():
            entities.extend(
                AjaxDeviceBinarySensor(rt.coordinator, hub_id, device_id, rt.rooms, desc)
                for desc in DEVICE_DESCRIPTIONS if desc.exists_fn(device)
            )
    async_add_entities(entities)


class AjaxDeviceBinarySensor(AjaxSecurFlowDeviceEntity, BinarySensorEntity):
    entity_description: AjaxBinarySensorDescription

    def __init__(self, coordinator: AjaxSecurFlowCoordinator, hub_id: str, device_id: str, rooms: dict[str, str], description: AjaxBinarySensorDescription) -> None:
        super().__init__(coordinator, hub_id, device_id, rooms)
        self.entity_description = description
        self._attr_unique_id = f"{hub_id}_{device_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.device)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.device)


class AjaxHubBinarySensor(AjaxSecurFlowHubEntity, BinarySensorEntity):
    entity_description: AjaxBinarySensorDescription

    def __init__(self, coordinator: AjaxSecurFlowCoordinator, hub_id: str, description: AjaxBinarySensorDescription) -> None:
        super().__init__(coordinator, hub_id)
        self.entity_description = description
        self._attr_unique_id = f"{hub_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.hub_data.hub)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_binary_sensor.py tests/test_init.py -v`
Expected: all PASSED, including `test_devices_registered_with_via_device` from Task 8

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajaxsecurflow/binary_sensor.py tests/test_binary_sensor.py
git commit -m "feat: add device and hub binary sensors"
```

---

### Task 11: Sensors

**Files:**
- Modify: `custom_components/ajaxsecurflow/sensor.py`
- Test: `tests/test_sensor.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_sensor.py
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.helpers import entity_registry as er

from custom_components.ajaxsecurflow.const import DOMAIN


def _state(hass, unique_id):
    eid = er.async_get(hass).async_get_entity_id(SENSOR_DOMAIN, DOMAIN, unique_id)
    return hass.states.get(eid) if eid else None


async def test_device_sensors(hass, init_integration):
    assert _state(hass, "HUB1_D1_battery").state == "88"
    assert _state(hass, "HUB1_D1_signal_level").state == "strong"
    assert _state(hass, "HUB1_D1_temperature").state == "21.5"
    assert _state(hass, "HUB1_D1_humidity") is None
    assert _state(hass, "HUB1_D1_co2") is None
    assert _state(hass, "HUB1_D2_temperature") is None


async def test_hub_sensors(hass, init_integration):
    assert _state(hass, "HUB1_battery").state == "100"
    assert _state(hass, "HUB1_gsm_signal").state == "strong"
    assert _state(hass, "HUB1_firmware_version").state == "2.20.1"
    assert _state(hass, "HUB1_last_event").state == "unknown"


async def test_last_event_reflects_sse(hass, init_integration):
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["HUB1"].last_event = {"event_type": "ALARM", "tag": "MotionDetected", "timestamp": "2026-09-18T10:00:00+00:00", "description": "Movimiento", "severity": "critical"}
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()
    state = _state(hass, "HUB1_last_event")
    assert state.state == "ALARM"
    assert state.attributes["tag"] == "MotionDetected"
    assert state.attributes["timestamp"] == "2026-09-18T10:00:00+00:00"


async def test_unknown_signal_value_is_unknown(hass, mock_api, config_entry):
    devices = mock_api.get_devices.return_value
    mock_api.get_devices.return_value = [{**devices[0], "signal_level": "SOMETHING_NEW"}, devices[1]]
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert _state(hass, "HUB1_D1_signal_level").state == "unknown"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_sensor.py -v`
Expected: FAIL with `AttributeError: 'NoneType' object has no attribute 'state'`

- [ ] **Step 3: Write the platform**

```python
# custom_components/ajaxsecurflow/sensor.py
"""Sensors for Ajax devices and hubs."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION, PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AjaxSecurFlowConfigEntry
from .const import SIGNAL_LEVELS
from .coordinator import AjaxSecurFlowCoordinator
from .entity import AjaxSecurFlowDeviceEntity, AjaxSecurFlowHubEntity
from .models import HubData

SIGNAL_OPTIONS = [level.lower() for level in SIGNAL_LEVELS]


@dataclass(frozen=True, kw_only=True)
class AjaxSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Any], Any]
    exists_fn: Callable[[Any], bool]
    attributes_fn: Callable[[Any], dict[str, Any]] | None = None


def _get(field: str) -> Callable[[dict[str, Any]], Any]:
    return lambda payload: payload.get(field)


def _present(field: str) -> Callable[[dict[str, Any]], bool]:
    return lambda payload: payload.get(field) is not None


def _signal(raw: Any) -> str | None:
    value = str(raw or "").lower()
    return value if value in SIGNAL_OPTIONS else None


DEVICE_DESCRIPTIONS: tuple[AjaxSensorDescription, ...] = (
    AjaxSensorDescription(key="battery", translation_key="battery", device_class=SensorDeviceClass.BATTERY,
                          native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT,
                          entity_category=EntityCategory.DIAGNOSTIC, value_fn=_get("battery_level"), exists_fn=_present("battery_level")),
    AjaxSensorDescription(key="signal_level", translation_key="signal_level", device_class=SensorDeviceClass.ENUM,
                          options=SIGNAL_OPTIONS, entity_category=EntityCategory.DIAGNOSTIC,
                          value_fn=lambda d: _signal(d.get("signal_level")), exists_fn=_present("signal_level")),
    AjaxSensorDescription(key="temperature", translation_key="temperature", device_class=SensorDeviceClass.TEMPERATURE,
                          native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT,
                          value_fn=_get("temperature"), exists_fn=_present("temperature")),
    AjaxSensorDescription(key="humidity", translation_key="humidity", device_class=SensorDeviceClass.HUMIDITY,
                          native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT,
                          value_fn=_get("humidity"), exists_fn=_present("humidity")),
    AjaxSensorDescription(key="co2", translation_key="co2", device_class=SensorDeviceClass.CO2,
                          native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION, state_class=SensorStateClass.MEASUREMENT,
                          value_fn=_get("co2"), exists_fn=_present("co2")),
)

HUB_DESCRIPTIONS: tuple[AjaxSensorDescription, ...] = (
    AjaxSensorDescription(key="battery", translation_key="battery", device_class=SensorDeviceClass.BATTERY,
                          native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT,
                          entity_category=EntityCategory.DIAGNOSTIC,
                          value_fn=lambda hd: (hd.hub.get("battery") or {}).get("chargeLevelPercentage"),
                          exists_fn=lambda hd: (hd.hub.get("battery") or {}).get("chargeLevelPercentage") is not None),
    AjaxSensorDescription(key="gsm_signal", translation_key="gsm_signal", device_class=SensorDeviceClass.ENUM,
                          options=SIGNAL_OPTIONS, entity_category=EntityCategory.DIAGNOSTIC,
                          value_fn=lambda hd: _signal((hd.hub.get("gsm") or {}).get("signalLevel")),
                          exists_fn=lambda hd: (hd.hub.get("gsm") or {}).get("signalLevel") is not None),
    AjaxSensorDescription(key="firmware_version", translation_key="firmware_version", entity_category=EntityCategory.DIAGNOSTIC,
                          value_fn=lambda hd: (hd.hub.get("firmware") or {}).get("version"),
                          exists_fn=lambda hd: (hd.hub.get("firmware") or {}).get("version") is not None),
    AjaxSensorDescription(key="last_event", translation_key="last_event",
                          value_fn=lambda hd: (hd.last_event or {}).get("event_type"),
                          exists_fn=lambda hd: True,
                          attributes_fn=lambda hd: {k: (hd.last_event or {}).get(k) for k in ("tag", "timestamp", "description", "severity")}),
)


async def async_setup_entry(hass: HomeAssistant, entry: AjaxSecurFlowConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    rt = entry.runtime_data
    entities: list[SensorEntity] = []
    for hub_id, hub_data in rt.coordinator.data.items():
        entities.extend(AjaxHubSensor(rt.coordinator, hub_id, desc) for desc in HUB_DESCRIPTIONS if desc.exists_fn(hub_data))
        for device_id, device in hub_data.devices.items():
            entities.extend(
                AjaxDeviceSensor(rt.coordinator, hub_id, device_id, rt.rooms, desc)
                for desc in DEVICE_DESCRIPTIONS if desc.exists_fn(device)
            )
    async_add_entities(entities)


class AjaxDeviceSensor(AjaxSecurFlowDeviceEntity, SensorEntity):
    entity_description: AjaxSensorDescription

    def __init__(self, coordinator: AjaxSecurFlowCoordinator, hub_id: str, device_id: str, rooms: dict[str, str], description: AjaxSensorDescription) -> None:
        super().__init__(coordinator, hub_id, device_id, rooms)
        self.entity_description = description
        self._attr_unique_id = f"{hub_id}_{device_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.device)


class AjaxHubSensor(AjaxSecurFlowHubEntity, SensorEntity):
    entity_description: AjaxSensorDescription

    def __init__(self, coordinator: AjaxSecurFlowCoordinator, hub_id: str, description: AjaxSensorDescription) -> None:
        super().__init__(coordinator, hub_id)
        self.entity_description = description
        self._attr_unique_id = f"{hub_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.hub_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.hub_data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_sensor.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajaxsecurflow/sensor.py tests/test_sensor.py
git commit -m "feat: add device and hub sensors"
```

---

### Task 12: Diagnostics

**Files:**
- Create: `custom_components/ajaxsecurflow/diagnostics.py`
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_diagnostics.py
from custom_components.ajaxsecurflow.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_redacts_secrets(hass, init_integration):
    diag = await async_get_config_entry_diagnostics(hass, init_integration)
    assert diag["entry"]["token"] == "**REDACTED**"
    assert diag["entry"]["base_url"] == "**REDACTED**"
    assert diag["plan"] == "pro"
    assert diag["hubs"]["HUB1"]["hub"]["state"] == "DISARMED"
    assert "D1" in diag["hubs"]["HUB1"]["devices"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_diagnostics.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write diagnostics**

```python
# custom_components/ajaxsecurflow/diagnostics.py
"""Diagnostics dump with secrets redacted."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import AjaxSecurFlowConfigEntry
from .const import CONF_BASE_URL, CONF_TOKEN

TO_REDACT = {CONF_TOKEN, CONF_BASE_URL, "email", "login", "phone"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: AjaxSecurFlowConfigEntry) -> dict[str, Any]:
    rt = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "plan": rt.plan,
        "rooms": rt.rooms,
        "sse_running": rt.listener.running,
        "hubs": {hub_id: asdict(hub_data) for hub_id, hub_data in (rt.coordinator.data or {}).items()},
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_diagnostics.py -v`
Expected: 1 PASSED

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajaxsecurflow/diagnostics.py tests/test_diagnostics.py
git commit -m "feat: add redacted diagnostics"
```

---

### Task 13: README, full suite, smoke test and tag

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write the README**

```markdown
# AjaxSecurFlow for Home Assistant

Brings your Ajax Systems hubs and devices into Home Assistant through the [AjaxSecurFlow](https://www.ajaxsecurflow.com) API. Home Assistant never talks to Ajax directly and needs no Ajax API key.

## Requirements

- Home Assistant 2025.1 or newer.
- An AjaxSecurFlow account on the **Basic** plan or higher. **Pro** or **Premium** is required to arm/disarm.

## Installation (HACS)

1. HACS → Integrations → ⋮ → **Custom repositories**.
2. Add `https://github.com/virapa/ajaxsecurflow-hass` with category **Integration**.
3. Install **AjaxSecurFlow** and restart Home Assistant.

## Setup

1. In the AjaxSecurFlow dashboard open **Perfil → Integraciones** and create a token. Copy it: it is shown only once.
2. Settings → Devices & services → **Add integration** → **AjaxSecurFlow**.
3. Paste the token. Leave the API URL as is unless you self-host the backend.

Options (⚙ on the integration card): polling interval, 30-600 s (default 60).

## What you get

| Platform | Entities |
|---|---|
| `alarm_control_panel` | one per hub; one per group when groups mode is enabled. States: disarmed, armed_away, armed_night, armed_custom_bypass (partial), triggered |
| `binary_sensor` | per device: opening, external contact, motion, glass break, leak, smoke, online, tamper, problem (with `malfunctions` attribute). Per hub: online, tamper, external power |
| `sensor` | per device: battery, signal, temperature, humidity, CO2. Per hub: battery, GSM signal, firmware, last event |

Entities are created only for the fields a device actually reports.

## Real-time events

Changes arrive within a second over Server-Sent Events; polling reconciles the full state on the configured interval. Every event also fires `ajaxsecurflow_event` on the Home Assistant bus with the backend's hybrid envelope:

```yaml
automation:
  - alias: Notify on Ajax alarm
    trigger:
      - platform: event
        event_type: ajaxsecurflow_event
        event_data:
          event_type: ALARM
    action:
      - service: notify.mobile_app_phone
        data:
          title: "{{ trigger.event.data.title }}"
          message: "{{ trigger.event.data.description }}"
```

Recognised `eventTag` values are listed in `custom_components/ajaxsecurflow/const.py`; open an issue with a diagnostics dump to add new ones.

## Troubleshooting

- **Re-authentication requested**: the token was revoked or expired. Create a new one and paste it.
- **Arming fails with "requires a Pro or Premium plan"**: upgrade the AjaxSecurFlow plan.
- **No real-time updates**: the Basic plan includes the stream; check the log for `Real-time stream not included`. Polling still works.
- Download diagnostics from the integration card before reporting an issue; tokens and emails are redacted.

## Development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements_test.txt
python -m pytest tests -v
```

## License

Proprietary. See `LICENSE`.
```

- [ ] **Step 2: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all PASSED (≈75 tests)

- [ ] **Step 3: hassfest/HACS sanity (optional locally)**

Run: `python -c "import json; json.load(open('custom_components/ajaxsecurflow/manifest.json')); json.load(open('hacs.json')); json.load(open('custom_components/ajaxsecurflow/strings.json'))"`
Expected: no output. The GitHub workflow runs the real validators on push.

- [ ] **Step 4: Smoke test against a real backend**

1. Copy `custom_components/ajaxsecurflow` into a Home Assistant dev instance's `config/custom_components/` (or a devcontainer) and restart.
2. Create an integration token in the dashboard (backend plan Task 10) and add the integration.
3. Verify: hub panel state matches the Ajax app; open a door → `binary_sensor.<door>_opening` turns on within ~1 s; arm from HA → Ajax app shows armed (Pro plan).
4. Revoke the token in the dashboard → HA shows the re-authenticate notification within one polling interval.

- [ ] **Step 5: Commit and tag**

```bash
git add README.md
git commit -m "docs: add README with installation and usage"
git tag v0.1.0
```

Create the GitHub repository `virapa/ajaxsecurflow-hass`, push `main` and the tag, and add the repo URL to `HA_DOCS_URL` in the dashboard (`frontend/src/features/integrations/ApiTokensSection.tsx`) if it differs.

---

## Self-review

- **Spec coverage:** 6.1 structure → Tasks 1-12; 6.2 config flow → Task 6; 6.3 client → Task 2; 6.4 coordinator/SSE/apply_event → Tasks 3-5; 6.5 entities → Tasks 7, 9-11; 6.6 diagnostics → Task 12; 7 error table (HA rows) → Tasks 4, 5, 6, 8, 9; 8 HA tests → each task; README/automation example → Task 13.
- **Type consistency:** `HubData(hub, groups, devices, triggered, last_event)` used identically in Tasks 3, 4, 5, 9-12. `AjaxSecurFlowClient.set_arm_state(hub_id, arm_state, group_id=None)` matches Task 2 and Task 9 assertions (`("HUB1", 1, None)`). `runtime_data` fields `client, coordinator, listener, plan, rooms` match Tasks 8-12. Unique ids: `{hub}_panel`, `{hub}_{group}_panel`, `{hub}_{device}_{key}`, `{hub}_{key}` consistent between platforms and tests.
- **Placeholders:** none. Platform placeholders in Task 8 Step 5 are explicitly replaced in Tasks 9-11.
- **Deviation from spec, deliberate:** binary sensors are created by field presence rather than by device-type table; the type table in the spec is what makes those fields present, so the observable result is the same and the code stays smaller.
