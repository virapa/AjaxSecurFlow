/**
 * Shared Type Definitions
 */

export interface User {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    role: string;
    subscription_active: boolean;
    subscription_expires_at?: string;
    subscription_plan?: string;
    subscription_id?: string;
    ajax_info?: {
        id: number;
        login: string;
        firstName: string;
        lastName: string;
        email: string;
        phone: string;
        imageUrls: {
            small: string;
            medium: string;
            large: string;
        };
    };
}

export interface Hub {
    id: string;
    name: string;
    status: 'armed' | 'disarmed' | 'night' | 'online' | 'offline';
    last_ping: string;
    connection_type: string;
    signal_strength: number;
    battery_level: number;
}

export interface Device {
    id: string;
    name: string;
    device_type: string;
    online: boolean;
    state: string;
    battery_level?: number;
    signal_level?: string;
    temperature?: number;
    malfunctions?: string[];
    bypassState?: string[];
}

export interface LogEntry {
    id: string;
    hub_id: string;
    timestamp: string;
    event_code: string;
    event_desc: string;
    user_name?: string;
    device_name?: string;
    transition?: string;
}
