import { apiClient } from '@/infrastructure/api-client'

export interface ApiToken {
    id: number
    name: string
    prefix: string
    last_used_at?: string | null
    expires_at?: string | null
    created_at: string
}

export interface ApiTokenCreated extends ApiToken {
    /** Raw token. Returned only once by the backend. */
    token: string
}

/**
 * Integration Tokens Service (Local Scope: features/integrations)
 * Long-lived tokens used by external clients such as the Home Assistant integration.
 */
export const apiTokenService = {
    list: (): Promise<ApiToken[]> => apiClient.get<ApiToken[]>('/auth/api-tokens'),
    create: (name: string): Promise<ApiTokenCreated> => apiClient.post<ApiTokenCreated>('/auth/api-tokens', { name }),
    revoke: (id: number): Promise<void> => apiClient.delete<void>(`/auth/api-tokens/${id}`),
}
