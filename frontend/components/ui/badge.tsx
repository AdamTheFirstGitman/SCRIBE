import React from 'react'

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outline' | 'success' | 'warning' | 'danger'
}

export function Badge({ className = '', variant = 'default', children, ...props }: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-800',
    outline: 'border border-gray-300 bg-transparent text-gray-700',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800'
  }

  return (
    <div
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}