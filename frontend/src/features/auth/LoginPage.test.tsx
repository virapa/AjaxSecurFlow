import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import LoginPage from './LoginPage'
import { authService } from './auth.service'

// Mock the local auth service
vi.mock('./auth.service', () => ({
    authService: {
        login: vi.fn()
    }
}))

// Mock next/navigation
vi.mock('next/navigation', () => ({
    useRouter: () => ({
        push: vi.fn()
    })
}))

describe('LoginPage Component (Local Scope: Auth)', () => {
    it('should render the login form with all required fields', () => {
        render(<LoginPage />)

        expect(screen.getByRole('heading', { name: /acceso al gateway/i })).toBeInTheDocument()
        expect(screen.getByLabelText(/email de tu cuenta ajax/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /entrar al panel/i })).toBeInTheDocument()
    })

    it('should display the instruction text', () => {
        render(<LoginPage />)
        expect(screen.getByText(/utiliza exactamente el mismo email/i)).toBeInTheDocument()
    })

    it('should call authService.login with credentials when form is submitted', async () => {
        const loginMock = vi.mocked(authService.login).mockResolvedValue({ success: true })
        render(<LoginPage />)

        fireEvent.change(screen.getByLabelText(/email de tu cuenta ajax/i), {
            target: { value: 'test@example.com' }
        })
        fireEvent.change(screen.getByLabelText(/contraseña/i), {
            target: { value: 'password123' }
        })

        fireEvent.click(screen.getByRole('button', { name: /entrar/i }))

        await waitFor(() => {
            expect(loginMock).toHaveBeenCalledWith('test@example.com', 'password123')
        })
    })
})
