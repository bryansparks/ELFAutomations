import React from 'react'
import { cn } from '@/lib/utils'
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  Play,
  Pause,
  Archive,
  Upload,
  Loader2
} from 'lucide-react'

interface StateBadgeProps {
  state: string
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  className?: string
}

const stateConfig: Record<string, {
  label: string
  color: string
  bgColor: string
  icon: React.ElementType
}> = {
  // Common states
  created: {
    label: 'Created',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    icon: Clock
  },
  registered: {
    label: 'Registered',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    icon: CheckCircle
  },
  building: {
    label: 'Building',
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    icon: RefreshCw
  },
  built: {
    label: 'Built',
    color: 'text-indigo-700',
    bgColor: 'bg-indigo-100',
    icon: CheckCircle
  },
  deploying: {
    label: 'Deploying',
    color: 'text-purple-700',
    bgColor: 'bg-purple-100',
    icon: Upload
  },
  deployed: {
    label: 'Deployed',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    icon: CheckCircle
  },
  active: {
    label: 'Active',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    icon: Play
  },
  inactive: {
    label: 'Inactive',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    icon: Pause
  },
  failed: {
    label: 'Failed',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    icon: XCircle
  },
  error: {
    label: 'Error',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    icon: XCircle
  },
  archived: {
    label: 'Archived',
    color: 'text-gray-500',
    bgColor: 'bg-gray-50',
    icon: Archive
  },

  // Workflow-specific states
  validating: {
    label: 'Validating',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    icon: Loader2
  },
  validated: {
    label: 'Validated',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    icon: CheckCircle
  },
  failed_validation: {
    label: 'Validation Failed',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    icon: XCircle
  },

  // MCP-specific states
  health_checking: {
    label: 'Health Check',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    icon: RefreshCw
  },
  available: {
    label: 'Available',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    icon: CheckCircle
  },

  // Team-specific states
  awaiting_dependencies: {
    label: 'Awaiting Dependencies',
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    icon: AlertCircle
  },
  scaling: {
    label: 'Scaling',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    icon: RefreshCw
  }
}

export function StateBadge({ state, size = 'md', showIcon = true, className }: StateBadgeProps) {
  const config = stateConfig[state] || {
    label: state,
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    icon: AlertCircle
  }

  const Icon = config.icon

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5'
  }

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  }

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 rounded-full font-medium',
      config.bgColor,
      config.color,
      sizeClasses[size],
      className
    )}>
      {showIcon && (
        <Icon className={cn(
          iconSizes[size],
          state === 'validating' || state === 'building' || state === 'health_checking' || state === 'scaling'
            ? 'animate-spin'
            : ''
        )} />
      )}
      {config.label}
    </span>
  )
}

export function getStateColor(state: string): string {
  const config = stateConfig[state]
  return config?.color || 'text-gray-700'
}

export function getStateBgColor(state: string): string {
  const config = stateConfig[state]
  return config?.bgColor || 'bg-gray-100'
}
