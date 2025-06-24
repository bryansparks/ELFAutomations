'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { MetricCard } from '@/components/ui/metric-card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loading } from '@/components/ui/loading'
import { Users, Workflow, DollarSign, Activity, Brain, Network, Server, Shield } from 'lucide-react'
import { TeamHierarchy } from '@/components/team-hierarchy'
import { CostTrends } from '@/components/cost-trends'
import { WorkflowStatus } from '@/components/workflow-status'
import { SystemHealth } from '@/components/system-health'
import { RecentActivity } from '@/components/recent-activity'
import { useSystemStats } from '@/hooks/useSystemStats'

export default function DashboardPage() {
  const { data: stats, loading } = useSystemStats()

  return (
    <PageTransition variant="fade">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gradient">ElfAutomations.ai Control Center</h1>
          <p className="text-muted-foreground mt-1">
            Real-time monitoring and control of your autonomous AI ecosystem
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Active Teams"
            value={stats?.teams?.active || 0}
            change={stats?.teams?.change}
            changeLabel="from last week"
            icon={<Users className="h-4 w-4" />}
            color="info"
            animate
            loading={loading}
          />
          <MetricCard
            title="Workflows Running"
            value={stats?.workflows?.running || 0}
            change={stats?.workflows?.change}
            icon={<Workflow className="h-4 w-4" />}
            color="success"
            animate
            loading={loading}
          />
          <MetricCard
            title="Daily Cost"
            value={stats?.costs?.daily || 0}
            prefix="$"
            change={stats?.costs?.change}
            changeLabel="vs yesterday"
            icon={<DollarSign className="h-4 w-4" />}
            color={stats?.costs?.change > 10 ? "warning" : "default"}
            animate
            loading={loading}
          />
          <MetricCard
            title="System Health"
            value={stats?.health?.score || 0}
            suffix="%"
            icon={<Activity className="h-4 w-4" />}
            color={stats?.health?.score > 90 ? "success" : stats?.health?.score > 70 ? "warning" : "danger"}
            animate
            loading={loading}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Team Hierarchy */}
          <Card variant="glass" hover="lift" className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Team Hierarchy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <TeamHierarchy />
            </CardContent>
          </Card>

          {/* Cost Trends */}
          <Card variant="gradient" hover="glow" className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Cost Analytics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CostTrends />
            </CardContent>
          </Card>

          {/* Workflow Status */}
          <Card variant="glass" hover="lift">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Workflow className="h-5 w-5" />
                Workflow Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <WorkflowStatus />
            </CardContent>
          </Card>

          {/* System Health */}
          <Card variant="neu" hover="lift">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                Infrastructure Health
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SystemHealth />
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <Card variant="glass" hover="none">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <RecentActivity />
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
