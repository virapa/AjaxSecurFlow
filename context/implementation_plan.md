# Auth Refinement & Frontend Dashboard

This plan covers the transition from standard header-based JWT authentication to a more secure **HTTPOnly Cookies** strategy for the new Frontend Dashboard.

## Proposed Changes

### [Component] Backend Authentication Refinement
Currently, the backend returns tokens in the JSON response body. To improve security for the Frontend, we will transition to using cookies.

#### [MODIFY] [auth.py](file:///c:/Users/rpalacios.SATYATEC/APPs/git-proyects/AjaxSecurFlow/backend/app/api/v1/auth.py)
- Update `login_for_access_token` to set `access_token` and `refresh_token` as HTTPOnly, Secure, and SameSite=Lax cookies.
- Update `logout` to clear these cookies.
- Update `refresh_token` to read from and update cookies.
- Update `get_current_user` dependency to check cookies if the Authorization header is missing.

### [Component] Frontend Dashboard (Next.js) [NEW]
We will initialize a modern, high-performance Dashboard using Next.js.

#### [NEW] [frontend/](file:///c:/Users/rpalacios.SATYATEC/APPs/git-proyects/AjaxSecurFlow/frontend)
- **Framework**: Next.js 14+ (App Router).
- **Styling**: Vanilla CSS (or Tailwind if requested, but default is Vanilla for this project specialized look).
- **Auth Integration**: Automatically handle cookie-based sessions.

## User Review Required

> [!IMPORTANT]
> **Why HTTPOnly Cookies?**
> Standard tokens in headers (LocalStorage) are vulnerable to XSS. By using HTTPOnly cookies, the browser handles the tokens automatically and JavaScript cannot access them, making it significantly more secure.

> [!IMPORTANT]
> **Retrocompatibilidad Garantizada**
> Este plan **NO romperá** tus aplicaciones de terceros. La lógica de autenticación funcionará así:
> 1.  **Prioridad Header**: Primero se busca el token en el header `Authorization`. Si el script o app externa lo envía, se valida y entra.
> 2.  **Fallback Cookies**: Si el header no existe (caso del navegador/dashboard), se buscan las Cookies.
> 3.  **Resultado**: Tus apps actuales siguen funcionando igual, mientras que el nuevo Dashboard disfruta de la seguridad extra de las Cookies.

Por favor, confirma si podemos proceder con este enfoque **Híbrido (Cookies + Headers)**.
