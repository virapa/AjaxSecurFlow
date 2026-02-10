import { apiClient } from '@/infrastructure/api-client'

export interface HubBattery {
    chargeLevelPercentage: number
    state: string
}

export interface HubGSM {
    signalLevel: string
    networkStatus: string
    activeSimCard?: number
}

export interface Hub {
    id: string
    name: string
    online: boolean
    state: 'ARMED' | 'DISARMED' | 'NIGHT_MODE'
    hub_subtype?: string
    battery_level?: number
    gsm_signal?: string
    ethernet_ip?: string
    firmware_version?: string
    battery?: HubBattery
    gsm?: HubGSM
    role?: 'MASTER' | 'PRO' | 'USER'
}

/**
 * Hub Service (Local Scope: features/hubs)
 * Interacts with the backend proxy to communicate with Ajax Systems API.
 */
export const hubService = {
    /**
     * Fetches the list of hubs associated with the user's Ajax account.
     */
    getHubs: async (): Promise<Hub[]> => {
        return apiClient.get<Hub[]>('/ajax/hubs')
    },

    /**
     * Fetches detailed information for a specific hub.
     */
    getHubDetails: async (hubId: string): Promise<Hub> => {
        return apiClient.get<Hub>(`/ajax/hubs/${hubId}`)
    },

    /**
     * Sends an arm/disarm command to the hub.
     */
    setArmState: async (hubId: string, armState: 0 | 1 | 2): Promise<{ success: boolean }> => {
        return apiClient.post(`/ajax/hubs/${hubId}/arm-state`, { armState })
    }
}
