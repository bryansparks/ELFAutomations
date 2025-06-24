'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MetricCard } from '@/components/ui/metric-card'
import { useState, useEffect } from 'react'
import { api, WorkflowStatus } from '@/services/api'
import { Loading } from '@/components/ui/loading'
import { Plus, Workflow, Play, Pause, RefreshCw, Clock, CheckCircle, XCircle } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowStatus[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchWorkflows()
  }, [])

  const fetchWorkflows = async () => {
    try {
      setLoading(true)
      const data = await api.getWorkflows()
      setWorkflows(data)
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  const activeWorkflows = workflows.filter(w => w.status === 'active').length
  const totalExecutions = workflows.reduce((sum, w) => sum + w.executions_today, 0)
  const avgSuccessRate = workflows.reduce((sum, w) => sum + w.success_rate, 0) / workflows.length || 0

  // Prepare chart data
  const chartData = workflows.map(w => ({
    name: w.name.length > 20 ? w.name.substring(0, 20) + '...' : w.name,
    executions: w.executions_today,
    success: w.success_rate
  }))

  return (
    <PageTransition variant="fade">
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Workflow Management</h1>
            <p className="text-muted-foreground mt-1">
              Monitor and control your N8N workflows
            </p>
          </div>
          <Button variant="gradient" className="gap-2">
            <Plus className="h-4 w-4" />
            Create Workflow
          </Button>
        </div>

        {/* Metrics */}
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard
            title="Active Workflows"
            value={activeWorkflows}
            icon={<Workflow className="h-4 w-4" />}
            color="success"
            animate
            loading={loading}
          />
          <MetricCard
            title="Total Executions"
            value={totalExecutions}
            suffix=" today"
            icon={<RefreshCw className="h-4 w-4" />}
            color="info"
            animate
            loading={loading}
          />
          <MetricCard
            title="Success Rate"
            value={avgSuccessRate}
            suffix="%"
            icon={<CheckCircle className="h-4 w-4" />}
            color={avgSuccessRate > 90 ? "success" : avgSuccessRate > 70 ? "warning" : "danger"}
            animate
            loading={loading}
          />
          <MetricCard
            title="Avg Duration"
            value={workflows.reduce((sum, w) => sum + w.avg_duration, 0) / workflows.length || 0}
            suffix="s"
            icon={<Clock className="h-4 w-4" />}
            color="default"
            animate
            loading={loading}
          />
        </div>

        {/* Workflow Chart */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Workflow Executions Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="name"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                  />
                  <YAxis tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                  <Tooltip />
                  <Bar dataKey="executions" fill="#a855f7" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Workflow List */}
        <Card variant="gradient">
          <CardHeader>
            <CardTitle>All Workflows</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <Loading variant="pulse" />
              </div>
            ) : (
              <div className="space-y-4">
                {workflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-background/50 hover:bg-accent transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <Workflow className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-semibold">{workflow.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {workflow.executions_today} executions • {workflow.success_rate}% success rate
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">Last run</p>
                        <p className="text-sm">
                          {workflow.last_run ? new Date(workflow.last_run).toLocaleTimeString() : 'Never'}
                        </p>
                      </div>
                      <span className={cn(
                        "px-2 py-1 text-xs rounded-full",
                        workflow.status === 'active'
                          ? "bg-green-500/20 text-green-500"
                          : "bg-gray-500/20 text-gray-500"
                      )}>
                        {workflow.status}
                      </span>
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost">
                          {workflow.status === 'active' ? (
                            <Pause className="h-4 w-4" />
                          ) : (
                            <Play className="h-4 w-4" />
                          )}
                        </Button>
                        <Button size="sm" variant="ghost">
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}
