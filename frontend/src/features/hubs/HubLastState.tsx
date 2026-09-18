'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { hubService, HubLastState as HubLastStateDto } from './hub.service'
import { es as t } from '@/shared/i18n/es'

const STORAGE_KEY = 'ajax_hub_states'
const POLL_INTERVAL_MS = 30000

interface HubLastStateProps {
    hubId?: string
}

const EVENT_STYLES: Record<string, { icon: string; color: string }> = {
    ALARM: { icon: '🛑', color: 'bg-red-500/20 text-red-400' },
    ARMED: { icon: '🔐', color: 'bg-cyan-500/20 text-cyan-400' },
    DISARMED: { icon: '🔓', color: 'bg-gray-500/20 text-gray-300' },
    NIGHT_MODE_ON: { icon: '🏠', color: 'bg-indigo-500/20 text-indigo-400' },
    POWER_LOSS: { icon: '⚡', color: 'bg-amber-500/20 text-amber-400' },
    POWER_RESTORED: { icon: '🔌', color: 'bg-emerald-500/20 text-emerald-400' }
}

const getEventLabel = (eventType: string): string => {
    // @ts-ignore - Dynamic key lookup
    return t.sqsEvents[eventType] || `${t.sqsEvents.UNKNOWN}: ${eventType}`
}

/**
 * HubLastState (Local Scope: Hubs)
 * Shows the last known state of the selected hub, fed by the backend SQS
 * events consumer. Every state received is persisted in localStorage so the
 * last known state survives reloads and temporary API outages.
 */
export const HubLastState: React.FC<HubLastStateProps> = ({ hubId }) => {
    const [states, setStates] = useState<Record<string, HubLastStateDto>>({})
    const [isStale, setIsStale] = useState(false)

    const hydrateFromStorage = useCallback(() => {
        if (typeof window === 'undefined') return
        try {
            const stored = window.localStorage.getItem(STORAGE_KEY)
            if (stored) {
                setStates(JSON.parse(stored))
                setIsStale(true)
            }
        } catch {
            // Corrupt storage: ignore, next successful fetch overwrites it
        }
    }, [])

    const fetchStates = useCallback(async () => {
        try {
            const data = await hubService.getHubStates()
            const byHub: Record<string, HubLastStateDto> = {}
            for (const state of data) {
                byHub[state.hub_id] = state
            }
            setStates(byHub)
            setIsStale(false)
            if (typeof window !== 'undefined') {
                window.localStorage.setItem(STORAGE_KEY, JSON.stringify(byHub))
            }
        } catch (err) {
            console.error('[HubLastState] Failed to fetch hub states:', err)
            hydrateFromStorage()
        }
    }, [hydrateFromStorage])

    useEffect(() => {
        fetchStates()
        const interval = setInterval(fetchStates, POLL_INTERVAL_MS)
        return () => clearInterval(interval)
    }, [fetchStates])

    const current = hubId ? states[hubId] : undefined
    const style = current ? (EVENT_STYLES[current.last_event_type] || { icon: '📡', color: 'bg-gray-500/20 text-gray-400' }) : null

    return (
        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md mb-8">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-white">{t.dashboard.lastState.title}</h3>
                {isStale && (
                    <span className="text-[8px] font-bold uppercase tracking-widest text-amber-400/80">
                        {t.dashboard.lastState.offline}
                    </span>
                )}
            </div>

            {current && style ? (
                <div className="flex items-center gap-4" data-testid="hub-last-state">
                    <div className={`h-10 w-10 rounded-2xl flex items-center justify-center text-lg ${style.color}`}>
                        {style.icon}
                    </div>
                    <div className="flex flex-col">
                        <span className="text-[13px] font-bold text-white">
                            {getEventLabel(current.last_event_type)}
                        </span>
                        {current.updated_at && (
                            <span className="text-[9px] font-mono text-gray-500">
                                {t.dashboard.lastState.updated}: {new Date(current.updated_at).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' })} {new Date(current.updated_at).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        )}
                    </div>
                </div>
            ) : (
                <div className="text-gray-600 italic text-[10px] uppercase tracking-widest py-2">
                    📭 {t.dashboard.lastState.empty}
                </div>
            )}
        </div>
    )
}
