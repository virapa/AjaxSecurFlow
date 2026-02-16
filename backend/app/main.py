from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from backend.app.core.config import settings
from backend.app.modules.ajax.service import AjaxAuthError
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (e.g. initialize DB connection pools if needed explicitly)
    yield
    # Shutdown logic


from fastapi.middleware.cors import CORSMiddleware
from backend.app.modules.router import api_router as modular_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## AjaxSecurFlow Proxy API

An advanced, secure proxy for Ajax Systems API with tiered subscription plans.

### Features
- **Corporate Auditing**: Comprehensive logging and tracking

### Subscription Plans

| Plan | Access Level |
|------|---------------|
| **Free** | Read-only (hubs, devices, rooms, groups) |
| **Basic** | Free + Logs & telemetry |
| **Pro** | Basic + Commands (arm/disarm) |
| **Premium** | Pro + Full API proxy |

### Authentication

All endpoints require authentication via Bearer token:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Get your token from `POST /api/v1/auth/token`

For detailed endpoint permissions, see [API Permissions Documentation](/docs/API_PERMISSIONS.md)
    """,
    contact={
        "name": "Development",
    },
    license_info={
        "name": "Proprietary",
    },
    lifespan=lifespan
)

import re
MALICIOUS_PATTERNS = [
    # Legacy server extensions
    r"\.(php|asp|aspx|jsp|cgi|pl|cfm|rb|py)$",
    # Sensitive files
    r"(\.env|\.git|\.vscode|\.ssh|web\.config|composer\.json|package\.json|Dockerfile)",
    # Admin panels
    r"/(admin|phpmyadmin|wp-admin|wp-content|wordpress|administrator|backoffice|cp|controlpanel|manager)",
    # Path traversal
    r"(/etc/passwd|/etc/shadow|/windows/system\.ini|win\.ini|\.\./)",
    # DB and logs
    r"\.(sql|bak|old|swp|log|sqlite|db)$",
    # Specific probes
    r"/(sdk|jk-status|balancer-manager|admin-console|webmail|happyaxis|uddiclient|fckeditor)"
]
MALICIOUS_REGEX = re.compile("|".join(MALICIOUS_PATTERNS), re.IGNORECASE)

@app.middleware("http")
async def request_shield_middleware(request: Request, call_next):
    """
    Backend Request Shield:
    Intercepts and blocks malicious scanning patterns before processing.
    """
    path = request.url.path
    if MALICIOUS_REGEX.search(path):
        logger.warning(f"[SECURITY] Blocked malicious backend probe: {path} from {request.client.host if request.client else 'unknown'}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Forbidden: Malicious activity detected."}
        )
    return await call_next(request)

# Global Exception Handlers
@app.exception_handler(AjaxAuthError)
async def ajax_auth_exception_handler(request: Request, exc: AjaxAuthError):
    """Handle Ajax authentication failures specifically."""
    logger.warning(f"Ajax Auth Failure: {exc}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Upstream authentication failure. Please check your Ajax credentials."}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Final fallback to prevent leaking technical details."""
    logger.exception(f"Unhandled exception at {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )

# CORS Configuration (Must be LAST to be the outermost middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
import time
import uuid
from fastapi import Request
from backend.app.shared.infrastructure.database.session import async_session_factory
from backend.app.modules.security import service as security_service


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    Injects security headers recommended by OWASP 2025:
    - Content-Security-Policy (CSP)
    - Strict-Transport-Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
    """
    response = await call_next(request)
    
    # Prevents Clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevents MIME-sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Controls how much referrer information is sent
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Enforces HTTPS
    # Only meaningful on HTTPS deployments
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Basic CSP - Restrictive by default
    # Note: Swagger UI and Redoc require jsdelivr for assets by default in FastAPI
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "frame-ancestors 'none';"
    )
    
    return response

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """
    Middleware to automatically audit all mutations (POST, PUT, PATCH, DELETE).
    """
    # Track correlation ID and start time for audit
    import uuid
    import time
    from backend.app.core.config import settings
    
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()
    
    # Store in request state for later retrieval in routes if needed
    request.state.correlation_id = correlation_id
    
    response = None
    try:
        response = await call_next(request)
        
        # Only audit mutations for API routes
        if request.scope['path'].startswith(settings.API_V1_STR) and request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Only audit successful or client-error attempts that reach routes
            if response.status_code < 500:
                from backend.app.modules.security.service import log_request_action
                from backend.app.shared.infrastructure.database.session import async_session_factory
                
                # Check for user_id in request state (if set by auth)
                user_id = getattr(request.state, "user_id", None)
                
                # We use a background task or a separate session to avoid blocking the main request
                # For this implementation, we use a separate session
                try:
                    # Defensive check for status_code to prevent RecursionError with mocks in tests
                    raw_status = getattr(response, "status_code", 500)
                    if hasattr(raw_status, "__call__") or not isinstance(raw_status, (int, float)):
                        status_code = 500
                    else:
                        status_code = int(raw_status)

                    async with async_session_factory() as db:
                        await log_request_action(
                            db=db,
                            request=request, 
                            user_id=user_id,
                            action=f"Mutation: {request.url.path}",
                            status_code=status_code
                        )
                except Exception as audit_err:
                    logger.error(f"Audit log failure: {str(audit_err)}")
        
        # Calculate latency and add correlation ID header
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-Latency-ms"] = str(latency_ms)
        
        return response
    except Exception as e:
        logger.error(f"Audit middleware crash: {str(e)}")
        if response:
            return response
        raise e
        
# Include modular router
app.include_router(modular_router, prefix=settings.API_V1_STR)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    try:
        # Enhanced API description with documentation links
        enhanced_description = """
## AjaxSecurFlow Proxy API

An advanced, secure proxy for Ajax Systems API with tiered subscription plans.

    
### Subscription Plans

| Plan | Access Level |
|------|---------------|
| **Free** | Hub listing only |
| **Basic** | Free + Devices, Rooms, Groups, Logs |
| **Pro** | Basic + Commands (arm/disarm) |
| **Premium** | Pro + Full API proxy |

### Authentication

All endpoints require authentication via Bearer token:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Get your token from `POST /auth/token`

### Documentation

- [API Permissions](https://github.com/virapa/AjaxSecurFlow/blob/main/backend/docs/API_PERMISSIONS.md) - Detailed permission matrix
- [Plan Migration Guide](https://github.com/virapa/AjaxSecurFlow/blob/main/backend/docs/PLAN_MIGRATION_GUIDE.md) - Upgrading/downgrading plans
- [Integration Examples](https://github.com/virapa/AjaxSecurFlow/blob/main/backend/docs/INTEGRATION_EXAMPLES.md) - Code samples
- [Frontend Integration](https://github.com/virapa/AjaxSecurFlow/blob/main/frontend/docs/FRONTEND_INTEGRATION.md) - React integration guide
        """
        
        # Generate the base schema with enhanced description
        openapi_schema = get_openapi(
            title="AjaxSecurFlow Proxy API",
            version="1.0.0",
            description=enhanced_description,
            routes=app.routes,
        )
        
        # Add security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token obtained from /auth/token endpoint. Example: `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`"
            }
        }
        
        # Add global security requirement
        openapi_schema["security"] = [{"BearerAuth": []}]
        
        # Enhanced server definitions
        openapi_schema["servers"] = [
            {
                "url": settings.API_V1_STR,
                "description": "Production environment"
            }
        ]
        
        # Add contact and license information
        openapi_schema["info"]["contact"] = {
            "name": "AjaxSecurFlow Support",
            "email": "support@ajaxsecurflow.com",
            "url": "https://www.ajaxsecurflow.com"
        }
        
        openapi_schema["info"]["license"] = {
            "name": "Proprietary",
            "url": "https://ajaxsecurflow.com/terms"
        }
        
        # VISUAL CLEANUP: Strip /api/v1 from the paths displayed in Swagger
        new_paths = {}
        for path, methods in openapi_schema["paths"].items():
            if path.startswith(settings.API_V1_STR):
                clean_path = path.replace(settings.API_V1_STR, "", 1)
                if not clean_path.startswith("/"):
                    clean_path = "/" + clean_path
                new_paths[clean_path] = methods
            else:
                new_paths[path] = methods
        
        openapi_schema["paths"] = new_paths
        
        # Add custom extensions to endpoints (plan requirements and rate limits)
        # This is a foundation - specific endpoint annotations should be added in routers
        for path, path_item in openapi_schema["paths"].items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    operation = path_item[method]
                    
                    # Add plan requirement based on path patterns
                    if "/ajax/" in path:
                        if "/devices" in path or "/rooms" in path or "/groups" in path or "/logs" in path:
                            operation["x-required-plan"] = "basic"
                        elif "/arm-state" in path:
                            operation["x-required-plan"] = "pro"
                        elif path == "/ajax" or "hubs" in path:
                            operation["x-required-plan"] = "free"
        
        # Add tags metadata to differentiate Ajax API from Ajax Systems Proxy
        openapi_schema["tags"] = [
            {
                "name": "AjaxSecurFlow API",
                "description": """
**Structured Ajax Systems endpoints** with plan-based access control.

These endpoints provide access to specific Ajax resources (hubs, devices, rooms, groups, logs, commands) with granular permissions based on your subscription plan.

**Access Levels:**
- **Free**: Hubs only
- **Basic**: Free + Devices, Rooms, Groups, Logs
- **Pro**: Basic + Commands (arm/disarm)
- **Premium**: Pro + Full API Proxy

All endpoints in this section are explicitly defined and documented.
                """
            },
            {
                "name": "Ajax Systems Proxy",
                "description": """
**🔒 PREMIUM ONLY** - Full Ajax API proxy with unrestricted access.

This is a **catch-all proxy** that forwards ALL HTTP methods (GET, POST, PUT, DELETE, PATCH) directly to the Ajax Systems API. It allows you to access **any Ajax endpoint** not explicitly defined in the "AjaxSecurFlow API" section above.

**Required Plan**: Premium

**How it works:**
- Any request to `/ajax/{path}` that doesn't match an explicit endpoint is proxied
- Supports all HTTP methods
- Forwards request body and headers
- Returns raw Ajax API responses

**Example:**
```bash
# Access any custom Ajax endpoint
GET /ajax/custom/endpoint/path
POST /ajax/user/12345/custom-action
```

**Note**: The proxy endpoints are not shown in this Swagger UI because they are dynamic catch-all routes. Refer to the [Ajax Systems API documentation](https://ajax.systems/api) for available endpoints.
                """
            },
            {
                "name": "Authentication",
                "description": "User authentication and token management endpoints."
            }
        ]
        
        app.openapi_schema = openapi_schema
        logger.info("OpenAPI schema generated successfully with enhanced documentation.")
        return app.openapi_schema
    except Exception as e:
        logger.error(f"Error generating OpenAPI schema: {e}")
        # Return fallback default schema if custom logic fails
        return get_openapi(
            title="AjaxSecurFlow Proxy API (Fallback)",
            version="1.0.0",
            routes=app.routes
        )

app.openapi = custom_openapi

@app.get("/health", tags=["System"], include_in_schema=False)
async def health_check():
    """
    Service health check endpoint for monitoring systems.
    """
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    """
    API Root endpoint.
    """
    return {"message": "AjaxSecurFlow Proxy API is running"}
