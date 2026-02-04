import { apiClient } from '@/infrastructure/api-client'

export interface Notification {
    id: string
    title: string
    message: string
    notification_type: 'info' | 'success' | 'warning' | 'security'
    is_read: boolean
    created_at: string
}

/**
 * Notification Service (Local Scope: features/notifications)
 */
export const notificationService = {
    /**
     * Fetches the user's notifications.
     */
    getNotifications: async (unreadOnly: boolean = false, limit: number = 20): Promise<Notification[]> => {
        return apiClient.get<Notification[]>(`/notifications?unread_only=${unreadOnly}&limit=${limit}`)
    },

    /**
     * Marks a single notification as read.
     */
    markAsRead: async (notificationId: string): Promise<{ status: string }> => {
        return apiClient.patch<{ status: string }>(`/notifications/${notificationId}/read`)
    },

    /**
     * Marks all notifications as read.
     */
    markAllAsRead: async (): Promise<{ status: string; marked_read: number }> => {
        return apiClient.post<{ status: string; marked_read: number }>('/notifications/mark-all-read', {})
    }
}
