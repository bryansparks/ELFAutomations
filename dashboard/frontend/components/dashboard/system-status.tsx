'use client'

import { Activity, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface SystemStatusProps {
  health: any
}

export function SystemStatus({ health }: SystemStatusProps) {
  if (!health) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        Loading system status...
      </div>
    )
  }

  const statusIcons = {
    healthy: CheckCircle,
    degraded: AlertCircle,
    unhealthy: XCircle,
    unknown: AlertCircle,
  }

  const statusColors = {
    healthy: 'text-green-500',
    degraded: 'text-yellow-500',
    unhealthy: 'text-red-500',
    unknown: 'text-gray-500',
  }

  return (
    <div className="space-y-3">
      {Object.entries(health).map(([component, status]: [string, any]) => {
        const Icon = statusIcons[status.status as keyof typeof statusIcons] || AlertCircle
        const colorClass = statusColors[status.status as keyof typeof statusColors] || 'text-gray-500'

        return (
          <div key={component} className="flex items-center justify-between p-3 rounded-md bg-muted/50">
            <div className="flex items-center space-x-3">
              <Icon className={`h-5 w-5 ${colorClass}`} />
              <div>
                <p className="text-sm font-medium capitalize">{component}</p>
                <p className="text-xs text-muted-foreground">{status.message}</p>
              </div>
            </div>
            <span className={`text-xs font-medium ${colorClass}`}>
              {status.status.toUpperCase()}
            </span>
          </div>
        )
      })}
    </div>
  )
}
