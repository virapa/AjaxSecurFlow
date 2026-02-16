import { User, Hub, Device, LogEntry } from '@/shared/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL
const API_VERSION = '/api/v1'

if (!BASE_URL) {
    console.warn('⚠️ NEXT_PUBLIC_API_URL is not defined in environment variables. API requests may fail.')
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${API_VERSION}${endpoint}`

    console.log(`[API] Requesting: ${endpoint} (${options.method})`)

    // Token management is now handled by HTTPOnly cookies.
    // No need to manually inject the Authorization header for the Dashboard.
    // However, we keep the header injection IF a token is found in localStorage 
    // to maintain compatibility during the transition or for specific use cases.
    let token = null
    if (typeof window !== 'undefined') {
        token = localStorage.getItem('ajax_access_token')
    }

    const defaultHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
    }

    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`
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

        // Special handling for Logout: clear state regardless of outcome
        if (endpoint === '/auth/logout' && typeof window !== 'undefined') {
            console.log('[API] Clearing local auth state (Logout)')
            localStorage.removeItem('ajax_access_token')
            // Cookies will be cleared by the backend response
        }

        if (!response.ok) {
            console.error(`[API] Request failed with status ${response.status} at ${endpoint}`)
            // If 401, clear local state. Cookies should be cleared by backend if possible,
            // but we can also trigger a manual logout or redirect.
            if (response.status === 401 && typeof window !== 'undefined') {
                localStorage.removeItem('ajax_access_token')
            }

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

            const error = new Error(errorMessage);
            (error as any).status = response.status;
            throw error;
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
