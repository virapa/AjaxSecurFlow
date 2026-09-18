# Integración de Home Assistant (HACS) para AjaxSecurFlow

- Fecha: 2026-09-18
- Estado: aprobado
- Alcance: cambios en backend y frontend de este repo + nueva integración HACS en repo separado (`ajaxsecurflow-hass`)

## 1. Objetivo

Exponer los hubs y dispositivos Ajax de un usuario de AjaxSecurFlow en Home Assistant, usando exclusivamente la API de AjaxSecurFlow. Home Assistant nunca habla con la API de Ajax Systems ni necesita API key de Ajax.

Referencias de inspiración (no se copian, se adaptan a este backend):
- https://github.com/prismagroupsa/Ajax_alarm_ha_integration (polling con `DataUpdateCoordinator`, options flow)
- https://github.com/foXaCe/ajax-security-hass (modo proxy con SSE, grupos, mapa amplio de dispositivos)

## 2. Decisiones tomadas

| Decisión | Elección |
|---|---|
| Autenticación de HA | Token de integración de larga duración, revocable, generado desde el dashboard |
| Tiempo real | SSE (`/ajax/events/stream`) + polling de respaldo |
| Alcance de entidades v1 | Ampliado: panel de alarma por hub y grupo, binary_sensor de apertura/movimiento/rotura/inundación/humo/tamper/online/problema, sensores de batería/señal/temperatura/humedad/CO2 |
| Ubicación del código de HA | Repo separado `ajaxsecurflow-hass` (requisito de HACS) |
| Cómo sirve el backend el estado | Endpoints actuales; se amplían los esquemas para que la lista de dispositivos ya lleve el estado de los sensores |
| Dashboard de tokens | Sí, sección mínima en la página de perfil |

## 3. Arquitectura

```
Home Assistant (custom_components/ajaxsecurflow)
   │  Authorization: Bearer asf_<token>
   ├── polling: GET /api/v1/ajax/hubs, /hubs/{id}, /hubs/{id}/devices, /hubs/{id}/groups
   ├── comandos: POST /api/v1/ajax/hubs/{id}/arm-state
   └── SSE: GET /api/v1/ajax/events/stream (reconexión con backoff)
                    │
            AjaxSecurFlow API ──► Ajax Systems API
                    ▲
            SQS worker ──► Redis pub/sub (hub_events:{hub_id}) ──► SSE
```

Con polling de 60 s y 3 hubs, HA genera unas 10 peticiones por minuto frente al límite global de 100 por minuto del rate limiter.

## 4. Backend (este repo)

### 4.1 Tokens de integración

Módulo `backend/app/modules/auth`.

**Modelo `ApiToken`** (tabla `api_tokens`, migración Alembic nueva con `down_revision = 'e7f1a9b2c3d4'`):

| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| user_id | int FK users.id, ondelete CASCADE, index | |
| name | str, not null | etiqueta dada por el usuario |
| token_hash | str, unique, index, not null | SHA-256 del token en claro |
| prefix | str(12), not null | `asf_` + primeros 8 chars aleatorios, para identificar en UI |
| last_used_at | datetime tz, nullable | actualizado como máximo una vez por minuto |
| expires_at | datetime tz, nullable | null = sin caducidad |
| revoked_at | datetime tz, nullable | null = activo |
| created_at | datetime tz, server_default now | |

**Formato del token**: `asf_` + `secrets.token_urlsafe(30)`. No es JWT. Se valida por hash en base de datos, así la revocación es inmediata sin pasar por la blacklist de Redis.

**Endpoints** (`/api/v1/auth/api-tokens`, requieren sesión JWT normal; un token `asf_` no puede gestionar tokens):

| Método | Ruta | Respuesta |
|---|---|---|
| POST | `/api-tokens` body `{name, expires_in_days?}` | 201 `{id, name, prefix, token, created_at, expires_at}`. `token` solo se devuelve aquí |
| GET | `/api-tokens` | lista `[{id, name, prefix, last_used_at, expires_at, created_at}]` de tokens no revocados |
| DELETE | `/api-tokens/{id}` | 204; marca `revoked_at` |

Reglas:
- Requiere `billing_service.can_access_feature(user, "read_devices")` (plan Basic o superior). Free recibe 403.
- Máximo 10 tokens activos por usuario; el undécimo recibe 400.
- Se audita `API_TOKEN_CREATED` y `API_TOKEN_REVOKED` vía `security_service.log_request_action`.

**Cambios en `get_current_user`** (`backend/app/modules/auth/service.py`):
- Si el bearer empieza por `asf_`: calcular hash, buscar `ApiToken` activo (no revocado, no expirado), cargar el usuario y devolverlo. Saltar verificación de User-Agent, IP y blacklist JTI. Si no existe: 401 genérico y auditoría `API_TOKEN_INVALID`.
- Si no empieza por `asf_`: flujo JWT actual sin cambios.
- Actualizar `last_used_at` solo si han pasado más de 60 s desde el último valor, para no escribir en cada petición.

### 4.2 Esquemas de dispositivos y hubs

`backend/app/modules/ajax/schemas.py`:

- `DeviceListItem` y `DeviceDetail` añaden (todos opcionales, serializados en snake_case, con `AliasChoices` para el camelCase de Ajax):
  `battery_level` (batteryChargeLevelPercentage), `signal_level` (signalLevel), `temperature`, `tampered`, `state`, `malfunctions` (lista, default vacía), `reed_closed` (reedClosed), `extra_contact_closed` (extraContactClosed), `extra_contact_aware` (extraContactAware), `motion_detected` (motionDetected), `glass_break_detected` (glassBreakDetected), `leak_detected` (leakDetected), `smoke_alarm_detected` (smokeAlarmDetected), `humidity`, `co2`.
- `HubDetail` añade `groups_enabled` (groupsEnabled).
- `HubDetail.state` documenta los valores posibles de Ajax: `DISARMED`, `ARMED`, `NIGHT_MODE`, `ARMED_NIGHT_MODE_ON/OFF`, `DISARMED_NIGHT_MODE_ON/OFF`, `PARTIALLY_ARMED_NIGHT_MODE_ON/OFF`.

La lista de dispositivos ya pide `enrich=true` y aplana `properties`, así que estos campos llegan sin llamadas extra. No se crea ningún endpoint nuevo. `/hubs/{id}/arm-state` no cambia.

### 4.3 SSE

Sin cambios de código. El sobre híbrido que emite `normalize_ajax_event` pasa a ser contrato documentado para HA:

```json
{
  "id": "…", "hub_id": "…", "event_type": "ALARM|SECURITY|COMMON|MALFUNCTION|FUNCTION_RECOVERED|…",
  "title": "…", "description": "…", "severity": "info|success|warning|critical",
  "timestamp": "ISO-8601", "media_urls": [], "source": "sqs",
  "data": { "event": { "eventId", "hubId", "eventTag", "sourceObjectId", "sourceObjectType", "sourceObjectName", "transition", "timestamp", "additionalData" }, "recipient": {} }
}
```

Se añade este bloque a `backend/docs/INTEGRATION_EXAMPLES.md`.

### 4.4 Documentación

- `backend/docs/API_PERMISSIONS.md`: fila para `/auth/api-tokens` (Basic+).
- `CHANGELOG.md`: entrada de la versión.

## 5. Frontend (este repo)

Feature nueva `frontend/src/features/integrations/`:

- `api-token.service.ts`: `create(name)`, `list()`, `revoke(id)` con `apiClient`, siguiendo el patrón de `hub.service.ts`.
- `ApiTokensSection.tsx`: sección "Integraciones" montada dentro de `ProfileComponent` bajo los datos de cuenta. Sin ruta nueva.
  - Botón "Crear token" abre un input de nombre. Tras crear, muestra el token completo una sola vez con botón copiar y aviso de que no se volverá a mostrar.
  - Lista: nombre, prefijo, creado, último uso, botón revocar con confirmación.
  - Si el plan es Free, muestra aviso de plan requerido y deshabilita crear.
  - Incluye enlace al README del repo `ajaxsecurflow-hass` con instrucciones de instalación en HACS.
- Textos en `frontend/src/shared/i18n/es.ts` bajo `profile.integrations`.
- Cumple la regla del repo: leer `DESIGN.md` si existe; crearlo antes si no.

## 6. Integración de Home Assistant (repo `ajaxsecurflow-hass`)

Dominio: `ajaxsecurflow`. Creado como directorio hermano `../ajaxsecurflow-hass` con su propio git. Versión mínima de HA: 2025.1.

### 6.1 Estructura

```
custom_components/ajaxsecurflow/
├── __init__.py            # async_setup_entry: crea api, coordinator, listener SSE; async_unload_entry
├── manifest.json          # domain, name, version, iot_class: cloud_push, config_flow: true, requirements: []
├── config_flow.py         # user step (base_url, token) + reauth step + options flow (scan_interval)
├── api.py                 # AjaxSecurFlowClient (aiohttp de HA): get_me, get_hubs, get_hub, get_devices, get_groups, get_rooms, set_arm_state, stream_events
├── coordinator.py         # AjaxSecurFlowCoordinator(DataUpdateCoordinator) + SSEListener
├── const.py               # DOMAIN, defaults, DEVICE_CLASS_BY_TYPE, EVENT_TAG_MAP, ARM_STATE_MAP
├── entity.py              # AjaxSecurFlowEntity base: device_info, unique_id, available
├── alarm_control_panel.py
├── binary_sensor.py
├── sensor.py
├── diagnostics.py         # volcado con token redactado
├── strings.json
└── translations/en.json, es.json
hacs.json                  # {"name": "AjaxSecurFlow", "render_readme": true}
README.md
tests/                     # pytest-homeassistant-custom-component
requirements_test.txt
```

Sin `button` de pánico en v1: el backend solo expone arm-state.

### 6.2 Config flow

1. Paso `user`: `base_url` (default `https://api.ajaxsecurflow.com`) y `token`.
2. Valida con `GET /api/v1/auth/me`. Errores: `cannot_connect`, `invalid_auth` (401), `plan_free` (plan free). Plan basic: se acepta con aviso `no_control` en la descripción del paso final.
3. `unique_id` = email de `/auth/me`; `_abort_if_unique_id_configured`.
4. Paso `reauth`: pide solo un token nuevo cuando el coordinator lanza `ConfigEntryAuthFailed`.
5. Options flow: `scan_interval` entre 30 y 600 s, default 60.

### 6.3 Cliente API (`api.py`)

- Cabeceras: `Authorization: Bearer <token>`, `User-Agent: ajaxsecurflow-hass/<version>`.
- Timeout 15 s por petición. Excepciones propias: `AuthError` (401), `PlanError` (403), `RateLimitError` (429), `ApiError` (resto).
- `stream_events()` es un async generator sobre `/api/v1/ajax/events/stream` que parsea líneas `event: ajax_event` / `data: {...}` e ignora comentarios `: ping`.

### 6.4 Coordinator y datos

- Un `DataUpdateCoordinator` por config entry. `_async_update_data`: `get_hubs()`, y por hub `get_hub`, `get_devices`, `get_groups` en paralelo con `asyncio.gather`. Rooms se cargan una sola vez en setup para `suggested_area`.
- Estructura: `{hub_id: {"hub": HubDetail, "groups": {group_id: Group}, "devices": {device_id: Device}}}`.
- `RateLimitError` y `ApiError` → `UpdateFailed`. `AuthError` → `ConfigEntryAuthFailed`. Tras 2 fallos consecutivos las entidades pasan a `unavailable` (comportamiento estándar de HA).
- `SSEListener`: tarea de fondo creada en setup, cancelada en unload. Reconexión con backoff exponencial 5 s → 5 min. Si recibe 403, se detiene y queda solo polling. Por cada evento:
  - Localiza `hub_id`; si el hub no está en `coordinator.data`, ignora y programa `async_request_refresh`.
  - Aplica actualización parcial según `EVENT_TAG_MAP` y `transition`:
    - arm/disarm/night (por `event_type` o `eventTag`, con `sourceObjectType` GROUP → grupo): actualiza `state` del hub o grupo.
    - `ExtContactOpened`/`ReedOpened` (+ `RECOVERED`): `reed_closed` / `extra_contact_closed` del dispositivo `sourceObjectId`.
    - `MotionDetected`: `motion_detected = True`; se limpia en el siguiente polling.
    - `GlassBreak`, `Leak`, `Smoke`: flag correspondiente; `RECOVERED` lo limpia.
    - `event_type == "ALARM"`: marca `triggered` en el hub hasta el siguiente disarm o polling que devuelva DISARMED.
    - Tamper, offline, malfunction: `tampered` / `online` / `malfunctions`.
  - Llama a `async_set_updated_data(data)` y dispara `hass.bus.async_fire("ajaxsecurflow_event", envelope)`.
  - Idempotente: aplicar dos veces el mismo evento (fan-out de Ajax por usuario) deja el mismo estado.

### 6.5 Entidades

**Device registry**: un dispositivo HA por hub (`identifiers={(DOMAIN, hub_id)}`, modelo `hub_subtype`, sw_version firmware) y uno por dispositivo Ajax (`via_device` = hub, modelo `device_type`, `suggested_area` = nombre de sala).

**alarm_control_panel**
- Uno por hub. Si `groups_enabled`, uno adicional por grupo.
- Mapa de estado Ajax → HA: `DISARMED*` → `disarmed`; `ARMED*` → `armed_away`; `NIGHT_MODE`, `*_NIGHT_MODE_ON` → `armed_night`; `PARTIALLY_ARMED_*` → `armed_custom_bypass`; alarma activa → `triggered`.
- Comandos: `alarm_disarm` → armState 0, `alarm_arm_away` → 1, `alarm_arm_night` → 2, con `groupId` para paneles de grupo. `code_arm_required = False`.
- `supported_features` = ARM_AWAY | ARM_NIGHT si el plan es pro/premium; vacío si basic. Un 403 en comando lanza `HomeAssistantError` con clave de traducción `plan_required`.

**binary_sensor** (por dispositivo, según `DEVICE_CLASS_BY_TYPE` derivado del enum `DeviceType` de Ajax):

| Tipos | Clase | Fuente |
|---|---|---|
| DoorProtect*, SuperiorDoorProtect* | `opening` | `not reed_closed`; segunda entidad `opening` para `extra_contact_closed` si `extra_contact_aware` |
| MotionProtect*, MotionCam*, CombiProtect*, SuperiorMotionProtect*, MotionProtectOutdoor, DualCurtainOutdoor | `motion` | `motion_detected` |
| GlassProtect*, CombiProtect* | `sound` | `glass_break_detected` |
| LeaksProtect | `moisture` | `leak_detected` |
| FireProtect*, FireProtectPlus | `smoke` | `smoke_alarm_detected` |
| todos | `connectivity` | `online` |
| todos | `tamper` | `tampered` |
| todos | `problem` | `malfunctions` no vacío (atributo con la lista) |
| hub | `connectivity`, `tamper`, `power` | `online`, `tampered`, `externallyPowered` |

Una entidad solo se crea si el campo fuente viene en el payload del dispositivo (no `None`).

**sensor**
- Dispositivo: `battery` (%, `battery_level`), `signal_level` (texto, categoría diagnóstico), `temperature` (°C), `humidity` (%), `co2` (ppm). Solo si el campo existe.
- Hub: `battery` (%), `gsm_signal` (texto), `firmware_version` (diagnóstico), `last_event` (texto con `event_type` del último evento SSE, atributo timestamp).

### 6.6 Diagnostics

`diagnostics.py` devuelve `coordinator.data` y la config entry con `token` y `base_url` redactados.

## 7. Manejo de errores

| Situación | Backend | Home Assistant |
|---|---|---|
| Token revocado o inexistente | 401 genérico, auditoría `API_TOKEN_INVALID` | `ConfigEntryAuthFailed` → reauth flow |
| Plan Free | 403 al crear token; 403 en devices/stream | Config flow muestra el error `plan_free` en el formulario |
| Plan Basic y comando de armado | 403 | `HomeAssistantError` traducible; panel sin features de control |
| Rate limit | 429 | `UpdateFailed`, reintento en el siguiente ciclo |
| Backend caído | — | entidades `unavailable` tras 2 fallos; SSE reintenta con backoff |
| SSE con hub desconocido | — | ignora y programa refresh completo |
| Evento SQS duplicado (fan-out por usuario) | deduplicado por `eventId` en el worker | aplicación idempotente |
| Más de 10 tokens activos | 400 | — |

## 8. Tests

**Backend** (pytest, `backend/tests/unit`, mismo `conftest`):
- `test_api_tokens.py`: crear devuelve token en claro con prefijo `asf_`; listar no devuelve token; revocar marca `revoked_at`; límite de 10; Free recibe 403.
- `test_auth_api_token.py`: `get_current_user` con token válido, revocado, expirado, hash inexistente, y con User-Agent distinto al de creación (debe pasar); `last_used_at` no se reescribe dentro del minuto.
- `test_ajax_schemas.py`: `DeviceListItem`/`DeviceDetail` con payload real de `enrich=true` exponen `reed_closed`, `motion_detected`, `temperature`, `malfunctions`; `HubDetail.groups_enabled`.
- `test_plan_permissions.py`: fila nueva para `/auth/api-tokens`.

**Frontend** (vitest + testing-library):
- `ApiTokensSection.test.tsx`: crea y muestra el token una vez, lista, revoca con confirmación, estado Free deshabilitado. Servicio mockeado.

**Home Assistant** (`pytest-homeassistant-custom-component`, fixtures JSON de respuestas reales):
- `test_config_flow.py`: éxito, `invalid_auth`, `cannot_connect`, `plan_free`, reauth, options.
- `test_coordinator.py`: carga inicial, `UpdateFailed` en 429, `ConfigEntryAuthFailed` en 401.
- `test_sse.py`: parseo de líneas SSE, aplicación de cada `eventTag` del mapa, idempotencia, reconexión con backoff, parada en 403 (con `aioresponses`).
- `test_alarm_control_panel.py`: cada estado de Ajax → estado HA; comandos envían el body correcto; 403 → `HomeAssistantError`.
- `test_binary_sensor.py` y `test_sensor.py`: creación condicional por tipo y por presencia de campo.

## 9. Orden de entrega

1. Backend en este repo, rama `feat/ha-integration` desde `dev`: modelo + migración + endpoints de tokens, cambio en `get_current_user`, esquemas ampliados, docs, tests.
2. Frontend en la misma rama o PR siguiente: sección de tokens en perfil.
3. Repo `ajaxsecurflow-hass` en `../ajaxsecurflow-hass`: estructura HACS, config flow, cliente, coordinator, entidades, tests, README con instalación y ejemplo de automatización sobre `ajaxsecurflow_event`.

## 10. Fuera de alcance (v1)

- Botón de pánico, switches de relés/enchufes, cámaras, ajustes de dispositivos (requieren endpoints nuevos en el backend).
- Webhooks entrantes en HA como alternativa al SSE.
- Publicación en el store por defecto de HACS (se instala como repositorio personalizado).
