'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Overview } from '@/components/dashboard/overview'
import { TeamManager } from '@/components/dashboard/team-manager'
import { WorkflowManager } from '@/components/dashboard/workflow-manager'
import { CostAnalytics } from '@/components/dashboard/cost-analytics'
import { SystemHealth } from '@/components/dashboard/system-health'
import { CommunicationHub } from '@/components/dashboard/communication-hub'
import { MCPRegistry } from '@/components/dashboard/mcp-registry'
import { StatsCards } from '@/components/dashboard/stats-cards'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useDashboardStore } from '@/stores/dashboard'
import { Brain, Workflow, DollarSign, Activity, MessageSquare, Puzzle } from 'lucide-react'

export default function DashboardPage() {
  const { connect, disconnect } = useWebSocket()
  const { stats, fetchStats } = useDashboardStore()

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    connect()

    // Fetch initial stats
    fetchStats()

    return () => {
      disconnect()
    }
  }, [connect, disconnect, fetchStats])

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="flex h-16 items-center px-4">
          <h1 className="text-2xl font-bold">ELF Automations Dashboard</h1>
          <div className="ml-auto flex items-center space-x-4">
            <span className="text-sm text-muted-foreground">
              Central Command Center
            </span>
          </div>
        </div>
      </div>

      <div className="p-8 space-y-8">
        {/* Stats Overview */}
        <StatsCards stats={stats} />

        {/* Main Dashboard Tabs */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="teams" className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Teams
            </TabsTrigger>
            <TabsTrigger value="workflows" className="flex items-center gap-2">
              <Workflow className="h-4 w-4" />
              Workflows
            </TabsTrigger>
            <TabsTrigger value="costs" className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Costs
            </TabsTrigger>
            <TabsTrigger value="health" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Health
            </TabsTrigger>
            <TabsTrigger value="communications" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Comms
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Overview />
          </TabsContent>

          <TabsContent value="teams" className="space-y-4">
            <TeamManager />
          </TabsContent>

          <TabsContent value="workflows" className="space-y-4">
            <WorkflowManager />
          </TabsContent>

          <TabsContent value="costs" className="space-y-4">
            <CostAnalytics />
          </TabsContent>

          <TabsContent value="health" className="space-y-4">
            <SystemHealth />
          </TabsContent>

          <TabsContent value="communications" className="space-y-4">
            <CommunicationHub />
          </TabsContent>
        </Tabs>

        {/* MCP Registry (always visible) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Puzzle className="h-5 w-5" />
              MCP Registry
            </CardTitle>
            <CardDescription>
              Available Model Context Protocol servers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <MCPRegistry />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
