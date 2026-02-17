'use client'

import React, { useEffect, useState, useImperativeHandle, forwardRef } from 'react'
import { deviceService, Device } from './device.service'
import { es as t } from '@/shared/i18n/es'

export interface DeviceTelemetryRef {
    exportToCSV: () => void
}

interface DeviceTelemetryProps {
    hubId?: string
    searchQuery?: string
}

interface DeviceDetails extends Device {
    [key: string]: unknown
}

// Modal Component for Device Details - fetches details on demand
const DeviceDetailModal: React.FC<{
    device: Device
    hubId: string
    onClose: () => void
}> = ({ device, hubId, onClose }) => {
    const [details, setDetails] = useState<DeviceDetails | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const isOffline = device.online === false

    // Fetch device details on mount
    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const data = await deviceService.getDeviceDetails(hubId, device.id)
                setDetails({ ...device, ...data } as DeviceDetails)
            } catch (err) {
                console.warn(`[DeviceDetailModal] Failed to fetch details for ${device.id}`)
                setDetails(device as DeviceDetails)
            } finally {
                setIsLoading(false)
            }
        }
        fetchDetails()
    }, [hubId, device])

    // Close on escape key
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose()
        }
        window.addEventListener('keydown', handleEsc)
        return () => window.removeEventListener('keydown', handleEsc)
    }, [onClose])

    // Format value for display
    const formatValue = (value: unknown): string => {
        if (value === null || value === undefined) return '—'
        if (typeof value === 'boolean') return value ? 'Sí' : 'No'
        if (typeof value === 'object') return JSON.stringify(value, null, 2)
        return String(value)
    }

    // Fields to display with labels
    const displayFields = [
        { key: 'id', label: 'ID' },
        { key: 'name', label: 'Nombre' },
        { key: 'device_type', label: 'Tipo' },
        { key: 'online', label: 'Estado' },
        { key: 'battery_level', label: 'Batería' },
        { key: 'temperature', label: 'Temperatura' },
        { key: 'signal_level', label: 'Señal' },
        { key: 'state', label: 'Estado Sensor' },
        { key: 'firmware_version', label: 'Firmware' },
        { key: 'room_id', label: 'ID Habitación' },
        { key: 'group_id', label: 'ID Grupo' },
        { key: 'model', label: 'Modelo' },
        { key: 'color', label: 'Color' },
        { key: 'bypassState', label: 'Bypass' },
    ]

    // Get text color based on field and offline status
    const getValueColor = (key: string, value: unknown): string => {
        if (key === 'online') {
            return value === true ? 'text-green-400' : value === false ? 'text-red-400' : 'text-gray-400'
        }
        if (isOffline) {
            return 'text-gray-600'
        }
        return 'text-white'
    }

    const displayDevice = details || device

    return (
        <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
            onClick={onClose}
        >
            <div
                className={`bg-[#0f172a] border border-white/10 rounded-3xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-hidden animate-in zoom-in-95 duration-200 ${isOffline ? 'opacity-80' : ''}`}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="px-6 py-5 border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className={`h-12 w-12 rounded-xl flex items-center justify-center text-2xl ${isOffline ? 'bg-gray-500/10 grayscale' : 'bg-cyan-500/10'}`}>
                            {device.device_type?.includes('Motion') || device.device_type?.includes('MotionProtect') ? '📡' :
                                device.device_type?.includes('Door') || device.device_type?.includes('DoorProtect') ? '🚪' :
                                    device.device_type?.includes('Space') || device.device_type?.includes('Control') ? '🎮' :
                                        device.device_type?.includes('Relay') || device.device_type?.includes('WallSwitch') ? '💡' :
                                            device.device_type?.includes('Fire') || device.device_type?.includes('Smoke') ? '🔥' :
                                                device.device_type?.includes('Siren') ? '🔔' :
                                                    device.device_type?.includes('Keyboard') || device.device_type?.includes('KeyPad') ? '⌨️' : '📦'}
                        </div>
                        <div>
                            <h2 className={`text-lg font-bold ${isOffline ? 'text-gray-500' : 'text-white'}`}>{device.name || 'Sin nombre'}</h2>
                            <p className="text-xs text-gray-500">{device.device_type}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="h-8 w-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                    >
                        ✕
                    </button>
                </div>

                {/* Offline banner */}
                {isOffline && (
                    <div className="px-6 py-2 bg-red-500/10 border-b border-red-500/20">
                        <p className="text-[10px] font-bold text-red-400 uppercase tracking-wider">⚠️ Dispositivo Offline - Mostrando últimos valores conocidos</p>
                    </div>
                )}

                {/* Content */}
                <div className="px-6 py-4 overflow-y-auto max-h-[calc(80vh-100px)]">
                    {isLoading ? (
                        <div className="py-8 text-center">
                            <span className="text-[10px] text-gray-600 animate-pulse font-bold uppercase tracking-widest">Cargando detalles...</span>
                        </div>
                    ) : (
                        <>
                            <div className="space-y-3">
                                {displayFields.map(({ key, label }) => {
                                    const value = (displayDevice as any)[key]
                                    if (value === undefined) return null

                                    return (
                                        <div key={key} className="flex justify-between items-center py-2 border-b border-white/5 last:border-0">
                                            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">{label}</span>
                                            <span className={`text-sm font-medium ${getValueColor(key, value)}`}>
                                                {key === 'online'
                                                    ? (value === true ? '🟢 Online' : value === false ? '🔴 Offline' : '—')
                                                    : key === 'battery_level' && value !== null
                                                        ? `${value}%`
                                                        : key === 'temperature' && value !== null
                                                            ? `${value}°C`
                                                            : key === 'bypassState' && Array.isArray(value)
                                                                ? (value.length > 0 ? value.join(', ') : '—')
                                                                : formatValue(value)
                                                }
                                            </span>
                                        </div>
                                    )
                                })}
                            </div>

                            {/* Additional raw data section (collapsed) */}
                            <details className="mt-4">
                                <summary className="text-[10px] font-bold text-gray-600 uppercase tracking-wider cursor-pointer hover:text-gray-400 transition-colors">
                                    Datos técnicos
                                </summary>
                                <pre className="mt-2 p-3 bg-black/30 rounded-xl text-[10px] text-gray-500 overflow-x-auto font-mono">
                                    {JSON.stringify(displayDevice, null, 2)}
                                </pre>
                            </details>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}

export const DeviceTelemetry = forwardRef<DeviceTelemetryRef, DeviceTelemetryProps>(({ hubId, searchQuery = '' }, ref) => {
    const [devices, setDevices] = useState<Device[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [mounted, setMounted] = useState(false)
    const [selectedDevice, setSelectedDevice] = useState<Device | null>(null)

    // Expose export function to parent
    useImperativeHandle(ref, () => ({
        exportToCSV: () => {
            if (!devices.length) return

            const filtered = devices.filter(device =>
                (device.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                (device.device_type || '').toLowerCase().includes(searchQuery.toLowerCase())
            )

            if (!filtered.length) return

            // CSV Header
            const headers = ['Nombre', 'Tipo', 'Estado', 'Batería', 'Señal', 'ID']
            const rows = filtered.map(d => [
                d.name || 'Sin nombre',
                d.device_type || 'Unknown',
                d.online ? 'Online' : 'Offline',
                d.battery_level !== undefined ? `${d.battery_level}%` : '—',
                d.signal_level !== undefined ? d.signal_level : '—',
                d.id
            ])

            const csvContent = [
                headers.join(','),
                ...rows.map(r => r.map(field => `"${field}"`).join(','))
            ].join('\n')

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
            const url = URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.setAttribute('href', url)
            link.setAttribute('download', `AjaxSecurFlow_Report_${hubId || 'Direct'}_${new Date().toISOString().split('T')[0]}.csv`)
            link.style.visibility = 'hidden'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        }
    }))

    useEffect(() => {
        setMounted(true)
        if (!hubId) {
            setDevices([])
            setIsLoading(false)
            return
        }

        const fetchDevices = async () => {
            try {
                console.log(`[DeviceTelemetry] Fetching devices for hub: ${hubId}`)
                const data = await deviceService.getHubDevices(hubId)
                setDevices(data || [])
            } catch (err: unknown) {
                console.error(`[DeviceTelemetry] Failed to fetch devices:`, err)
                setDevices([])
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
        <>
            {/* Modal - fetches details on demand */}
            {selectedDevice && hubId && (
                <DeviceDetailModal
                    device={selectedDevice}
                    hubId={hubId}
                    onClose={() => setSelectedDevice(null)}
                />
            )}

            <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl overflow-hidden backdrop-blur-md">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-white/5">
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.telemetry.labels.name}</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.telemetry.labels.status}</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-600 text-right">{t.dashboard.telemetry.labels.action}</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {(() => {
                            const filteredDevices = devices.filter(device =>
                                (device.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                                (device.device_type || '').toLowerCase().includes(searchQuery.toLowerCase())
                            )

                            if (filteredDevices.length === 0) {
                                return (
                                    <tr>
                                        <td colSpan={3} className="px-6 py-20 text-center text-gray-700 italic text-[10px] uppercase tracking-widest">
                                            {t.dashboard.telemetry.empty}
                                        </td>
                                    </tr>
                                )
                            }

                            return filteredDevices.map((device) => {
                                const isOffline = device.online === false
                                return (
                                    <tr key={device.id} className={`hover:bg-white/[0.02] transition-colors group ${isOffline ? 'opacity-70' : ''}`}>
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-4">
                                                <div className={`h-10 w-10 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform ${isOffline ? 'bg-gray-500/10 grayscale' : 'bg-cyan-500/10 text-cyan-400'}`}>
                                                    {device.device_type?.includes('Motion') || device.device_type?.includes('MotionProtect') ? '📡' :
                                                        device.device_type?.includes('Door') || device.device_type?.includes('DoorProtect') ? '🚪' :
                                                            device.device_type?.includes('Space') || device.device_type?.includes('Control') ? '🎮' :
                                                                device.device_type?.includes('Relay') || device.device_type?.includes('WallSwitch') ? '💡' :
                                                                    device.device_type?.includes('Fire') || device.device_type?.includes('Smoke') ? '🔥' :
                                                                        device.device_type?.includes('Siren') ? '🔔' :
                                                                            device.device_type?.includes('Keyboard') || device.device_type?.includes('KeyPad') ? '⌨️' : '📦'}
                                                </div>
                                                <div>
                                                    <div className={`text-sm font-bold ${isOffline ? 'text-gray-500' : 'text-white'}`}>{device.name || 'Sin nombre'}</div>
                                                    <div className="text-[10px] text-gray-600 font-medium">{device.device_type}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-2">
                                                <span className={`h-2 w-2 rounded-full ${device.online === true ? 'bg-green-500 animate-pulse' : device.online === false ? 'bg-red-500' : 'bg-gray-500'}`} />
                                                <span className={`text-xs font-bold ${device.online === true ? 'text-green-400' : device.online === false ? 'text-red-400' : 'text-gray-500'}`}>
                                                    {device.online === true ? 'Online' : device.online === false ? 'Offline' : '—'}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 text-right">
                                            <button
                                                onClick={() => setSelectedDevice(device)}
                                                className="text-[10px] font-bold text-cyan-400 hover:text-cyan-300 transition-colors uppercase tracking-tighter bg-cyan-500/10 hover:bg-cyan-500/20 px-3 py-1.5 rounded-lg"
                                            >
                                                {t.dashboard.telemetry.labels.details}
                                            </button>
                                        </td>
                                    </tr>
                                )
                            })
                        })()}
                    </tbody>
                </table>
            </div>
        </>
    )
})

DeviceTelemetry.displayName = 'DeviceTelemetry'
