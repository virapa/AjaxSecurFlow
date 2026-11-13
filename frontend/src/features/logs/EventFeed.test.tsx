import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { EventFeed } from './EventFeed'
import { logService, EventLog } from './log.service'

vi.mock('./log.service', () => ({
    logService: {
        getHubLogs: vi.fn(),
        syncRemoteLogs: vi.fn(),
        subscribeToEventStream: vi.fn(() => () => {})
    }
}))

const mockedGetHubLogs = vi.mocked(logService.getHubLogs)

describe('EventFeed Component (Media & Subscription Permissions)', () => {
    const mockLogsWithMedia: EventLog[] = [
        {
            id: 'evt_1',
            hub_id: 'hub_test',
            timestamp: '2026-09-02T10:11:22Z',
            event_code: 'ALARM',
            event_desc: 'Movimiento detectado, Cámara en Cabina',
            device_name: 'Cámara',
            user_name: 'Cabina',
            media_urls: [
                'https://s3.amazonaws.com/photo1.jpg',
                'https://s3.amazonaws.com/photo2.jpg'
            ]
        }
    ]

    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('should render PhotoViewer when user has a subscription plan allowing events (e.g. basic)', async () => {
        mockedGetHubLogs.mockResolvedValue(mockLogsWithMedia)

        render(<EventFeed hubId="hub_test" role="MASTER" userPlan="basic" />)

        await waitFor(() => {
            expect(screen.getByText(/Movimiento detectado/i)).toBeInTheDocument()
        })

        // PhotoViewer should be visible with photo counter
        expect(screen.getByText('1/2')).toBeInTheDocument()
        const img = screen.getByAltText('Fotoverificación 1')
        expect(img).toBeInTheDocument()
        expect(img).toHaveAttribute('src', 'https://s3.amazonaws.com/photo1.jpg')
    })

    it('should cycle to the next photo when clicking the navigation button', async () => {
        mockedGetHubLogs.mockResolvedValue(mockLogsWithMedia)

        render(<EventFeed hubId="hub_test" role="MASTER" userPlan="pro" />)

        await waitFor(() => {
            expect(screen.getByText('1/2')).toBeInTheDocument()
        })

        // Click next button '›'
        const nextButton = screen.getByText('›')
        fireEvent.click(nextButton)

        // Photo indicator and image should advance
        expect(screen.getByText('2/2')).toBeInTheDocument()
        const nextImg = screen.getByAltText('Fotoverificación 2')
        expect(nextImg).toHaveAttribute('src', 'https://s3.amazonaws.com/photo2.jpg')
    })

    it('should NOT render PhotoViewer when user has a free plan without events permission', async () => {
        mockedGetHubLogs.mockResolvedValue(mockLogsWithMedia)

        render(<EventFeed hubId="hub_test" role="MASTER" userPlan="free" />)

        await waitFor(() => {
            expect(screen.getByText(/Movimiento detectado/i)).toBeInTheDocument()
        })

        // PhotoViewer elements must not be present
        expect(screen.queryByText('1/2')).not.toBeInTheDocument()
        expect(screen.queryByAltText('Fotoverificación 1')).not.toBeInTheDocument()
    })
})
