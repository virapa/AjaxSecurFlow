import React, { useId } from 'react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string
    error?: string
}

/**
 * Standard Atomic Input Component with Label and Error support.
 * GLOBAL SCOPE: shared/components
 */
export const Input: React.FC<InputProps> = ({
    label,
    error,
    className = '',
    id: customId,
    disabled,
    ...props
}) => {
    const generatedId = useId()
    const id = customId || generatedId

    const baseInputStyles = 'flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-950 dark:ring-offset-gray-950 dark:placeholder:text-gray-400'

    const errorStyles = error
        ? 'border-red-500 focus-visible:ring-red-500 dark:border-red-900'
        : ''

    const combinedInputClasses = `${baseInputStyles} ${errorStyles} ${className}`

    return (
        <div className="grid w-full items-center gap-1.5">
            {label && (
                <label
                    htmlFor={id}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 dark:text-gray-100"
                >
                    {label}
                </label>
            )}
            <input
                id={id}
                className={combinedInputClasses}
                disabled={disabled}
                {...props}
            />
            {error && (
                <p className="text-xs font-medium text-red-500 dark:text-red-400">
                    {error}
                </p>
            )}
        </div>
    )
}
