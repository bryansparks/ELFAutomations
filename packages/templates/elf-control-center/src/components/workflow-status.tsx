'use client'

import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Clock, Play } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface Workflow {
  id: string
  name: string
  status: 'running' | 'success' | 'failed' | 'pending'
  executionTime: string
  lastRun: string
}

const workflows: Workflow[] = [
  { id: '1', name: 'Daily Cost Report', status: 'success', executionTime: '2m 15s', lastRun: '2 hours ago' },
  { id: '2', name: 'Team Sync Pipeline', status: 'running', executionTime: '5m 32s', lastRun: 'Running now' },
  { id: '3', name: 'Data Backup', status: 'success', executionTime: '8m 12s', lastRun: '6 hours ago' },
  { id: '4', name: 'Security Scan', status: 'failed', executionTime: '1m 45s', lastRun: '1 hour ago' },
  { id: '5', name: 'Performance Monitor', status: 'pending', executionTime: '-', lastRun: 'Scheduled' },
]

const statusIcons = {
  running: { icon: Play, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  success: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-500/10' },
  failed: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
  pending: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
}

export function WorkflowStatus() {
  return (
    <div className="space-y-3">
      {workflows.map((workflow, index) => {
        const { icon: Icon, color, bg } = statusIcons[workflow.status]

        return (
          <motion.div
            key={workflow.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${bg}`}>
                <Icon className={`h-4 w-4 ${color}`} />
              </div>
              <div>
                <p className="font-medium text-sm">{workflow.name}</p>
                <p className="text-xs text-muted-foreground">{workflow.lastRun}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">{workflow.executionTime}</span>
              {workflow.status === 'failed' && (
                <Button size="sm" variant="outline">
                  Retry
                </Button>
              )}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
