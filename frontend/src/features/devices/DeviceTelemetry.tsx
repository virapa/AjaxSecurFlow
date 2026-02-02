'use client'

import React, { useEffect, useState } from 'react'
import { deviceService, Device } from './device.service'
import { es as t } from '@/shared/i18n/es'

interface DeviceTelemetryProps {
    hubId?: string
}

export const DeviceTelemetry: React.FC<DeviceTelemetryProps> = ({ hubId }) => {
    const [devices, setDevices] = useState<Device[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
        if (!hubId) {
            setDevices([])
            setIsLoading(false)
            return
        }

        const fetchDevices = async () => {
            try {
                const data = await deviceService.getHubDevices(hubId)
                setDevices(data)
            } catch (err) {
                console.error('Failed to fetch devices', err)
            } finally {
                setIsLoading(false)
            }
        }

        fetchDevices()
    }, [hubId])

    if (!mounted || isLoading) {
        return <div className="p-8 text-center text-gray-600 animate-pulse text-[10px] font-bold uppercase tracking-widest">{t.common.loading}</div>
    }

    return (
        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl overflow-hidden backdrop-blur-md">
            <table className="w-full text-left">
                <thead>
                    <tr className="border-b border-white/5">
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.telemetry.labels.name}</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.telemetry.labels.status}</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.telemetry.labels.battery}</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.telemetry.labels.signal}</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.telemetry.labels.temp}</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600 text-right">{t.dashboard.telemetry.labels.action}</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                    {devices.length > 0 ? devices.map((device) => (
                        <tr key={device.id} className="hover:bg-white/[0.02] transition-colors group">
                            <td className="px-6 py-5">
                                <div className="flex items-center gap-4">
                                    <div className="h-10 w-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                                        {device.name.includes('Motion') ? '📡' : device.name.includes('Door') ? '🚪' : '🔥'}
                                    </div>
                                    <div>
                                        <div className="text-sm font-bold text-white">{device.name}</div>
                                        <div className="text-[10px] text-gray-600 font-medium">{device.device_type}</div>
                                    </div>
                                </div>
                            </td>
                            <td className="px-6 py-5">
                                <div className="flex items-center gap-2">
                                    <span className={`h-1.5 w-1.5 rounded-full ${device.state === 'Secure' || device.state === 'OK' || device.state === 'Closed' ? 'bg-green-500' : 'bg-red-500'}`} />
                                    <span className="text-xs font-bold text-white">{device.state}</span>
                                </div>
                            </td>
                            <td className="px-6 py-5">
                                <div className="flex items-center gap-3">
                                    <div className="w-16 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${device.battery_level && device.battery_level < 20 ? 'bg-red-500' : device.battery_level && device.battery_level < 50 ? 'bg-orange-500' : 'bg-green-500'}`}
                                            style={{ width: `${device.battery_level}%` }}
                                        />
                                    </div>
                                    <span className="text-[10px] font-bold text-gray-400">{device.battery_level}%</span>
                                </div>
                            </td>
                            <td className="px-6 py-5">
                                <div className="flex items-end gap-0.5 h-3">
                                    <div className="w-1 h-3/6 bg-green-500 rounded-[1px]" />
                                    <div className="w-1 h-4/6 bg-green-500 rounded-[1px]" />
                                    <div className="w-1 h-5/6 bg-green-500 rounded-[1px]" />
                                    <div className="w-1 h-full bg-green-500 rounded-[1px]" />
                                </div>
                            </td>
                            <td className="px-6 py-5">
                                <span className="text-xs font-bold text-gray-400">{device.temperature}°C</span>
                            </td>
                            <td className="px-6 py-5 text-right">
                                <button className="text-[10px] font-bold text-gray-600 hover:text-white transition-colors uppercase tracking-tighter">{t.dashboard.telemetry.labels.details}</button>
                            </td>
                        </tr>
                    )) : (
                        <tr>
                            <td colSpan={6} className="px-6 py-20 text-center text-gray-700 italic text-[10px] uppercase tracking-widest">
                                No se han detectado dispositivos activos
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    )
}
