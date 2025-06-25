'use client'

import { Workflow, CheckCircle, XCircle, Clock } from 'lucide-react'
import { format } from 'date-fns'

interface RecentWorkflowsProps {
  workflows: any[] | undefined
}

export function RecentWorkflows({ workflows }: RecentWorkflowsProps) {
  if (!workflows || workflows.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No recent workflow executions
      </div>
    )
  }

  const statusIcons = {
    success: CheckCircle,
    failed: XCircle,
    running: Clock,
  }

  const statusColors = {
    success: 'text-green-500',
    failed: 'text-red-500',
    running: 'text-yellow-500',
  }

  return (
    <div className="space-y-2">
      {workflows.map((workflow: any, index: number) => {
        const Icon = statusIcons[workflow.status as keyof typeof statusIcons] || Clock
        const colorClass = statusColors[workflow.status as keyof typeof statusColors] || 'text-gray-500'

        return (
          <div key={index} className="flex items-center space-x-3 p-2 rounded-md hover:bg-muted/50 transition-colors">
            <Icon className={`h-4 w-4 ${colorClass}`} />
            <div className="flex-1">
              <p className="text-sm font-medium">{workflow.workflow_name || workflow.name}</p>
              <p className="text-xs text-muted-foreground">
                {workflow.owner_team} • {workflow.last_execution ? format(new Date(workflow.last_execution), 'MMM d, h:mm a') : 'Never run'}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">
                {workflow.duration_seconds ? `${workflow.duration_seconds}s` : '-'}
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
