import { User, Hub, Device, LogEntry } from '@/shared/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL
const API_VERSION = '/api/v1'

if (!BASE_URL) {
    console.warn('⚠️ NEXT_PUBLIC_API_URL is not defined in environment variables. API requests may fail.')
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${API_VERSION}${endpoint}`

    console.log(`[API] Requesting: ${endpoint} (${options.method})`)

    // Get token from storage (client-side only)
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
            credentials: 'include',
        })

        console.log(`[API] Response status: ${response.status} for ${endpoint}`)

        // Special handling for Logout: clear state regardless of outcome
        if (endpoint === '/auth/logout' && typeof window !== 'undefined') {
            console.log('[API] Clearing local auth state (Logout)')
            localStorage.removeItem('ajax_access_token')
            document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT'
        }

        if (!response.ok) {
            console.error(`[API] Request failed with status ${response.status} at ${endpoint}`)
            // If 401, clear token and redirect (standard security)
            if (response.status === 401 && typeof window !== 'undefined') {
                localStorage.removeItem('ajax_access_token')
                document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT'
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

        // If we are logging in, store the token
        if (endpoint === '/auth/token' && (data as { access_token?: string }).access_token && typeof window !== 'undefined') {
            const newToken = (data as { access_token: string }).access_token
            console.log('[API] Login detected, saving token...')
            localStorage.setItem('ajax_access_token', newToken)
            // Set cookie so middleware can see it
            document.cookie = `access_token=${newToken}; path=/; max-age=3600; SameSite=Lax`
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
