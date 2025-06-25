'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { TeamHierarchy } from './team-hierarchy'
import { RecentWorkflows } from './recent-workflows'
import { CostTrend } from './cost-trend'
import { SystemStatus } from './system-status'

export function Overview() {
  const { data: teams } = useQuery({
    queryKey: ['team-hierarchy'],
    queryFn: api.getTeamHierarchy,
  })

  const { data: workflows } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.getWorkflows,
  })

  const { data: costs } = useQuery({
    queryKey: ['cost-analytics'],
    queryFn: api.getCostAnalytics,
  })

  const { data: health } = useQuery({
    queryKey: ['system-health'],
    queryFn: api.getSystemHealth,
  })

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Team Hierarchy</CardTitle>
            <CardDescription>
              Organizational structure of AI teams
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TeamHierarchy teams={teams} />
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>
              Infrastructure health overview
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SystemStatus health={health} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Cost Trends</CardTitle>
            <CardDescription>
              API usage costs over the last 7 days
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <CostTrend data={costs?.trends} />
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Workflows</CardTitle>
            <CardDescription>
              Latest workflow executions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RecentWorkflows workflows={workflows?.slice(0, 5)} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
