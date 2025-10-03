import { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
}

export function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="rounded-full bg-gray-200 dark:bg-gray-800 p-4 mb-4">
        <Icon className="h-8 w-8 text-gray-500 dark:text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-200 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 max-w-sm">{description}</p>
      )}
    </div>
  )
}
