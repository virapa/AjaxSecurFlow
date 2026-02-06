import { apiClient } from '@/infrastructure/api-client'

export interface Device {
    id: string
    name: string
    device_type: string
    online: boolean
    state: string
    battery_level?: number
    signal_level?: string
    temperature?: number
    malfunctions: string[]
    bypassState?: string[]
}

/**
 * Device Service (Local Scope: features/devices)
 */
export const deviceService = {
    /**
     * Fetches all devices for a given hub.
     */
    getHubDevices: async (hubId: string): Promise<Device[]> => {
        return apiClient.get<Device[]>(`/ajax/hubs/${hubId}/devices`)
    },

    /**
     * Fetches details for a specific device.
     */
    getDeviceDetails: async (hubId: string, deviceId: string): Promise<Device> => {
        return apiClient.get<Device>(`/ajax/hubs/${hubId}/devices/${deviceId}`)
    }
}
