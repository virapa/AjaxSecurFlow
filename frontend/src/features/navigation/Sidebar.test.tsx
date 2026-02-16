import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Sidebar } from './Sidebar'
import { es as t } from '@/shared/i18n/es'

describe('Sidebar Component (Local Scope: Navigation)', () => {
    it('should render all navigation links', () => {
        render(<Sidebar />)

        // Check for navigation role
        expect(screen.getByRole('navigation')).toBeInTheDocument()

        // Check for specific links (using regex for flexibility with translations or icons)
        expect(screen.getByRole('link', { name: new RegExp(t.dashboard.nav.dashboard, 'i') })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: new RegExp(t.dashboard.nav.notifications, 'i') })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: new RegExp(t.dashboard.nav.subscription, 'i') })).toBeInTheDocument()
    })

    it('should render the brand name or logo', () => {
        render(<Sidebar />)
        expect(screen.getByText(/ajaxsecurflow/i)).toBeInTheDocument()
    })

    it('should NOT contain a logout button (moved to header)', () => {
        render(<Sidebar />)
        expect(screen.queryByRole('button', { name: /salir/i })).not.toBeInTheDocument()
    })
})
