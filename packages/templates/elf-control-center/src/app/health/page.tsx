'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SystemHealth } from '@/components/system-health'
import { MetricCard } from '@/components/ui/metric-card'
import { useState, useEffect } from 'react'
import { api, SystemStatus } from '@/services/api'
import { Activity, Server, Database, Shield, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

export default function HealthPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchSystemStatus = async () => {
    try {
      const data = await api.getSystemStatus()
      setSystemStatus(data)
    } catch (error) {
      console.error('Failed to fetch system status:', error)
    } finally {
      setLoading(false)
    }
  }

  const getHealthIcon = (score: number) => {
    if (score > 90) return CheckCircle
    if (score > 70) return AlertTriangle
    return XCircle
  }

  const getHealthColor = (score: number) => {
    if (score > 90) return 'success'
    if (score > 70) return 'warning'
    return 'danger'
  }

  return (
    <PageTransition variant="slide">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">System Health</h1>
          <p className="text-muted-foreground mt-1">
            Monitor infrastructure and service health
          </p>
        </div>

        {/* Health Metrics */}
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard
            title="Overall Health"
            value={systemStatus?.health_score || 0}
            suffix="%"
            icon={<Activity className="h-4 w-4" />}
            color={getHealthColor(systemStatus?.health_score || 0)}
            animate
            loading={loading}
          />
          <MetricCard
            title="System Load"
            value={(systemStatus?.system_load || 0) * 100}
            suffix="%"
            icon={<Server className="h-4 w-4" />}
            color={systemStatus && systemStatus.system_load > 0.8 ? "warning" : "default"}
            animate
            loading={loading}
          />
          <MetricCard
            title="Active Teams"
            value={systemStatus?.active_teams || 0}
            suffix={`/${systemStatus?.total_teams || 0}`}
            icon={<Database className="h-4 w-4" />}
            color="info"
            animate
            loading={loading}
          />
          <MetricCard
            title="API Status"
            value={systemStatus?.status || 'unknown'}
            icon={<Shield className="h-4 w-4" />}
            color={systemStatus?.status === 'operational' ? 'success' : 'danger'}
            animate={false}
            loading={loading}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Infrastructure Health */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle>Infrastructure Status</CardTitle>
            </CardHeader>
            <CardContent>
              <SystemHealth />
            </CardContent>
          </Card>

          {/* API Availability */}
          <Card variant="gradient">
            <CardHeader>
              <CardTitle>API Availability</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {systemStatus && Object.entries(systemStatus.api_availability).map(([api, available]) => {
                  const Icon = available ? CheckCircle : XCircle
                  return (
                    <div key={api} className="flex items-center justify-between p-3 rounded-lg bg-background/50">
                      <div className="flex items-center gap-3">
                        <Icon className={`h-5 w-5 ${available ? 'text-green-500' : 'text-red-500'}`} />
                        <span className="font-medium capitalize">{api}</span>
                      </div>
                      <span className={`text-sm ${available ? 'text-green-500' : 'text-red-500'}`}>
                        {available ? 'Available' : 'Unavailable'}
                      </span>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Health History */}
        <Card variant="neu">
          <CardHeader>
            <CardTitle>Health Monitoring</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">System Checks</h3>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <span>Database Connections</span>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <span>Memory Usage</span>
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <span>CPU Usage</span>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <span>Disk Space</span>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Recent Incidents</h3>
                <p className="text-muted-foreground">No incidents in the last 24 hours</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
