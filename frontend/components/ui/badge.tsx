import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "bg-gray-800 text-gray-200 hover:bg-gray-700",
        secondary: "bg-gray-700 text-gray-300 hover:bg-gray-600",
        outline: "border border-gray-700 bg-transparent text-gray-300 hover:bg-gray-800",
        success: "bg-mimir-500/20 text-mimir-300 border border-mimir-500/30",
        warning: "bg-yellow-500/20 text-yellow-300 border border-yellow-500/30",
        danger: "bg-red-500/20 text-red-300 border border-red-500/30",
        plume: "bg-plume-500/20 text-plume-300 border border-plume-500/30",
        mimir: "bg-mimir-500/20 text-mimir-300 border border-mimir-500/30"
      },
      size: {
        sm: "px-2 py-0.5 text-xs",
        md: "px-2.5 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "md"
    }
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant, size }), className)} {...props} />
  )
}

export { Badge, badgeVariants }