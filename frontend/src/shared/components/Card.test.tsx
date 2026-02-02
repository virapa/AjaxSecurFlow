import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Card } from './Card'

describe('Card Component', () => {
    it('should render content correctly', () => {
        render(
            <Card>
                <div>Test Content</div>
            </Card>
        )

        expect(screen.getByText(/test content/i)).toBeInTheDocument()
    })

    it('should render header and footer when provided', () => {
        render(
            <Card
                header={<h2>Title</h2>}
                footer={<p>Footer Text</p>}
            >
                Body content
            </Card>
        )

        expect(screen.getByRole('heading', { level: 2, name: /title/i })).toBeInTheDocument()
        expect(screen.getByText(/footer text/i)).toBeInTheDocument()
        expect(screen.getByText(/body content/i)).toBeInTheDocument()
    })

    it('should apply custom className', () => {
        const { container } = render(<Card className="custom-class">Content</Card>)

        expect(container.firstChild).toHaveClass('custom-class')
    })
})
