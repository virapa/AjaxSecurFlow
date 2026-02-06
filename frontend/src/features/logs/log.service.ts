import { apiClient } from '@/infrastructure/api-client'

export interface EventLog {
    id: string
    hub_id: string
    timestamp: string
    event_code: string
    event_desc: string
    user_name?: string
    device_name?: string
    transition?: string
}

export interface EventLogResponse {
    logs: EventLog[]
    total_count: number
}

/**
 * Log Service (Local Scope: features/logs)
 */
export const logService = {
    /**
     * Fetches event logs for a specific hub.
     */
    getHubLogs: async (hubId: string, limit: number = 20): Promise<EventLogResponse> => {
        return apiClient.get<EventLogResponse>(`/ajax/hubs/${hubId}/logs?limit=${limit}`)
    }
}
