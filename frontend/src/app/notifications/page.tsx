'use client'

import React from 'react'
import { Sidebar } from '@/features/navigation/Sidebar'
import { DashboardHeader } from '@/features/navigation/DashboardHeader'
import { NotificationInbox } from '@/features/notifications/NotificationInbox'
import { es as t } from '@/shared/i18n/es'
import { authService } from '@/features/auth/auth.service'
import { notificationService } from '@/features/notifications/notification.service'

export default function NotificationsPage() {
    const [user, setUser] = React.useState<any>(null)
    const [unreadCount, setUnreadCount] = React.useState(0)

    React.useEffect(() => {
        const load = async () => {
            try {
                const [profile, summary] = await Promise.all([
                    authService.getProfile(),
                    notificationService.getSummary()
                ])
                setUser(profile)
                setUnreadCount(summary.unread_count)
            } catch (err) {
                console.error('Failed to load notifications data:', err)
            }
        }
        load()
    }, [])

    return (
        <div className="min-h-screen bg-[#020617] text-white flex font-sans selection:bg-blue-500/30">
            <Sidebar />

            <main className="flex-1 bg-[#020617]">
                <DashboardHeader
                    title={t.dashboard.nav.notifications}
                    user={user}
                    unreadNotificationsCount={unreadCount}
                />

                <div className="p-10 max-w-[1000px] mx-auto">
                    <div className="mb-10">
                        <h2 className="text-3xl font-black tracking-tight mb-2">{t.dashboard.nav.notifications}</h2>
                        <p className="text-gray-500 text-sm">{t.dashboard.billing.description}</p>
                    </div>

                    <NotificationInbox />
                </div>
            </main>
        </div>
    )
}
