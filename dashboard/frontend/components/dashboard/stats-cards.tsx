import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Brain, Workflow, DollarSign, Activity } from 'lucide-react'

interface StatsCardsProps {
  stats: {
    totalTeams: number
    activeTeams: number
    totalWorkflows: number
    workflowsToday: number
    totalCostToday: number
    apiCallsToday: number
    systemHealth: string
    activeMcps: number
  } | null
}

export function StatsCards({ stats }: StatsCardsProps) {
  if (!stats) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  const cards = [
    {
      title: 'Active Teams',
      value: `${stats.activeTeams} / ${stats.totalTeams}`,
      icon: Brain,
      description: 'AI teams running',
      color: 'text-blue-500',
    },
    {
      title: 'Workflows Today',
      value: stats.workflowsToday.toString(),
      icon: Workflow,
      description: `of ${stats.totalWorkflows} total`,
      color: 'text-green-500',
    },
    {
      title: 'Cost Today',
      value: `$${stats.totalCostToday.toFixed(2)}`,
      icon: DollarSign,
      description: `${stats.apiCallsToday} API calls`,
      color: stats.totalCostToday > 100 ? 'text-red-500' : 'text-yellow-500',
    },
    {
      title: 'System Health',
      value: stats.systemHealth.charAt(0).toUpperCase() + stats.systemHealth.slice(1),
      icon: Activity,
      description: `${stats.activeMcps} MCPs active`,
      color: stats.systemHealth === 'healthy' ? 'text-green-500' : 'text-red-500',
    },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, index) => (
        <Card key={index}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
            <p className="text-xs text-muted-foreground">{card.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
