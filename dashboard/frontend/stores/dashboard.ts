import { create } from 'zustand'
import { api } from '@/lib/api'

interface DashboardStats {
  totalTeams: number
  activeTeams: number
  totalWorkflows: number
  workflowsToday: number
  totalCostToday: number
  apiCallsToday: number
  systemHealth: string
  activeMcps: number
}

interface DashboardStore {
  stats: DashboardStats | null
  isLoading: boolean
  error: string | null

  fetchStats: () => Promise<void>
  updateStats: (stats: Partial<DashboardStats>) => void
  setError: (error: string | null) => void
}

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  stats: null,
  isLoading: false,
  error: null,

  fetchStats: async () => {
    set({ isLoading: true, error: null })
    try {
      const stats = await api.getStats()
      set({
        stats: {
          totalTeams: stats.total_teams,
          activeTeams: stats.active_teams,
          totalWorkflows: stats.total_workflows,
          workflowsToday: stats.workflows_today,
          totalCostToday: stats.total_cost_today,
          apiCallsToday: stats.api_calls_today,
          systemHealth: stats.system_health,
          activeMcps: stats.active_mcps,
        },
        isLoading: false
      })
    } catch (error: any) {
      set({
        error: error.message || 'Failed to fetch stats',
        isLoading: false
      })
    }
  },

  updateStats: (newStats) => {
    const currentStats = get().stats
    if (currentStats) {
      set({
        stats: {
          ...currentStats,
          ...newStats
        }
      })
    }
  },

  setError: (error) => set({ error }),
}))
