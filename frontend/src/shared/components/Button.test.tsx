import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Button } from './Button'

describe('Button Component', () => {
    it('should render correctly with text content', () => {
        render(<Button>Click me</Button>)

        const button = screen.getByRole('button', { name: /click me/i })
        expect(button).toBeInTheDocument()
    })

    it('should call onClick handler when clicked', () => {
        const handleClick = vi.fn()
        render(<Button onClick={handleClick}>Post</Button>)

        const button = screen.getByRole('button', { name: /post/i })
        fireEvent.click(button)

        expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should be disabled when the disabled prop is true', () => {
        render(<Button disabled>Disabled Button</Button>)

        const button = screen.getByRole('button', { name: /disabled button/i })
        expect(button).toBeDisabled()
    })

    it('should have basic accessibility attributes', () => {
        render(<Button aria-label="custom label">Icon Button</Button>)

        const button = screen.getByRole('button', { name: /custom label/i })
        expect(button).toBeInTheDocument()
    })
})
