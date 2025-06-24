'use client'

import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts'
import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { api, CostMetrics } from '@/services/api'
import { Loading } from '@/components/ui/loading'

const COLORS = ['#0ea5e9', '#a855f7', '#f59e0b', '#10b981', '#ef4444']

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-card p-3 rounded-lg shadow-lg border border-border"
      >
        <p className="font-semibold">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: ${entry.value}
          </p>
        ))}
      </motion.div>
    )
  }
  return null
}

export function CostTrends() {
  const [costData, setCostData] = useState<CostMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState<'hourly' | 'model'>('hourly')

  useEffect(() => {
    fetchCostData()
  }, [])

  const fetchCostData = async () => {
    try {
      setLoading(true)
      const data = await api.getCostMetrics()
      setCostData(data)
    } catch (err) {
      console.error('Failed to fetch cost data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[300px]">
        <Loading variant="pulse" />
      </div>
    )
  }

  if (!costData) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No cost data available
      </div>
    )
  }

  // Transform hourly data for line chart
  const hourlyData = costData.hourly_costs.map(item => ({
    hour: `${item.hour}:00`,
    cost: item.cost,
    requests: item.requests
  }))

  // Transform model data for pie chart
  const modelData = Object.entries(costData.cost_by_model).map(([model, cost]) => ({
    name: model,
    value: cost
  }))

  return (
    <div>
      {/* View Toggle */}
      <div className="flex justify-end mb-4 gap-2">
        <button
          onClick={() => setView('hourly')}
          className={`px-3 py-1 text-xs rounded-md transition-colors ${
            view === 'hourly'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          Hourly Trend
        </button>
        <button
          onClick={() => setView('model')}
          className={`px-3 py-1 text-xs rounded-md transition-colors ${
            view === 'model'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          By Model
        </button>
      </div>

      {/* Cost Summary */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <p className="text-sm text-muted-foreground">Today</p>
          <p className="text-xl font-bold">{api.formatCurrency(costData.today_cost)}</p>
          <p className="text-xs text-muted-foreground">
            {api.formatPercentage(costData.today_percentage)} of budget
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-muted-foreground">Month</p>
          <p className="text-xl font-bold">{api.formatCurrency(costData.month_cost)}</p>
        </div>
        <div className="text-center">
          <p className="text-sm text-muted-foreground">Trend</p>
          <p className={`text-xl font-bold ${
            costData.trend === 'up' ? 'text-red-500' :
            costData.trend === 'down' ? 'text-green-500' :
            'text-yellow-500'
          }`}>
            {costData.trend === 'up' ? '↑' : costData.trend === 'down' ? '↓' : '→'}
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="h-[200px] w-full">
        {view === 'hourly' ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={hourlyData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="hour"
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="cost"
                stroke="#a855f7"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                name="Cost ($)"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={modelData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {modelData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => api.formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
