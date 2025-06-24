'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MetricCard } from '@/components/ui/metric-card'
import { Loading } from '@/components/ui/loading'
import { Network, Plus, Server, Shield, Activity, Power } from 'lucide-react'
import Link from 'next/link'

export default function MCPsPage() {
  // Mock data for now
  const mcps = [
    { id: '1', name: 'File System MCP', type: 'internal', status: 'active', endpoints: 12, calls_today: 1250 },
    { id: '2', name: 'Database MCP', type: 'internal', status: 'active', endpoints: 8, calls_today: 890 },
    { id: '3', name: 'Slack MCP', type: 'external', status: 'active', endpoints: 6, calls_today: 456 },
    { id: '4', name: 'GitHub MCP', type: 'external', status: 'inactive', endpoints: 15, calls_today: 0 },
  ]

  const activeMCPs = mcps.filter(m => m.status === 'active').length
  const totalCalls = mcps.reduce((sum, m) => sum + m.calls_today, 0)

  return (
    <PageTransition variant="fade">
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">MCP Management</h1>
            <p className="text-muted-foreground mt-1">
              Model Context Protocol servers for tool access
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/mcps/create">
              <Button variant="gradient" className="gap-2">
                <Plus className="h-4 w-4" />
                Create Internal MCP
              </Button>
            </Link>
            <Link href="/mcps/discover">
              <Button variant="outline" className="gap-2">
                <Network className="h-4 w-4" />
                Discover Public MCPs
              </Button>
            </Link>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard
            title="Active MCPs"
            value={activeMCPs}
            icon={<Network className="h-4 w-4" />}
            color="success"
            animate
          />
          <MetricCard
            title="Total Endpoints"
            value={mcps.reduce((sum, m) => sum + m.endpoints, 0)}
            icon={<Server className="h-4 w-4" />}
            color="info"
            animate
          />
          <MetricCard
            title="API Calls Today"
            value={totalCalls}
            icon={<Activity className="h-4 w-4" />}
            color="default"
            animate
          />
          <MetricCard
            title="Avg Response Time"
            value={125}
            suffix="ms"
            icon={<Activity className="h-4 w-4" />}
            color="warning"
            animate
          />
        </div>

        {/* MCP Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {mcps.map((mcp) => (
            <Card key={mcp.id} variant={mcp.status === 'active' ? 'gradient' : 'glass'} hover="lift">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2">
                    <Network className="h-5 w-5" />
                    <CardTitle className="text-lg">{mcp.name}</CardTitle>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    mcp.status === 'active'
                      ? 'bg-green-500/20 text-green-500'
                      : 'bg-gray-500/20 text-gray-500'
                  }`}>
                    {mcp.status}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Type</span>
                    <span className="text-sm font-medium">{mcp.type}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Endpoints</span>
                    <span className="text-sm font-medium">{mcp.endpoints}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Calls Today</span>
                    <span className="text-sm font-medium">{mcp.calls_today.toLocaleString()}</span>
                  </div>
                  <div className="pt-3 flex gap-2">
                    <Button size="sm" variant={mcp.status === 'active' ? 'outline' : 'default'} className="flex-1">
                      <Power className="h-3 w-3 mr-1" />
                      {mcp.status === 'active' ? 'Stop' : 'Start'}
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      View Logs
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* MCP Details */}
        <Card variant="neu">
          <CardHeader>
            <CardTitle>MCP Architecture</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <p>MCPs (Model Context Protocol servers) provide structured tool access to teams:</p>
              <ul>
                <li><strong>Internal MCPs</strong>: File system, database, and infrastructure access</li>
                <li><strong>External MCPs</strong>: Third-party integrations like Slack, GitHub, and cloud services</li>
                <li><strong>AgentGateway</strong>: Routes all MCP requests with authentication and rate limiting</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
