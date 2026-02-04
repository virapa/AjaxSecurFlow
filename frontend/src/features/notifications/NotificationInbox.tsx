'use client'

import React, { useEffect, useState } from 'react'
import { Card } from '@/shared/components/Card'
import { notificationService, Notification } from './notification.service'

import { es as t } from '@/shared/i18n/es'

/**
 * NotificationInbox Component (Local Scope: Notifications)
 * Displays a list of user alerts and messages.
 */
export const NotificationInbox: React.FC = () => {
    const [notifications, setNotifications] = useState<Notification[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const fetchNotifications = async () => {
            try {
                setIsLoading(true)
                const data = await notificationService.getNotifications()
                setNotifications(data)
            } catch (err: any) {
                setError(err.message || t.dashboard.stats.systemDegraded)
            } finally {
                setIsLoading(false)
            }
        }

        fetchNotifications()
    }, [])

    if (isLoading) {
        return (
            <div className="flex justify-center p-12">
                <p className="text-gray-500 animate-pulse text-[10px] font-bold uppercase tracking-widest">{t.common.loading}</p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-10 bg-red-500/5 border border-red-500/20 rounded-3xl text-red-400 text-center">
                <p className="text-xs font-bold">{error}</p>
            </div>
        )
    }

    if (notifications.length === 0) {
        return (
            <Card className="text-center p-12">
                <p className="text-gray-500">{t.dashboard.notifications.empty}</p>
            </Card>
        )
    }

    return (
        <div className="space-y-4">
            {notifications.map((notification) => (
                <Card
                    key={notification.id}
                    className={`relative overflow-hidden ${!notification.is_read ? 'border-l-4 border-l-blue-500' : ''}`}
                >
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className={`font-semibold ${!notification.is_read ? 'text-gray-900 dark:text-white' : 'text-gray-500'}`}>
                                {notification.title}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                {notification.message}
                            </p>
                        </div>
                        <span className="text-xs text-gray-400">
                            {new Date(notification.created_at).toLocaleDateString()}
                        </span>
                    </div>
                </Card>
            ))}
        </div>
    )
}
