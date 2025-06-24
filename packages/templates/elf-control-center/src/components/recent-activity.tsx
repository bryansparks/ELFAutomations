'use client'

import { motion } from 'framer-motion'
import { Users, Workflow, Shield, DollarSign, Brain } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface Activity {
  id: string
  type: 'team' | 'workflow' | 'security' | 'cost' | 'communication'
  title: string
  description: string
  timestamp: Date
  user?: string
}

const activities: Activity[] = [
  {
    id: '1',
    type: 'team',
    title: 'New team created',
    description: 'Marketing Analytics team was created with 3 members',
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
    user: 'Admin'
  },
  {
    id: '2',
    type: 'workflow',
    title: 'Workflow executed',
    description: 'Daily cost report completed successfully',
    timestamp: new Date(Date.now() - 1000 * 60 * 15),
  },
  {
    id: '3',
    type: 'security',
    title: 'Credentials rotated',
    description: 'API keys for OpenAI were automatically rotated',
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
  },
  {
    id: '4',
    type: 'cost',
    title: 'Cost alert',
    description: 'Daily spending exceeded budget threshold ($150)',
    timestamp: new Date(Date.now() - 1000 * 60 * 45),
  },
  {
    id: '5',
    type: 'communication',
    title: 'A2A message',
    description: 'Executive team requested report from Analytics team',
    timestamp: new Date(Date.now() - 1000 * 60 * 60),
  },
]

const typeConfig = {
  team: { icon: Users, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  workflow: { icon: Workflow, color: 'text-green-500', bg: 'bg-green-500/10' },
  security: { icon: Shield, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  cost: { icon: DollarSign, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  communication: { icon: Brain, color: 'text-pink-500', bg: 'bg-pink-500/10' },
}

export function RecentActivity() {
  return (
    <div className="space-y-4">
      {activities.map((activity, index) => {
        const { icon: Icon, color, bg } = typeConfig[activity.type]

        return (
          <motion.div
            key={activity.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex gap-3 p-3 rounded-lg hover:bg-accent/50 transition-colors"
          >
            <div className={`p-2 rounded-lg ${bg} flex-shrink-0`}>
              <Icon className={`h-4 w-4 ${color}`} />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <p className="font-medium text-sm truncate">{activity.title}</p>
                <span className="text-xs text-muted-foreground flex-shrink-0">
                  {formatDistanceToNow(activity.timestamp, { addSuffix: true })}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{activity.description}</p>
              {activity.user && (
                <p className="text-xs text-muted-foreground mt-1">by {activity.user}</p>
              )}
            </div>
          </motion.div>
        )
      })}

      <motion.button
        className="w-full text-center text-sm text-muted-foreground hover:text-foreground transition-colors py-2"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        View all activity →
      </motion.button>
    </div>
  )
}
