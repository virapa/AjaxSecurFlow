import SupportComponent from '@/features/support/SupportComponent'
import { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'Soporte Técnico | AjaxSecurFlow',
    description: 'Contacta con nuestro equipo de soporte para resolver dudas o reportar bugs.',
}

export default function SupportPage() {
    return <SupportComponent />
}
