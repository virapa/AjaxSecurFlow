from fastapi import HTTPException
import httpx
from backend.app.services.ajax_client import AjaxAuthError

def handle_ajax_error(e: Exception) -> None:
    """
    Standardize exception handling for Ajax API calls.
    Prevents leaking internal upstream URLs or session details.
    """
    if isinstance(e, AjaxAuthError):
        # Keep it consistent with authentication hardening
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if isinstance(e, httpx.HTTPStatusError):
        status_code = e.response.status_code
        # Map critical errors to user-friendly but non-revealing messages
        if status_code == 404:
            raise HTTPException(status_code=404, detail="The requested resource was not found on the security system.")
        if status_code == 403:
            raise HTTPException(status_code=403, detail="Access denied to this security resource.")
        if status_code == 405:
            raise HTTPException(status_code=405, detail="The security system does not support this type of action (Method Not Allowed).")
        
        # Generic fallback for other status codes
        raise HTTPException(status_code=502, detail="Upstream security service error.")
        
    # Catch-all for connection errors, timeouts, etc.
    raise HTTPException(status_code=502, detail="Communication failure with the security provider.")
