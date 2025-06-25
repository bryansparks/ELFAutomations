'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Activity, CheckCircle, XCircle, AlertCircle, Server, Database, Cloud, Shield } from 'lucide-react'

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

const componentIcons = {
  system: Server,
  docker: Cloud,
  kubernetes: Cloud,
  database: Database,
  security: Shield,
}

export function SystemHealth() {
  const { data: health, isLoading, error } = useQuery({
    queryKey: ['system-health'],
    queryFn: api.getSystemHealth,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="h-20 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            Failed to load system health data
          </div>
        </CardContent>
      </Card>
    )
  }

  const overallHealth = health && Object.values(health).every((component: any) =>
    component.status === 'healthy'
  ) ? 'healthy' : 'degraded'

  return (
    <div className="space-y-4">
      {/* Overall Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>System Status</CardTitle>
              <CardDescription>
                Overall infrastructure health
              </CardDescription>
            </div>
            <div className={`flex items-center space-x-2 ${statusColors[overallHealth]}`}>
              <Activity className="h-6 w-6" />
              <span className="text-lg font-semibold capitalize">{overallHealth}</span>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Component Status Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {health && Object.entries(health).map(([component, status]: [string, any]) => {
          const Icon = componentIcons[component as keyof typeof componentIcons] || Server
          const StatusIcon = statusIcons[status.status as keyof typeof statusIcons] || AlertCircle
          const colorClass = statusColors[status.status as keyof typeof statusColors] || 'text-gray-500'

          return (
            <Card key={component}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Icon className="h-5 w-5 text-muted-foreground" />
                    <CardTitle className="text-base capitalize">{component}</CardTitle>
                  </div>
                  <StatusIcon className={`h-5 w-5 ${colorClass}`} />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-2">{status.message}</p>
                {status.details && (
                  <div className="space-y-1">
                    {Object.entries(status.details).map(([key, value]: [string, any]) => (
                      <div key={key} className="flex justify-between text-xs">
                        <span className="text-muted-foreground capitalize">
                          {key.replace(/_/g, ' ')}:
                        </span>
                        <span className="font-medium">
                          {typeof value === 'number' ?
                            value.toFixed(2) :
                            String(value)
                          }
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-2 text-xs text-muted-foreground">
                  Last checked: {new Date(status.timestamp).toLocaleTimeString()}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Infrastructure Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Infrastructure Metrics</CardTitle>
          <CardDescription>
            Resource utilization and performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">CPU Usage</span>
                <span className="text-sm font-medium">
                  {health?.system?.details?.cpu_percent || 0}%
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${health?.system?.details?.cpu_percent || 0}%` }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Memory Usage</span>
                <span className="text-sm font-medium">
                  {health?.system?.details?.memory_percent || 0}%
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${health?.system?.details?.memory_percent || 0}%` }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Disk Usage</span>
                <span className="text-sm font-medium">
                  {health?.system?.details?.disk_percent || 0}%
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${health?.system?.details?.disk_percent || 0}%` }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
