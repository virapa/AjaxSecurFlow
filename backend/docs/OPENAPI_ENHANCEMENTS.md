# OpenAPI/Swagger Enhancements

## Overview

This document describes the OpenAPI/Swagger enhancements implemented in AjaxSecurFlow to provide comprehensive, plan-aware API documentation.

---

## Custom OpenAPI Extensions

### Plan Requirement Extension (`x-required-plan`)

Each endpoint includes a custom extension indicating the minimum required subscription plan.

**Example:**
```yaml
paths:
  /api/v1/ajax/hubs/{hub_id}/devices:
    get:
      summary: List devices in a hub
      x-required-plan: basic
      responses:
        '200':
          description: Successful response
        '403':
          description: Insufficient plan (requires Basic+)
```

**Supported Values:**
- `free` - Available to all users
- `basic` - Requires Basic plan or higher
- `pro` - Requires Pro plan or higher
- `premium` - Requires Premium plan only

---

### Rate Limit Extension (`x-rate-limit`)

Endpoints include rate limiting information per plan tier.

**Example:**
```yaml
paths:
  /api/v1/ajax/hubs:
    get:
      summary: List all hubs
      x-rate-limit:
        free: 100/hour
        basic: 500/hour
        pro: 1000/hour
        premium: 5000/hour
```

---

## Security Schemes

### Bearer Token Authentication

All endpoints require Bearer token authentication obtained through the `/auth/token` endpoint.

**OpenAPI Configuration:**
```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT token obtained from /api/v1/auth/token endpoint.
        
        Example:
        ```
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        ```

security:
  - BearerAuth: []
```

---

## Endpoint Grouping (Tags)

Endpoints are organized into logical groups using OpenAPI tags:

### Tag Structure

| Tag                | Description                              | Endpoints                       |
| ------------------ | ---------------------------------------- | ------------------------------- |
| **Authentication** | User authentication and token management | `/auth/token`, `/auth/me`       |
| **Hubs**           | Hub listing and details (Free+)          | `/ajax/hubs`, `/ajax/hubs/{id}` |
| **Devices**        | Device management (Basic+)               | `/ajax/hubs/{id}/devices`       |
| **Rooms**          | Room organization (Basic+)               | `/ajax/hubs/{id}/rooms`         |
| **Groups**         | Security groups (Basic+)                 | `/ajax/hubs/{id}/groups`        |
| **Logs**           | Event logs and history (Basic+)          | `/ajax/hubs/{id}/logs`          |
| **Commands**       | System control (Pro+)                    | `/ajax/hubs/{id}/arm-state`     |
| **Proxy**          | Full Ajax API proxy (Premium)            | `/ajax/*`                       |
| **Billing**        | Subscription management                  | `/billing/*`                    |
| **Notifications**  | In-app notifications                     | `/notifications/*`              |

**OpenAPI Configuration:**
```yaml
tags:
  - name: Authentication
    description: User authentication and session management
  - name: Hubs
    description: Hub listing and details (Free+)
    externalDocs:
      description: Plan requirements
      url: /docs/API_PERMISSIONS.md#read-only-endpoints-free
  - name: Devices
    description: Device management and telemetry (Basic+)
    externalDocs:
      description: Plan requirements
      url: /docs/API_PERMISSIONS.md#deviceroomgroup-endpoints-basic
  # ... more tags
```

---

## Response Examples

### Success Responses (200)

Each endpoint includes realistic response examples for successful requests.

**Example: List Hubs**
```yaml
responses:
  '200':
    description: Successful response
    content:
      application/json:
        schema:
          type: array
          items:
            $ref: '#/components/schemas/Hub'
        examples:
          success:
            summary: Example hub list
            value:
              - id: "00022777"
                name: "Home Security"
                status: "armed"
                online: true
                role: "MASTER"
              - id: "00033888"
                name: "Office Security"
                status: "disarmed"
                online: true
                role: "PRO"
```

---

### Error Responses

#### 401 Unauthorized

Missing or invalid authentication token.

```yaml
responses:
  '401':
    description: Unauthorized - Invalid or missing token
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/Error'
        examples:
          missing_token:
            summary: Missing authorization header
            value:
              detail: "Not authenticated"
          invalid_token:
            summary: Invalid or expired token
            value:
              detail: "Could not validate credentials"
```

---

#### 403 Forbidden

Insufficient subscription plan for the requested endpoint.

```yaml
responses:
  '403':
    description: Forbidden - Insufficient plan
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/Error'
        examples:
          free_user_devices:
            summary: Free user accessing devices
            value:
              detail: "Device access not included in your plan"
          basic_user_commands:
            summary: Basic user sending commands
            value:
              detail: "Command execution not included in your plan"
          pro_user_proxy:
            summary: Pro user accessing proxy
            value:
              detail: "PREMIUM subscription required to access Proxy API"
```

---

#### 429 Too Many Requests

Rate limit exceeded for the current plan.

```yaml
responses:
  '429':
    description: Too Many Requests - Rate limit exceeded
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/Error'
        examples:
          rate_limit:
            summary: Rate limit exceeded
            value:
              detail: "Rate limit exceeded. Try again in 60 seconds."
              retry_after: 60
```

---

## Request Body Examples

Endpoints with request bodies include realistic examples.

**Example: Arm System (Pro+)**
```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          armState:
            type: integer
            enum: [0, 1, 2, 3]
            description: |
              Arm state:
              - 0: Disarmed
              - 1: Armed (full)
              - 2: Night mode
              - 3: Partial arm
      examples:
        arm_full:
          summary: Arm system (full)
          value:
            armState: 1
        arm_night:
          summary: Arm system (night mode)
          value:
            armState: 2
        disarm:
          summary: Disarm system
          value:
            armState: 0
```

---

## Schema Definitions

### Common Schemas

#### Hub Schema
```yaml
components:
  schemas:
    Hub:
      type: object
      properties:
        id:
          type: string
          example: "00022777"
        name:
          type: string
          example: "Home Security"
        status:
          type: string
          enum: [armed, disarmed, night]
          example: "armed"
        online:
          type: boolean
          example: true
        role:
          type: string
          enum: [MASTER, PRO, USER]
          example: "MASTER"
```

#### Device Schema
```yaml
Device:
  type: object
  properties:
    id:
      type: string
      example: "device123"
    name:
      type: string
      example: "Motion Detector"
    type:
      type: string
      example: "MotionProtect"
    battery:
      type: integer
      minimum: 0
      maximum: 100
      example: 85
    signal:
      type: string
      enum: [excellent, good, fair, poor]
      example: "excellent"
    status:
      type: string
      example: "active"
```

#### Error Schema
```yaml
Error:
  type: object
  properties:
    detail:
      type: string
      description: Human-readable error message
      example: "Device access not included in your plan"
```

---

## Server Definitions

AjaxSecurFlow uses a relative server definition to ensure compatibility with different hostnames and proxies. The documentation focuses on the production path.

```yaml
servers:
  - url: /api/v1
    description: Production environment
```

> **Note**: By using a relative URL as the server base, the Swagger UI remains functional regardless of whether it's accessed via `localhost`, a staging domain, or the production URL.

---

## API Information

### Contact Information
```yaml
info:
  title: AjaxSecurFlow Proxy API
  version: 1.0.0
  description: |
    Advanced, secure proxy for Ajax Systems API with tiered subscription plans.
    
    ## Features
    - Unified authentication with Ajax cloud
    - Session persistence with automated token refresh
    - SaaS billing via Stripe
    - Plan-based access control
    
    ## Documentation
    - [API Permissions](/docs/API_PERMISSIONS.md)
    - [Plan Migration Guide](/docs/PLAN_MIGRATION_GUIDE.md)
    - [Integration Examples](/docs/INTEGRATION_EXAMPLES.md)
  
  contact:
    name: AjaxSecurFlow Support
    email: support@ajaxsecurflow.com
    url: https://ajaxsecurflow.com/support
  
  license:
    name: Proprietary
    url: https://ajaxsecurflow.com/terms
```

---

## Accessing Enhanced Documentation

### Swagger UI

The enhanced OpenAPI documentation is available at:

**URL:** `http://localhost:8000/docs`

**Features:**
- Interactive API explorer
- Try-it-out functionality with Bearer token
- Plan requirement badges on each endpoint
- Realistic request/response examples
- Error response documentation

### ReDoc

Alternative documentation interface:

**URL:** `http://localhost:8000/redoc`

**Features:**
- Clean, readable layout
- Searchable endpoint list
- Grouped by tags
- Downloadable OpenAPI spec

### OpenAPI JSON

Raw OpenAPI specification:

**URL:** `http://localhost:8000/openapi.json`

**Use Cases:**
- Import into Postman
- Generate client SDKs
- Custom documentation tools

---

## Implementation Details

### Custom OpenAPI Configuration

The OpenAPI schema is dynamically generated and customized in `main.py` to support plan-based metadata and visual cleanup:

```python
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    try:
        # 1. Generate core schema
        openapi_schema = get_openapi(
            title="AjaxSecurFlow Proxy API",
            version="1.0.0",
            description=enhanced_description,
            routes=app.routes,
        )
        
        # 2. Add Security Schemes (JWT)
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
        openapi_schema["security"] = [{"BearerAuth": []}]
        
        # 3. Define Servers (Relative Path)
        openapi_schema["servers"] = [
            {"url": settings.API_V1_STR, "description": "Production environment"}
        ]
        
        # 4. Visual Cleanup: Strip /api/v1 from Swagger paths
        new_paths = {}
        for path, methods in openapi_schema["paths"].items():
            if path.startswith(settings.API_V1_STR):
                clean_path = path.replace(settings.API_V1_STR, "", 1)
                new_paths[clean_path or "/"] = methods
            else:
                new_paths[clean_path or path] = methods
        openapi_schema["paths"] = new_paths
        
        # 5. Add Custom Extensions (Plan Requirements)
        for path, path_item in openapi_schema["paths"].items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    operation = path_item[method]
                    if "/ajax/" in path:
                        if any(x in path for x in ["/devices", "/rooms", "/groups", "/logs"]):
                            operation["x-required-plan"] = "basic"
                        elif "/arm-state" in path:
                            operation["x-required-plan"] = "pro"
                        else:
                            operation["x-required-plan"] = "free"
                            
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    except Exception as e:
        return get_openapi(title="Fallback API", version="1.0.0", routes=app.routes)

app.openapi = custom_openapi
```

---

## Best Practices

### For API Consumers

1. **Always check plan requirements** before making requests
2. **Handle 403 errors gracefully** with upgrade prompts
3. **Respect rate limits** to avoid 429 errors
4. **Use Bearer token** in all authenticated requests
5. **Refer to examples** for request/response formats

### For API Maintainers

1. **Keep examples realistic** and up-to-date
2. **Document all error cases** with clear messages
3. **Update plan requirements** when permissions change
4. **Maintain consistent** tag and schema naming
5. **Version the API** when making breaking changes

---

## Related Documentation

- [API Permissions](./API_PERMISSIONS.md) - Detailed permission matrix
- [Integration Examples](./INTEGRATION_EXAMPLES.md) - Code samples
- [Plan Migration Guide](./PLAN_MIGRATION_GUIDE.md) - Subscription management
