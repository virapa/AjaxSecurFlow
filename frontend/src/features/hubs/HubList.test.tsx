import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { HubList } from './HubList'
import { Hub } from './hub.service'

describe('HubList Component (Local Scope: Hubs)', () => {
    const defaultProps = {
        hubs: [],
        isLoading: false,
        error: null,
        onSelectHub: vi.fn(),
        refreshHubs: vi.fn()
    }

    it('should display pulse skeletons while loading', () => {
        render(<HubList {...defaultProps} isLoading={true} />)
        // Pulse divs are rendered when loading
        const skeletons = document.querySelectorAll('.animate-pulse')
        expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should render a list of hubs when data is provided', () => {
        const mockHubs: Hub[] = [
            { id: 'hub1', name: 'Casa Principal', online: true, state: 'DISARMED', hub_subtype: 'AJAX_HUB' },
            { id: 'hub2', name: 'Oficina Central', online: false, state: 'ARMED', hub_subtype: 'AJAX_HUB_PLUS' }
        ]

        render(<HubList {...defaultProps} hubs={mockHubs} />)

        expect(screen.getByText(/casa principal/i)).toBeInTheDocument()
        expect(screen.getByText(/oficina central/i)).toBeInTheDocument()
    })

    it('should display the correct state badge for each hub', () => {
        const mockHubs: Hub[] = [
            { id: 'hub1', name: 'Hub 1', online: true, state: 'ARMED' },
            { id: 'hub2', name: 'Hub 2', online: true, state: 'DISARMED' },
            { id: 'hub3', name: 'Hub 3', online: true, state: 'NIGHT_MODE' }
        ]

        render(<HubList {...defaultProps} hubs={mockHubs} />)

        // Use getAllByText with exact match to avoid confusion with buttons like "Armado Total"
        expect(screen.getAllByText(/^armado$/i).length).toBeGreaterThan(0)
        expect(screen.getAllByText(/^desarmado$/i).length).toBeGreaterThan(0)
        expect(screen.getAllByText(/^modo noche$/i).length).toBeGreaterThan(0)
    })

    it('should display an empty state message when no hubs are provided', () => {
        render(<HubList {...defaultProps} hubs={[]} />)
        expect(screen.getByText(/no se encontraron hubs activos/i)).toBeInTheDocument()
    })

    it('should call onSelectHub when a card is clicked', () => {
        const onSelect = vi.fn()
        const mockHubs: Hub[] = [
            { id: 'hub1', name: 'Hub 1', online: true, state: 'DISARMED' }
        ]

        render(<HubList {...defaultProps} hubs={mockHubs} onSelectHub={onSelect} />)

        const cardHeader = screen.getByText(/hub 1/i)
        fireEvent.click(cardHeader)

        expect(onSelect).toHaveBeenCalledWith(mockHubs[0])
    })
})
