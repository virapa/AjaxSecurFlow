import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NotificationInbox } from './NotificationInbox'
import { notificationService, type Notification } from './notification.service'

// Mock the local notification service
vi.mock('./notification.service', () => ({
    notificationService: {
        getNotifications: vi.fn(),
        markAsRead: vi.fn()
    }
}))

describe('NotificationInbox Component (Local Scope: Notifications)', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('should display a loading message while fetching notifications', () => {
        vi.mocked(notificationService.getNotifications).mockReturnValue(new Promise(() => { }))
        render(<NotificationInbox />)

        expect(screen.getByText(/cargando/i)).toBeInTheDocument()
    })

    it('should render a list of notifications when data is loaded', async () => {
        const mockNotifications: Notification[] = [
            { id: '1', title: 'Alerta de Seguridad', message: 'Sensor activado', notification_type: 'security', is_read: false, created_at: '2024-01-01T10:00:00Z' },
            { id: '2', title: 'Facturación', message: 'Voucher canjeado', notification_type: 'success', is_read: true, created_at: '2024-01-01T11:00:00Z' }
        ]
        vi.mocked(notificationService.getNotifications).mockResolvedValue(mockNotifications)

        render(<NotificationInbox />)

        await waitFor(() => {
            expect(screen.getByText(/alerta de seguridad/i)).toBeInTheDocument()
            expect(screen.getByText(/facturación/i)).toBeInTheDocument()
        })
    })

    it('should display an empty state message when no notifications exist', async () => {
        vi.mocked(notificationService.getNotifications).mockResolvedValue([])

        render(<NotificationInbox />)

        await waitFor(() => {
            expect(screen.getByText(/no tienes notificaciones/i)).toBeInTheDocument()
        })
    })
})
