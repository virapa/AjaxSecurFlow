import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HubLastState } from './HubLastState'
import { hubService, HubLastState as HubLastStateDto } from './hub.service'

vi.mock('./hub.service', async (importOriginal) => {
    const original = await importOriginal<typeof import('./hub.service')>()
    return {
        ...original,
        hubService: {
            ...original.hubService,
            getHubStates: vi.fn()
        }
    }
})

const mockedGetHubStates = vi.mocked(hubService.getHubStates)

describe('HubLastState Component (Local Scope: Hubs)', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        window.localStorage.clear()
    })

    it('should render the last known state of the selected hub', async () => {
        const states: HubLastStateDto[] = [
            { hub_id: 'hub1', hub_name: 'Casa', last_event_type: 'ARMED', updated_at: '2026-07-08T10:00:00Z' }
        ]
        mockedGetHubStates.mockResolvedValue(states)

        render(<HubLastState hubId="hub1" />)

        await waitFor(() => {
            expect(screen.getByTestId('hub-last-state')).toBeInTheDocument()
        })
        expect(screen.getByText('Sistema Armado')).toBeInTheDocument()
    })

    it('should persist the fetched states in localStorage as last known state', async () => {
        const states: HubLastStateDto[] = [
            { hub_id: 'hub1', last_event_type: 'ALARM', updated_at: '2026-07-08T10:00:00Z' }
        ]
        mockedGetHubStates.mockResolvedValue(states)

        render(<HubLastState hubId="hub1" />)

        await waitFor(() => {
            const stored = window.localStorage.getItem('ajax_hub_states')
            expect(stored).not.toBeNull()
            expect(JSON.parse(stored!)['hub1'].last_event_type).toBe('ALARM')
        })
    })

    it('should fall back to the stored state when the API fails', async () => {
        window.localStorage.setItem('ajax_hub_states', JSON.stringify({
            hub1: { hub_id: 'hub1', last_event_type: 'DISARMED', updated_at: '2026-07-08T09:00:00Z' }
        }))
        mockedGetHubStates.mockRejectedValue(new Error('network down'))

        render(<HubLastState hubId="hub1" />)

        await waitFor(() => {
            expect(screen.getByText('Sistema Desarmado')).toBeInTheDocument()
        })
        // Stale indicator shown when serving from localStorage
        expect(screen.getByText(/último estado guardado/i)).toBeInTheDocument()
    })

    it('should show an empty state when there is no data for the hub', async () => {
        mockedGetHubStates.mockResolvedValue([])

        render(<HubLastState hubId="hub_without_events" />)

        await waitFor(() => {
            expect(screen.getByText(/sin eventos registrados/i)).toBeInTheDocument()
        })
    })
})
