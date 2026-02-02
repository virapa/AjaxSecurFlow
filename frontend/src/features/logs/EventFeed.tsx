'use client'

import React, { useEffect, useState } from 'react'
import { logService, EventLog } from './log.service'
import { es as t } from '@/shared/i18n/es'

interface EventFeedProps {
    hubId?: string
}

export const EventFeed: React.FC<EventFeedProps> = ({ hubId }) => {
    const [logs, setLogs] = useState<EventLog[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
        if (!hubId) {
            setLogs([])
            setIsLoading(false)
            return
        }

        const fetchLogs = async () => {
            try {
                const response = await logService.getHubLogs(hubId, 10)
                setLogs(response.logs || [])
            } catch (err: any) {
                // Ignore 404 errors for logs (hubs without history support)
                if (err.status === 404 || err.message?.includes('404')) {
                    setLogs([])
                } else {
                    console.error('Failed to fetch logs', err)
                }
            } finally {
                setIsLoading(false)
            }
        }

        fetchLogs()
    }, [hubId])

    if (!mounted || isLoading) {
        return <div className="p-8 text-center text-gray-700 animate-pulse text-[10px] font-bold uppercase tracking-widest">{t.common.loading}</div>
    }

    return (
        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-white">{t.dashboard.events.title}</h3>
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[9px] font-bold uppercase">
                    <span className="h-1 w-1 rounded-full bg-blue-500 animate-pulse" /> {t.dashboard.events.live}
                </span>
            </div>

            <div className="flex-1 space-y-8 relative before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-px before:bg-white/5">
                {logs.length > 0 ? logs.map((log) => (
                    <div key={log.id} className="relative pl-10">
                        {/* Timeline Connector Dot */}
                        <div className={`absolute left-0 top-1.5 h-[22px] w-[22px] rounded-full border border-[#0f172a] flex items-center justify-center z-10 ${log.event_desc.includes('imiento') || log.event_desc.includes('Motion') ? 'bg-red-500/20 text-red-500' :
                            log.event_desc.includes('Armado') || log.event_desc.includes('Armed') ? 'bg-blue-500/20 text-blue-500' :
                                log.event_desc.includes('Bater') || log.event_desc.includes('Battery') ? 'bg-orange-500/20 text-orange-500' : 'bg-gray-500/20 text-gray-400'
                            }`}>
                            <span className="text-[10px]">
                                {log.event_desc.includes('imiento') || log.event_desc.includes('Motion') ? '🏃' : log.event_desc.includes('Armado') || log.event_desc.includes('Armed') ? '🛡️' : log.event_desc.includes('Bater') || log.event_desc.includes('Battery') ? '🔋' : '✅'}
                            </span>
                        </div>

                        <div>
                            <div className="flex justify-between items-start mb-1">
                                <h4 className={`text-[13px] font-bold ${log.event_desc.includes('Motion') ? 'text-red-400' : 'text-white'}`}>
                                    {log.event_desc}
                                </h4>
                                <span className="text-[9px] font-mono text-gray-600">
                                    {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                            </div>
                            <p className="text-[10px] text-gray-500 leading-tight">
                                {log.user_name || log.device_name || 'System event'} - {log.user_name ? 'Identity Verified' : 'Technical Log'}
                            </p>

                            {/* Motion Image Mockup if needed */}
                            {log.event_desc.includes('Motion') && (
                                <div className="mt-3 rounded-xl border border-white/5 bg-white/5 p-1">
                                    <div className="aspect-video bg-black/40 rounded-lg flex items-center justify-center text-gray-700 text-[10px] font-bold italic">
                                        Minimal Verification Photo
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-700 italic text-[10px] uppercase tracking-widest py-20">
                        <span>📭 No hay eventos recientes</span>
                    </div>
                )}
            </div>

            <button className="mt-8 w-full py-3 rounded-xl border border-white/10 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white hover:bg-white/5 transition-all">
                {t.dashboard.telemetry.viewFullLogs}
            </button>
        </div>
    )
}
