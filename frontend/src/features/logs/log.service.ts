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
    media_urls?: string[]
}

export interface EventLogResponse {
    logs: EventLog[]
    total_count: number
}

export interface SQSEvent {
    id: number
    event_type: string
    hub_id: string
    received_at?: string
    processed_at?: string
}

export interface SQSEventListResponse {
    events: SQSEvent[]
    total_count: number
}

export interface SyncLogsResponse {
    success: boolean
    imported_count: number
    message: string
}

export interface HybridEvent {
    id: string
    hub_id: string
    event_type: string
    title: string
    description: string
    severity: 'critical' | 'warning' | 'info' | 'success' | string
    timestamp: string
    media_urls?: string[]
    source: string
    data?: any
}

/**
 * Log Service (Local Scope: features/logs)
 */
export const logService = {
    /**
     * Fetches event logs for a specific hub (served from local DB).
     */
    getHubLogs: async (hubId: string, limit: number = 20): Promise<EventLogResponse> => {
        return apiClient.get<EventLogResponse>(`/ajax/hubs/${hubId}/logs?limit=${limit}`)
    },

    /**
     * Explicit backup sync: fetches historical logs from Ajax Systems API.
     */
    syncRemoteLogs: async (hubId: string, limit: number = 50): Promise<SyncLogsResponse> => {
        return apiClient.post<SyncLogsResponse>(`/ajax/hubs/${hubId}/logs/sync?limit=${limit}`, {})
    },

    /**
     * Fetches the stored SQS event history for a specific hub (newest first).
     */
    getHubSqsEvents: async (hubId: string, limit: number = 20, offset: number = 0): Promise<SQSEventListResponse> => {
        return apiClient.get<SQSEventListResponse>(`/ajax/hubs/${hubId}/events?limit=${limit}&offset=${offset}`)
    },

    /**
     * Subscribes to real-time Server-Sent Events (SSE).
     * Returns an unsubscribe cleanup function.
     */
    subscribeToEventStream: (
        onEvent: (event: HybridEvent) => void,
        onError?: (error: any) => void
    ): (() => void) => {
        if (typeof window === 'undefined') return () => {}

        const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
        const url = `${baseUrl}/api/v1/ajax/events/stream`

        const eventSource = new EventSource(url, { withCredentials: true })

        eventSource.addEventListener('ajax_event', (e: MessageEvent) => {
            try {
                const parsed = JSON.parse(e.data) as HybridEvent
                onEvent(parsed)
            } catch (err) {
                console.error('[SSE] Failed to parse event data:', err)
            }
        })

        eventSource.onerror = (err) => {
            if (onError) onError(err)
        }

        return () => {
            eventSource.close()
        }
    }
}
