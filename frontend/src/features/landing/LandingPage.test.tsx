import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { LandingPage } from './LandingPage'
import { es as t } from '@/shared/i18n/es'

describe('LandingPage Component (Local Scope: Landing)', () => {
    it('should render the hero section with the main headline in Spanish', () => {
        render(<LandingPage />)

        const heading = screen.getByRole('heading', { level: 1 })
        expect(heading).toBeInTheDocument()
        expect(heading.textContent).toContain(t.landing.hero.titlePrimary)
        expect(heading.textContent).toContain(t.landing.hero.titleSecondary)
        expect(heading.textContent).toContain(t.landing.hero.titleTertiary)
    })

    it('should render the CTA buttons in the hero section', () => {
        render(<LandingPage />)
        expect(screen.getByRole('button', { name: new RegExp(t.landing.hero.ctaStart, 'i') })).toBeInTheDocument()
    })

    it('should render the capabilities section', () => {
        render(<LandingPage />)
        expect(screen.getByText(new RegExp(t.landing.capabilities.title, 'i'))).toBeInTheDocument()
    })

    it('should render the pricing section with tiered options', () => {
        render(<LandingPage />)
        expect(screen.getByText(new RegExp(t.landing.pricing.tag, 'i'))).toBeInTheDocument()
        // Use getAllByText as "Free" might appear multiple times (plans and stats)
        expect(screen.getAllByText(new RegExp(t.landing.pricing.plans[0].name, 'i')).length).toBeGreaterThan(0)
    })

    it('should render the navigation links', () => {
        render(<LandingPage />)
        expect(screen.getByRole('link', { name: new RegExp(t.common.features, 'i') })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: new RegExp(t.common.pricing, 'i') })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: new RegExp(t.common.login, 'i') })).toBeInTheDocument()
    })
})
