'use client'

import React, { useEffect, useState } from 'react'
import { logService, EventLog, HybridEvent } from './log.service'
import { es as t } from '@/shared/i18n/es'
import { canAccessFeature, SubscriptionPlan } from '@/shared/utils/permissions'

interface EventFeedProps {
    hubId?: string
    role?: 'MASTER' | 'PRO' | 'USER'
    userPlan?: SubscriptionPlan
}

const PhotoViewer: React.FC<{ urls: string[] }> = ({ urls }) => {
    const [index, setIndex] = useState(0)
    const [hasError, setHasError] = useState(false)

    if (!urls || urls.length === 0) return null

    const currentUrl = urls[index]

    return (
        <div className="mt-3 rounded-2xl border border-white/10 bg-black/50 p-2 overflow-hidden backdrop-blur-sm">
            <div className="relative aspect-video rounded-xl overflow-hidden bg-black flex items-center justify-center">
                {hasError ? (
                    <div className="text-gray-500 text-[10px] flex flex-col items-center gap-1 font-mono">
                        <span>⚠️ Enlace caducado o no disponible</span>
                    </div>
                ) : (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                        src={currentUrl}
                        alt={`Fotoverificación ${index + 1}`}
                        onError={() => setHasError(true)}
                        className="w-full h-full object-contain"
                    />
                )}

                {/* Badge con contador de fotos */}
                <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-black/70 border border-white/10 text-white text-[9px] font-mono font-bold tracking-wider flex items-center gap-1">
                    <span>📷</span>
                    <span>{index + 1}/{urls.length}</span>
                </div>

                {/* Controles si hay más de 1 foto */}
                {urls.length > 1 && (
                    <div className="absolute bottom-2 inset-x-2 flex justify-between items-center px-1">
                        <button
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation()
                                setIndex((prev) => (prev > 0 ? prev - 1 : urls.length - 1))
                                setHasError(false)
                            }}
                            className="h-6 w-6 rounded-full bg-black/70 hover:bg-white/20 text-white flex items-center justify-center text-xs transition-all border border-white/10"
                        >
                            ‹
                        </button>
                        <div className="flex gap-1">
                            {urls.map((_, i) => (
                                <button
                                    key={i}
                                    type="button"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        setIndex(i)
                                        setHasError(false)
                                    }}
                                    className={`h-1.5 rounded-full transition-all ${i === index ? 'w-4 bg-cyan-400' : 'w-1.5 bg-white/30 hover:bg-white/60'}`}
                                />
                            ))}
                        </div>
                        <button
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation()
                                setIndex((prev) => (prev < urls.length - 1 ? prev + 1 : 0))
                                setHasError(false)
                            }}
                            className="h-6 w-6 rounded-full bg-black/70 hover:bg-white/20 text-white flex items-center justify-center text-xs transition-all border border-white/10"
                        >
                            ›
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

export const EventFeed: React.FC<EventFeedProps> = ({ hubId, role, userPlan = 'basic' }) => {
    const [logs, setLogs] = useState<EventLog[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [mounted, setMounted] = useState(false)
    const [isSyncing, setIsSyncing] = useState(false)
    const [syncMessage, setSyncMessage] = useState<string | null>(null)

    const isPro = role === 'MASTER'
    const canViewEvents = canAccessFeature(userPlan, 'read_logs')

    // Helper to translate/refine event descriptions
    const getEventDescription = (log: EventLog): string => {
        const desc = log.event_desc || ''

        // Try direct lookup in translations
        // @ts-ignore - Dynamic key lookup
        const translated = t.logEvents[desc]
        if (translated) return translated

        // Check for transition-based bypass events
        if (desc.includes('TamperBypassOn') || desc.includes('BypassOn')) {
            if (log.transition === 'RECOVERED') {
                return 'Restablecimiento de anulación'
            }
            // Covers TRIGGERED or undefined
            return 'Anulación'
        }
        return desc
    }

    // Initial local DB fetch
    useEffect(() => {
        setMounted(true)
        if (!hubId) {
            setLogs([])
            setIsLoading(false)
            return
        }

        const fetchLogs = async () => {
            try {
                const response = await logService.getHubLogs(hubId, 20)
                if (!response) {
                    setLogs([])
                    return
                }

                // Support both legacy list and new wrapped object
                const logsData = Array.isArray(response) ? response : (response.logs || [])
                setLogs(logsData)
            } catch (err: unknown) {
                console.error('[EventFeed] Error fetching logs:', err)
                setLogs([])
            } finally {
                setIsLoading(false)
            }
        }

        fetchLogs()
    }, [hubId])

    // Real-time SSE listener
    useEffect(() => {
        if (!hubId) return

        const unsubscribe = logService.subscribeToEventStream(
            (newEvent: HybridEvent) => {
                if (newEvent.hub_id === hubId) {
                    const incomingLog: EventLog = {
                        id: newEvent.id,
                        hub_id: newEvent.hub_id,
                        timestamp: newEvent.timestamp,
                        event_code: newEvent.event_type,
                        event_desc: newEvent.description || newEvent.title,
                        user_name: newEvent.data?.event?.sourceObjectName || newEvent.data?.recipient?.name,
                        device_name: newEvent.data?.event?.deviceName || newEvent.data?.event?.tag,
                        transition: newEvent.data?.event?.transition,
                        media_urls: newEvent.media_urls || []
                    }

                    setLogs(prev => {
                        if (prev.some(l => l.id === incomingLog.id)) return prev
                        return [incomingLog, ...prev.slice(0, 19)]
                    })
                }
            },
            (err) => {
                console.warn('[EventFeed] SSE connection notice:', err)
            }
        )

        return () => {
            unsubscribe()
        }
    }, [hubId])

    const handleSyncBackup = async () => {
        if (!hubId || isSyncing) return
        setIsSyncing(true)
        setSyncMessage(null)
        try {
            const res = await logService.syncRemoteLogs(hubId, 50)
            setSyncMessage(`+${res.imported_count} importados`)
            const refreshed = await logService.getHubLogs(hubId, 20)
            if (refreshed) {
                const logsData = Array.isArray(refreshed) ? refreshed : (refreshed.logs || [])
                setLogs(logsData)
            }
            setTimeout(() => setSyncMessage(null), 4000)
        } catch (err) {
            console.error('[EventFeed] Sync error:', err)
            setSyncMessage('Error al sincronizar')
            setTimeout(() => setSyncMessage(null), 4000)
        } finally {
            setIsSyncing(false)
        }
    }

    if (!mounted || isLoading) {
        return <div className="p-8 text-center text-gray-700 animate-pulse text-[10px] font-bold uppercase tracking-widest">{t.common.loading}</div>
    }

    return (
        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-white">{t.dashboard.events.title}</h3>
                <div className="flex items-center gap-2">
                    {syncMessage && (
                        <span className="text-[9px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            {syncMessage}
                        </span>
                    )}
                    <button
                        onClick={handleSyncBackup}
                        disabled={isSyncing || !hubId}
                        title="Sincronizar historial remoto desde la API oficial de Ajax"
                        className="px-2.5 py-1 text-[9px] font-bold uppercase tracking-wider rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white border border-white/10 flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                        <span className={`text-[10px] ${isSyncing ? 'animate-spin' : ''}`}>🔄</span>
                        {isSyncing ? 'Sincronizando...' : 'Sincronizar Ajax'}
                    </button>
                    <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 text-[9px] font-bold uppercase">
                        <span className="h-1 w-1 rounded-full bg-cyan-500 animate-pulse" /> {t.dashboard.events.live}
                    </span>
                </div>
            </div>

            <div className="flex-1 space-y-8 relative before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-px before:bg-white/5">
                {!isPro ? (
                    <div className="relative pl-10 py-6 border-b border-white/5 mb-6 group transition-opacity opacity-70 hover:opacity-100">
                        {/* Fake Timeline Connector to make it look inline */}
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-[22px] w-[22px] rounded-full border border-[#0f172a] bg-amber-500/10 text-amber-500 flex items-center justify-center z-10 shadow-lg shadow-amber-500/5">
                            <span className="text-[11px]">🔐</span>
                        </div>
                        <div className="flex flex-col gap-1">
                            <span className="text-[10px] font-black uppercase tracking-[0.15em] text-amber-400/80">
                                {t.dashboard.events.nonProUser}
                            </span>
                            <span className="text-[8px] text-gray-600 font-bold uppercase tracking-widest max-w-[280px]">
                                {t.dashboard.events.nonProHint}
                            </span>
                        </div>
                    </div>
                ) : logs.length > 0 ? logs.map((log) => (
                    <div key={log.id} className="relative pl-10">
                        {/* Timeline Connector Dot */}
                        <div className={`absolute left-0 top-1.5 h-[22px] w-[22px] rounded-full border border-[#0f172a] flex items-center justify-center z-10 ${log.event_desc.includes('imiento') || log.event_desc.includes('Motion') ? 'bg-red-500/20 text-red-500' :
                            log.event_desc.includes('Armado') || log.event_desc.includes('Armed') ? 'bg-cyan-500/20 text-cyan-500' :
                                log.event_desc.includes('Bater') || log.event_desc.includes('Battery') ? 'bg-orange-500/20 text-orange-500' : 'bg-gray-500/20 text-gray-400'
                            }`}>
                            <span className="text-[10px]">
                                {log.event_desc.includes('imiento') || log.event_desc.includes('Motion') ? '🏃' :
                                    log.event_desc.includes('Desarmado') || log.event_desc.includes('Disarm') ? '🔓' :
                                        log.event_desc.includes('Armado') || log.event_desc.includes('Armed') ? '🔒' :
                                            log.event_desc.includes('Noche') || log.event_desc.includes('Night') ? '🏠' :
                                                log.event_desc.includes('Bater') || log.event_desc.includes('Battery') ? '🔋' : '✅'}
                            </span>
                        </div>

                        <div>
                            <div className="flex justify-between items-start mb-1">
                                <h4 className={`text-[13px] font-bold ${log.event_desc.includes('Motion') || log.event_desc.includes('imiento') ? 'text-red-400' : 'text-white'}`}>
                                    {getEventDescription(log)}
                                </h4>
                                <span className="text-[9px] font-mono text-gray-600">
                                    {new Date(log.timestamp).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' })} {new Date(log.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                            <p className="text-[10px] text-gray-500 leading-tight">
                                {log.user_name || log.device_name || 'System event'} - {log.user_name ? 'Identity Verified' : 'Technical Log'}
                            </p>

                            {/* Photo / Media Verification Viewer (Restricted to plans with event permissions) */}
                            {log.media_urls && log.media_urls.length > 0 && canViewEvents ? (
                                <PhotoViewer urls={log.media_urls} />
                            ) : null}
                        </div>
                    </div>
                )) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-700 italic text-[10px] uppercase tracking-widest py-20">
                        <span>📭 {t.dashboard.events.empty}</span>
                    </div>
                )}
            </div>

            <button className="mt-8 w-full py-3 rounded-xl border border-white/10 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white hover:bg-white/5 transition-all">
                {t.dashboard.telemetry.viewFullLogs}
            </button>
        </div>
    )
}
