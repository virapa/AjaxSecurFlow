import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import NotificationsPage from './page'
import { es as t } from '@/shared/i18n/es'

// Mock dependencies
vi.mock('@/features/navigation/Sidebar', () => ({
    Sidebar: () => <div data-testid="sidebar" />
}))
vi.mock('@/features/navigation/DashboardHeader', () => ({
    DashboardHeader: ({ title }: { title: string }) => <div data-testid="header">{title}</div>
}))
vi.mock('@/features/notifications/NotificationInbox', () => ({
    NotificationInbox: () => <div data-testid="notification-inbox" />
}))
vi.mock('@/features/auth/auth.service', () => ({
    authService: {
        getProfile: vi.fn().mockResolvedValue({ id: 1, email: 'test@test.com' })
    }
}))
vi.mock('@/features/notifications/notification.service', () => ({
    notificationService: {
        getSummary: vi.fn().mockResolvedValue({ unread_count: 5 }),
        getNotifications: vi.fn().mockResolvedValue([])
    }
}))
vi.mock('next/navigation', () => ({
    usePathname: vi.fn().mockReturnValue('/notifications')
}))

describe('NotificationsPage', () => {
    it('should render the notifications page structure', async () => {
        render(<NotificationsPage />)

        expect(screen.getByTestId('sidebar')).toBeInTheDocument()
        expect(screen.getByTestId('header')).toBeInTheDocument()
        expect(screen.getByTestId('notification-inbox')).toBeInTheDocument()
        expect(screen.getByText(t.dashboard.nav.notifications, { selector: 'h2' })).toBeInTheDocument()
    })
})
