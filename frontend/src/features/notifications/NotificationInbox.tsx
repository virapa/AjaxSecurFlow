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

    const fetchNotifications = async () => {
        try {
            setIsLoading(true)
            const data = await notificationService.getNotifications()
            setNotifications(data)
        } catch (err: unknown) {
            const error = err as Error
            setError(error.message || t.dashboard.stats.systemDegraded)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchNotifications()
    }, [])

    const handleMarkAsRead = async (id: string, isAlreadyRead: boolean) => {
        if (isAlreadyRead) return
        try {
            await notificationService.markAsRead(id)
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
        } catch (err) {
            console.error('Failed to mark as read:', err)
        }
    }

    const handleMarkAllRead = async () => {
        try {
            await notificationService.markAllAsRead()
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
        } catch (err) {
            console.error('Failed to mark all as read:', err)
        }
    }

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
            <div className="flex justify-end mb-4">
                <button
                    onClick={handleMarkAllRead}
                    className="text-[10px] font-black uppercase tracking-widest text-cyan-500 hover:text-cyan-400 transition-colors"
                >
                    Marcar todo como leído
                </button>
            </div>
            {notifications.map((notification) => (
                <div
                    key={notification.id}
                    onClick={() => handleMarkAsRead(notification.id, notification.is_read)}
                    className="cursor-pointer"
                >
                    <Card
                        className={`relative overflow-hidden transition-all hover:bg-white/[0.04] ${!notification.is_read ? 'border-l-4 border-l-cyan-500 bg-cyan-500/5' : 'opacity-60'}`}
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
                            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tight">
                                {new Date(notification.created_at).toLocaleString(undefined, {
                                    day: '2-digit',
                                    month: '2-digit',
                                    year: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </span>
                        </div>
                    </Card>
                </div>
            ))}
        </div>
    )
}
