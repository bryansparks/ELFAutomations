'use client'

import { motion } from 'framer-motion'
import { Check, AlertTriangle, X } from 'lucide-react'
// Progress component defined locally below

interface HealthMetric {
  name: string
  status: 'healthy' | 'warning' | 'critical'
  value: number
  details: string
}

const metrics: HealthMetric[] = [
  { name: 'API Gateway', status: 'healthy', value: 99.9, details: 'Response time: 45ms' },
  { name: 'Database', status: 'healthy', value: 98.5, details: 'Connections: 12/100' },
  { name: 'Kubernetes', status: 'warning', value: 85.2, details: 'High memory usage' },
  { name: 'Redis Cache', status: 'healthy', value: 99.8, details: 'Hit rate: 94%' },
  { name: 'Message Queue', status: 'critical', value: 62.5, details: 'Queue depth: 1.2k' },
]

const statusConfig = {
  healthy: { icon: Check, color: 'text-green-500', bg: 'bg-green-500' },
  warning: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-500' },
  critical: { icon: X, color: 'text-red-500', bg: 'bg-red-500' },
}

export function SystemHealth() {
  return (
    <div className="space-y-4">
      {metrics.map((metric, index) => {
        const { icon: Icon, color, bg } = statusConfig[metric.status]

        return (
          <motion.div
            key={metric.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="space-y-2"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Icon className={`h-4 w-4 ${color}`} />
                <span className="text-sm font-medium">{metric.name}</span>
              </div>
              <span className="text-xs text-muted-foreground">{metric.details}</span>
            </div>

            <div className="relative">
              <Progress value={metric.value} className="h-2" />
              <div
                className={`absolute top-0 left-0 h-full ${bg} rounded-full transition-all`}
                style={{ width: `${metric.value}%` }}
              />
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}

// Progress component (if not in @elf/ui)
function Progress({ value, className }: { value: number; className?: string }) {
  return (
    <div className={`w-full bg-muted rounded-full overflow-hidden ${className}`}>
      <motion.div
        className="h-full bg-primary rounded-full"
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 1, ease: "easeOut" }}
      />
    </div>
  )
}
