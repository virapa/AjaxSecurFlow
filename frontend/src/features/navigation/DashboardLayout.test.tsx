import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { DashboardLayout } from './DashboardLayout'

describe('DashboardLayout Component (Local Scope: Navigation)', () => {
    it('should render the sidebar and main content', () => {
        render(
            <DashboardLayout>
                <div>Dashboard Content</div>
            </DashboardLayout>
        )

        // Check for Sidebar (via navigation role)
        expect(screen.getByRole('navigation')).toBeInTheDocument()

        // Check for children content
        expect(screen.getByText(/dashboard content/i)).toBeInTheDocument()
    })

    it('should have a main tag for accessibility', () => {
        render(
            <DashboardLayout>
                <p>Content</p>
            </DashboardLayout>
        )

        expect(screen.getByRole('main')).toBeInTheDocument()
    })
})
