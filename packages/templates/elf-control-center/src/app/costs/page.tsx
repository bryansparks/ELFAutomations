'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MetricCard } from '@/components/ui/metric-card'
import { CostTrends } from '@/components/cost-trends'
import { useState, useEffect } from 'react'
import { api, CostMetrics } from '@/services/api'
import { Loading } from '@/components/ui/loading'
import { DollarSign, TrendingUp, TrendingDown, AlertTriangle, Users } from 'lucide-react'

export default function CostsPage() {
  const [costData, setCostData] = useState<CostMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCostData()
  }, [])

  const fetchCostData = async () => {
    try {
      setLoading(true)
      const data = await api.getCostMetrics()
      setCostData(data)
    } catch (error) {
      console.error('Failed to fetch cost data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageTransition variant="slide">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Cost Center</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and optimize your AI API costs
          </p>
        </div>

        {/* Cost Metrics */}
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard
            title="Today's Cost"
            value={costData?.today_cost || 0}
            prefix="$"
            icon={<DollarSign className="h-4 w-4" />}
            color={costData && costData.today_percentage > 80 ? "warning" : "default"}
            animate
            loading={loading}
          />
          <MetricCard
            title="Budget Used"
            value={costData?.today_percentage || 0}
            suffix="%"
            icon={<AlertTriangle className="h-4 w-4" />}
            color={
              costData && costData.today_percentage > 90 ? "danger" :
              costData && costData.today_percentage > 70 ? "warning" : "success"
            }
            animate
            loading={loading}
          />
          <MetricCard
            title="Monthly Cost"
            value={costData?.month_cost || 0}
            prefix="$"
            icon={<DollarSign className="h-4 w-4" />}
            color="info"
            animate
            loading={loading}
          />
          <MetricCard
            title="Cost Trend"
            value={costData?.trend || 'stable'}
            icon={
              costData?.trend === 'up' ? <TrendingUp className="h-4 w-4" /> :
              costData?.trend === 'down' ? <TrendingDown className="h-4 w-4" /> :
              <DollarSign className="h-4 w-4" />
            }
            color={
              costData?.trend === 'up' ? "danger" :
              costData?.trend === 'down' ? "success" : "default"
            }
            animate={false}
            loading={loading}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Cost Trends Chart */}
          <Card variant="gradient" className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Cost Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <CostTrends />
            </CardContent>
          </Card>

          {/* Top Spending Teams */}
          <Card variant="glass" className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Top Spending Teams</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <Loading variant="dots" />
                </div>
              ) : (
                <div className="space-y-4">
                  {costData?.top_teams.map((team, index) => (
                    <div key={team.team_name} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-sm font-bold`}>
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium">{team.team_name}</p>
                          <p className="text-sm text-muted-foreground">
                            {team.request_count} requests
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{api.formatCurrency(team.total_cost)}</p>
                        <p className="text-sm text-muted-foreground">
                          {((team.total_cost / (costData?.today_cost || 1)) * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Budget Management */}
        <Card variant="neu">
          <CardHeader>
            <CardTitle>Budget Management</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <h3 className="font-semibold mb-4">Daily Budgets</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Total Daily Budget</span>
                    <span className="font-mono">{api.formatCurrency(costData?.today_budget || 200)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Remaining Today</span>
                    <span className="font-mono text-green-500">
                      {api.formatCurrency((costData?.today_budget || 200) - (costData?.today_cost || 0))}
                    </span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-4">Monthly Budgets</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Total Monthly Budget</span>
                    <span className="font-mono">{api.formatCurrency(costData?.month_budget || 6000)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Remaining This Month</span>
                    <span className="font-mono text-green-500">
                      {api.formatCurrency((costData?.month_budget || 6000) - (costData?.month_cost || 0))}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
