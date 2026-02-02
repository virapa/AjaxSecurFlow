import React from 'react'

interface CardProps {
    children: React.ReactNode
    header?: React.ReactNode
    footer?: React.ReactNode
    className?: string
}

/**
 * Standard Atomic Card Component for structural layout.
 * GLOBAL SCOPE: shared/components
 */
export const Card: React.FC<CardProps> = ({
    children,
    header,
    footer,
    className = '',
}) => {
    const baseCardStyles = 'rounded-lg border bg-white shadow-sm dark:border-gray-800 dark:bg-gray-950 text-gray-900 dark:text-gray-100'
    const combinedClasses = `${baseCardStyles} ${className}`

    return (
        <div className={combinedClasses}>
            {header && (
                <div className="flex flex-col space-y-1.5 p-6 border-b dark:border-gray-800">
                    {header}
                </div>
            )}
            <div className="p-6">
                {children}
            </div>
            {footer && (
                <div className="flex items-center p-6 border-t dark:border-gray-800">
                    {footer}
                </div>
            )}
        </div>
    )
}
