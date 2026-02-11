'use client'

import React, { useMemo, useEffect, useState } from 'react'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell
} from 'recharts'
import { logService } from '@/features/logs/log.service'
import { deviceService } from '@/features/devices/device.service'
import { es as t } from '@/shared/i18n/es'
import { LogEntry, Device } from '@/shared/types'

interface AnalyticsDashboardProps {
    hubId?: string
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ hubId }) => {
    const [logs, setLogs] = useState<LogEntry[]>([])
    const [devices, setDevices] = useState<Device[]>([])

    useEffect(() => {
        if (!hubId) return

        const fetchData = async () => {
            try {
                const [logsRes, devicesRes] = await Promise.all([
                    logService.getHubLogs(hubId, 50),
                    deviceService.getHubDevices(hubId)
                ])
                setLogs(logsRes?.logs || [])
                setDevices(devicesRes || [])
            } catch (err) {
                console.error('Analytics fetch error:', err)
            }
        }
        fetchData()
    }, [hubId])

    // 1. Process Trends (Events over time - last 6h)
    const [trendData, setTrendData] = useState<{ name: string, events: number }[]>([])

    useEffect(() => {
        const calculateTrends = () => {
            const hours = Array.from({ length: 6 }, (_, i) => {
                const h = new Date()
                h.setHours(h.getHours() - (5 - i))
                const hourStr = h.getHours() + ':00'
                const count = logs.filter(l => new Date(l?.timestamp).getHours() === h.getHours()).length

                return {
                    name: hourStr,
                    events: count
                }
            })
            setTrendData(hours)
        }
        calculateTrends()
    }, [logs])


    return (
        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md h-full">
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
    )
}
