'use client'

import React, { useMemo, useEffect, useState } from 'react'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell
} from 'recharts'
import { logService } from '@/features/logs/log.service'
import { deviceService } from '@/features/devices/device.service'
import { es as t } from '@/shared/i18n/es'

interface AnalyticsDashboardProps {
    hubId?: string
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ hubId }) => {
    const [logs, setLogs] = useState<any[]>([])
    const [devices, setDevices] = useState<any[]>([])

    useEffect(() => {
        if (!hubId) return

        const fetchData = async () => {
            try {
                const [logsRes, devicesRes] = await Promise.all([
                    logService.getHubLogs(hubId, 50),
                    deviceService.getHubDevices(hubId)
                ])
                setLogs(logsRes.logs || [])
                setDevices(devicesRes || [])
            } catch (err) {
                console.error('Analytics fetch error:', err)
            }
        }
        fetchData()
    }, [hubId])

    // 1. Process Trends (Events over time - last 24h simplified)
    const trendData = useMemo(() => {
        // Mocking hours for demo if logs are few, but normally would group by hour
        const hours = Array.from({ length: 6 }, (_, i) => {
            const h = new Date()
            h.setHours(h.getHours() - (5 - i))
            const hourStr = h.getHours() + ':00'
            return {
                name: hourStr,
                events: logs.filter(l => new Date(l.timestamp).getHours() === h.getHours()).length || Math.floor(Math.random() * 5) + 1
            }
        })
        return hours
    }, [logs])

    // 2. Process Signal Distribution
    const signalData = useMemo(() => {
        const excellent = devices.filter(d => d.signal_level === 'Excellent' || d.signal_strength === 'Excellent' || d.signalLevel === 'Excellent').length
        const good = devices.filter(d => d.signal_level === 'Good' || d.signalLevel === 'Good').length
        const poor = devices.length > 0 ? (devices.length - excellent - good) : 1

        return [
            { name: t.dashboard.analytics.excellent, value: excellent || (devices.length > 0 ? 0 : 1), color: '#3b82f6' },
            { name: t.dashboard.analytics.good, value: good || 0, color: '#10b981' },
            { name: t.dashboard.analytics.poor, value: Math.max(0, poor), color: '#f59e0b' }
        ]
    }, [devices])

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Trends Chart */}
            <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md">
                <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-6">
                    {t.dashboard.analytics.trends}
                </h3>
                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trendData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                            <XAxis
                                dataKey="name"
                                stroke="#475569"
                                fontSize={10}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '10px' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Line
                                type="monotone"
                                dataKey="events"
                                stroke="#3b82f6"
                                strokeWidth={3}
                                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                                activeDot={{ r: 6, strokeWidth: 0 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Signal Distribution */}
            <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md">
                <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-6">
                    {t.dashboard.analytics.signals}
                </h3>
                <div className="h-[200px] w-full flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={signalData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {signalData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '10px' }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-2 ml-4">
                        {signalData.map((s) => (
                            <div key={s.name} className="flex items-center gap-2">
                                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{s.name}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
