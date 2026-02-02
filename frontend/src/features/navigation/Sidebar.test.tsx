import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Sidebar } from './Sidebar'

describe('Sidebar Component (Local Scope: Navigation)', () => {
    it('should render all navigation links', () => {
        render(<Sidebar />)

        // Check for navigation role
        expect(screen.getByRole('navigation')).toBeInTheDocument()

        // Check for specific links (using regex for flexibility with translations or icons)
        expect(screen.getByRole('link', { name: /panel/i })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: /hubs/i })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: /facturación/i })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: /notificaciones/i })).toBeInTheDocument()
    })

    it('should render the brand name or logo', () => {
        render(<Sidebar />)
        expect(screen.getByText(/ajaxsecurflow/i)).toBeInTheDocument()
    })

    it('should contain a logout button', () => {
        render(<Sidebar />)
        expect(screen.getByRole('button', { name: /salir/i })).toBeInTheDocument()
    })
})
