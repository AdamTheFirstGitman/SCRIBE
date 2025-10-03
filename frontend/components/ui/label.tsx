import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const labelVariants = cva(
  "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
  {
    variants: {
      variant: {
        default: "text-gray-900 dark:text-gray-200",
        muted: "text-gray-600 dark:text-gray-400",
        accent: "text-plume-600 dark:text-plume-300"
      }
    },
    defaultVariants: {
      variant: "default"
    }
  }
)

export interface LabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement>,
    VariantProps<typeof labelVariants> {}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, variant, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(labelVariants({ variant }), className)}
      {...props}
    />
  )
)
Label.displayName = "Label"

export { Label }