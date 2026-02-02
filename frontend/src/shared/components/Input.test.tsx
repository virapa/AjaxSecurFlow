import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Input } from './Input'

describe('Input Component', () => {
    it('should render correctly with a label', () => {
        render(<Input label="Email" placeholder="Enter your email" />)

        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
        expect(screen.getByPlaceholderText(/enter your email/i)).toBeInTheDocument()
    })

    it('should call onChange handler when typing', () => {
        const handleChange = vi.fn()
        render(<Input label="Name" onChange={handleChange} />)

        const input = screen.getByLabelText(/name/i)
        fireEvent.change(input, { target: { value: 'John Doe' } })

        expect(handleChange).toHaveBeenCalled()
    })

    it('should display an error message when error prop is provided', () => {
        render(<Input label="Password" error="Password is too short" />)

        expect(screen.getByText(/password is too short/i)).toBeInTheDocument()
    })

    it('should be disabled when disabled prop is true', () => {
        render(<Input label="Username" disabled />)

        const input = screen.getByLabelText(/username/i)
        expect(input).toBeDisabled()
    })

    it('should render as password type when type="password"', () => {
        render(<Input label="Pass" type="password" />)

        const input = screen.getByLabelText(/pass/i)
        expect(input).toHaveAttribute('type', 'password')
    })
})
