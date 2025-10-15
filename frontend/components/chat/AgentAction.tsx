'use client'

import { cn } from '../../lib/utils'

export interface AgentActionProps {
  agent: 'plume' | 'mimir'
  actionText: string
  status: 'running' | 'completed'
  timestamp: Date
}

function getAgentColor(agent: 'plume' | 'mimir') {
  return agent === 'plume' ? 'text-plume-500' : 'text-mimir-500'
}

function getAgentName(agent: 'plume' | 'mimir') {
  return agent === 'plume' ? 'Plume' : 'Mimir'
}

/**
 * AgentAction Component
 *
 * WhatsApp-style notification for agent actions (not messages)
 * Examples:
 * - "Mimir recherche dans les archives..."
 * - "Plume a créé une note"
 *
 * Style: Minimal, centered, no bubble
 * - Agent name in color (purple/green)
 * - Action text in neutral gray
 */
export function AgentAction({ agent, actionText, status }: AgentActionProps) {
  const agentColor = getAgentColor(agent)
  const agentName = getAgentName(agent)

  return (
    <div className="flex justify-center items-center py-2">
      <div className="flex items-center gap-1 text-sm">
        {/* Agent name (colored) */}
        <span className={cn('font-medium', agentColor)}>
          {agentName}
        </span>

        {/* Action text (neutral) */}
        <span className="text-gray-600 dark:text-gray-400">
          {actionText}
        </span>

        {/* Loading indicator for running status */}
        {status === 'running' && (
          <span className="ml-1 inline-flex gap-0.5">
            <span className="animate-pulse">.</span>
            <span className="animate-pulse delay-100">.</span>
            <span className="animate-pulse delay-200">.</span>
          </span>
        )}

        {/* Checkmark for completed status */}
        {status === 'completed' && (
          <span className="ml-1 text-green-500">✓</span>
        )}
      </div>
    </div>
  )
}
