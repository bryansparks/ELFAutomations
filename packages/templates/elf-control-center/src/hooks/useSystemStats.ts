import { useState, useEffect } from 'react'
import { api, DashboardData } from '@/services/api'

interface SystemStats {
  teams: {
    active: number
    total: number
    change: number
  }
  workflows: {
    running: number
    total: number
    change: number
  }
  costs: {
    daily: number
    monthly: number
    change: number
    budget_percentage: number
  }
  health: {
    score: number
    status: string
  }
}

export function useSystemStats() {
  const [data, setData] = useState<SystemStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    fetchData()

    // Set up polling for updates every 30 seconds
    const interval = setInterval(fetchData, 30000)

    // Set up WebSocket for real-time updates
    api.connectWebSocket((message) => {
      if (message.type === 'status_update') {
        updateSystemStats(message.data)
      }
    })

    return () => {
      clearInterval(interval)
      api.disconnectWebSocket()
    }
  }, [])

  const fetchData = async () => {
    try {
      const dashboard = await api.getDashboardData()
      setData(transformDashboardData(dashboard))
      setError(null)
    } catch (err) {
      setError(err as Error)
      console.error('Failed to fetch system stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const updateSystemStats = (statusData: any) => {
    setData(prev => {
      if (!prev) return prev
      return {
        ...prev,
        teams: {
          ...prev.teams,
          active: statusData.active_teams,
          total: statusData.total_teams,
        },
        workflows: {
          ...prev.workflows,
          running: statusData.active_workflows,
        },
        health: {
          score: statusData.health_score,
          status: statusData.status,
        },
      }
    })
  }

  const transformDashboardData = (dashboard: DashboardData): SystemStats => {
    // Calculate changes (mock for now, would compare with historical data)
    const teamChange = dashboard.system_status.active_teams > 5 ? 12 : -5
    const workflowChange = dashboard.system_status.active_workflows > 10 ? 8 : 3
    const costChange = dashboard.cost_metrics.trend === 'up' ? 15 :
                      dashboard.cost_metrics.trend === 'down' ? -10 : 0

    return {
      teams: {
        active: dashboard.system_status.active_teams,
        total: dashboard.system_status.total_teams,
        change: teamChange,
      },
      workflows: {
        running: dashboard.system_status.active_workflows,
        total: dashboard.workflows.length,
        change: workflowChange,
      },
      costs: {
        daily: dashboard.cost_metrics.today_cost,
        monthly: dashboard.cost_metrics.month_cost,
        change: costChange,
        budget_percentage: dashboard.cost_metrics.today_percentage,
      },
      health: {
        score: dashboard.system_status.health_score,
        status: dashboard.system_status.status,
      },
    }
  }

  return { data, loading, error, refetch: fetchData }
}
