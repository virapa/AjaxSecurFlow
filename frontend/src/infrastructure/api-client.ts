import { User, Hub, Device, LogEntry } from '@/shared/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL
const API_VERSION = '/api/v1'
// Pre-cookie dashboards stored the JWT here; it is only purged now.
const LEGACY_TOKEN_KEY = 'ajax_access_token'

if (!BASE_URL) {
    console.warn('⚠️ NEXT_PUBLIC_API_URL is not defined in environment variables. API requests may fail.')
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${API_VERSION}${endpoint}`

    console.log(`[API] Requesting: ${endpoint} (${options.method})`)

    // Auth is handled exclusively by HttpOnly cookies. Never send a token from
    // localStorage: the backend prefers the Authorization header over the cookie,
    // so a stale legacy token would cause 401s right after a valid login.
    if (typeof window !== 'undefined') {
        localStorage.removeItem(LEGACY_TOKEN_KEY)
    }

    const defaultHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
            credentials: 'include', // CRITICAL: This allows sending/receiving cookies
        })

        console.log(`[API] Response status: ${response.status} for ${endpoint}`)

        if (!response.ok) {
            console.error(`[API] Request failed with status ${response.status} at ${endpoint}`)

            // Try to extract error detail from response body
            let errorMessage = `API Error: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch {
                // If JSON parsing fails, use the default message
            }

            const error = new Error(errorMessage) as Error & { status?: number };
            error.status = response.status;
            throw error;
        }

        // 204 No Content (e.g. DELETE) has no body; parsing it would throw.
        if (response.status === 204) {
            return undefined as T
        }

        const data = await response.json()
        console.log(`[API] Success: data received for ${endpoint}`)

        // If we are logging in, we still get the token in JSON for 3rd party compatibility,
        // but the Dashboard relies on the Set-Cookie header which is handled by the browser.
        if (endpoint === '/auth/token' && (data as { access_token?: string }).access_token && typeof window !== 'undefined') {
            console.log('[API] Login detected. Backend issued HTTPOnly cookies.')
            // Optional: Keep localStorage for transition or legacy parts of the dashboard
            // localStorage.setItem('ajax_access_token', data.access_token)
        }

        return data
    } catch (error) {
        console.error(`[API] Error during fetch for ${endpoint}:`, error)
        throw error
    }
}

export const apiClient = {
    get: <T>(endpoint: string, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'GET' }),

    post: <T>(endpoint: string, body: unknown, options?: RequestInit) =>
        request<T>(endpoint, {
            ...options,
            method: 'POST',
            body: JSON.stringify(body)
        }),

    put: <T>(endpoint: string, body: unknown, options?: RequestInit) =>
        request<T>(endpoint, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(body)
        }),

    patch: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
        request<T>(endpoint, {
            ...options,
            method: 'PATCH',
            body: body ? JSON.stringify(body) : undefined
        }),

    delete: <T>(endpoint: string, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'DELETE' }),
}
