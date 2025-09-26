import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-plume-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950 disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default: "bg-plume-500 text-white hover:bg-plume-600 active:bg-plume-700 shadow-sm hover:shadow-md",
        secondary: "bg-gray-800 text-gray-200 hover:bg-gray-700 border border-gray-600 hover:border-gray-500",
        outline: "border border-gray-700 bg-transparent text-gray-300 hover:bg-gray-800 hover:text-gray-100",
        ghost: "text-gray-300 hover:bg-gray-800/50 hover:text-gray-100",
        destructive: "bg-red-600 text-white hover:bg-red-700 active:bg-red-800",
        mimir: "bg-mimir-500 text-white hover:bg-mimir-600 active:bg-mimir-700 shadow-sm hover:shadow-md",
        link: "text-plume-400 underline-offset-4 hover:underline hover:text-plume-300"
      },
      size: {
        sm: "h-8 px-3 text-sm rounded-md",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10 p-0"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "md"
    }
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }