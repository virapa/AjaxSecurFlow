'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { Sidebar } from '@/features/navigation/Sidebar'
import { authService } from '@/features/auth/auth.service'
import { notificationService } from '@/features/notifications/notification.service'
import { es as t } from '@/shared/i18n/es'

export const ProfileComponent: React.FC = () => {
    const [user, setUser] = useState<any>(null)
    const [unreadNotificationsCount, setUnreadNotificationsCount] = useState<number>(0)
    const [emailNotifications, setEmailNotifications] = useState(true)
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)
    const [showSuccess, setShowSuccess] = useState(false)

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const [profile, notifSummary] = await Promise.all([
                    authService.getProfile(),
                    notificationService.getSummary()
                ])
                setUser(profile)
                setUnreadNotificationsCount(notifSummary.unread_count)
                // Mocking notification preference for now
                setEmailNotifications(true)
            } catch (err) {
                console.error('Failed to fetch profile:', err)
            } finally {
                setIsLoading(false)
            }
        }
        fetchProfile()
    }, [])

    const handleSave = async () => {
        setIsSaving(true)
        // Mocking save delay
        await new Promise(resolve => setTimeout(resolve, 800))
        setIsSaving(false)
        setShowSuccess(true)
        setTimeout(() => setShowSuccess(false), 3000)
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-[#020617] flex items-center justify-center">
                <div className="h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-[#020617] text-white flex font-sans selection:bg-blue-500/30">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 bg-[#020617] overflow-y-auto">
                <header className="h-20 border-b border-white/5 px-10 flex items-center justify-between sticky top-0 z-30 bg-[#020617]/80 backdrop-blur-xl">
                    <h2 className="text-lg font-bold tracking-tight">{t.dashboard.profilePage.title}</h2>
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <p className="text-xs font-bold text-white">{user?.ajax_info?.login}</p>
                            <div className="relative">
                                <span className="text-sm text-gray-500">🔔</span>
                                {unreadNotificationsCount > 0 && (
                                    <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-600 border border-[#020617] flex items-center justify-center text-[7px] font-bold text-white">
                                        {unreadNotificationsCount}
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10 flex items-center justify-center text-xs shadow-lg overflow-hidden">
                            {user?.ajax_info?.imageUrls?.small ? (
                                <img src={user.ajax_info.imageUrls.small} alt="Profile" className="w-full h-full object-cover" />
                            ) : (
                                '👤'
                            )}
                        </div>
                    </div>
                </header>

                <div className="p-10 max-w-4xl mx-auto space-y-10">
                    {/* Hero Section */}
                    <div className="relative px-8 py-10 rounded-[2.5rem] bg-gradient-to-br from-[#1e293b] to-[#0f172a] border border-white/5 overflow-hidden">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-[80px] -mr-32 -mt-32"></div>
                        <div className="relative flex flex-col md:flex-row items-center gap-8">
                            <div className="h-24 w-24 rounded-3xl bg-blue-600/20 border border-blue-500/20 flex items-center justify-center text-4xl shadow-2xl">
                                {user?.ajax_info?.imageUrls?.medium ? (
                                    <img src={user.ajax_info.imageUrls.medium} alt="Profile" className="w-full h-full object-cover rounded-2xl" />
                                ) : (
                                    '👤'
                                )}
                            </div>
                            <div className="text-center md:text-left space-y-2">
                                <h1 className="text-3xl font-black tracking-tight text-white uppercase italic">
                                    {user?.ajax_info?.firstName} {user?.ajax_info?.lastName}
                                </h1>
                                <p className="text-xs font-bold tracking-[0.2em] text-blue-400 uppercase opacity-80">
                                    {t.dashboard.profile.role}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Personal Info */}
                        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-8 space-y-6">
                            <h3 className="text-sm font-black uppercase tracking-widest text-white mb-2">{t.dashboard.profilePage.personalInfo}</h3>
                            <div className="space-y-4">
                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.profilePage.labels.firstName}</label>
                                    <div className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-medium">
                                        {user?.ajax_info?.firstName || '—'}
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.profilePage.labels.lastName}</label>
                                    <div className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-medium">
                                        {user?.ajax_info?.lastName || '—'}
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.profilePage.labels.email}</label>
                                    <div className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-medium">
                                        {user?.ajax_info?.login || '—'}
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.profilePage.labels.phone}</label>
                                    <div className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-medium">
                                        {user?.ajax_info?.phone || '—'}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Settings */}
                        <div className="space-y-8">
                            <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-8 space-y-6">
                                <h3 className="text-sm font-black uppercase tracking-widest text-white mb-2">{t.dashboard.profilePage.notifications}</h3>
                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
                                    <div className="space-y-1">
                                        <p className="text-xs font-bold text-white uppercase tracking-tight">{t.dashboard.profilePage.emailNotifications}</p>
                                        <p className="text-[10px] text-gray-500 leading-tight pr-4">
                                            {t.dashboard.profilePage.emailDescription}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => setEmailNotifications(!emailNotifications)}
                                        className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors duration-200 outline-none ${emailNotifications ? 'bg-blue-600' : 'bg-gray-700'}`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ${emailNotifications ? 'translate-x-[24px]' : 'translate-x-[4px]'}`} />
                                    </button>
                                </div>
                            </div>

                            <div className="flex flex-col gap-4">
                                <button
                                    onClick={handleSave}
                                    disabled={isSaving}
                                    className={`w-full py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-sm font-black uppercase tracking-widest text-white transition-all shadow-xl shadow-blue-500/20 active:scale-[0.98] ${isSaving ? 'opacity-70 cursor-not-allowed text-transparent' : ''}`}
                                >
                                    {isSaving ? '' : t.dashboard.profilePage.saveChanges}
                                    {isSaving && (
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        </div>
                                    )}
                                </button>

                                {showSuccess && (
                                    <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-bold text-center animate-in slide-in-from-top-2 duration-300">
                                        ✅ {t.dashboard.profilePage.success}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}
