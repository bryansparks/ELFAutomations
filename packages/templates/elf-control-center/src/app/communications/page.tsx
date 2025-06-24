'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Brain, MessageSquare, Users, ArrowRight, Clock } from 'lucide-react'

export default function CommunicationsPage() {
  // Mock communication data
  const communications = [
    {
      id: '1',
      from: 'Chief Technology Officer',
      to: 'engineering-team',
      type: 'task_delegation',
      message: 'Implement new authentication system',
      timestamp: new Date(Date.now() - 3600000),
      status: 'in_progress'
    },
    {
      id: '2',
      from: 'marketing-team',
      to: 'Chief Marketing Officer',
      type: 'status_report',
      message: 'Campaign performance report ready',
      timestamp: new Date(Date.now() - 7200000),
      status: 'completed'
    },
    {
      id: '3',
      from: 'qa-team',
      to: 'engineering-team',
      type: 'collaboration',
      message: 'Found 3 critical bugs in latest release',
      timestamp: new Date(Date.now() - 10800000),
      status: 'pending'
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500/20 text-green-500'
      case 'in_progress': return 'bg-blue-500/20 text-blue-500'
      case 'pending': return 'bg-yellow-500/20 text-yellow-500'
      default: return 'bg-gray-500/20 text-gray-500'
    }
  }

  return (
    <PageTransition variant="fade">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Team Communications</h1>
          <p className="text-muted-foreground mt-1">
            Monitor inter-team and intra-team communications
          </p>
        </div>

        {/* Communication Patterns */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                A2A Protocol Messages
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {communications.map((comm) => (
                  <div key={comm.id} className="border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                        <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(comm.status)}`}>
                          {comm.status.replace('_', ' ')}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {comm.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm mb-2">
                      <span className="font-medium">{comm.from}</span>
                      <ArrowRight className="h-3 w-3" />
                      <span className="font-medium">{comm.to}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">{comm.message}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card variant="gradient">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Communication Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Inter-team Messages</span>
                    <span className="font-mono text-sm">247</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-primary rounded-full h-2" style={{ width: '65%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Intra-team Messages</span>
                    <span className="font-mono text-sm">1,892</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-blue-500 rounded-full h-2" style={{ width: '85%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Task Delegations</span>
                    <span className="font-mono text-sm">45</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-green-500 rounded-full h-2" style={{ width: '35%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Status Reports</span>
                    <span className="font-mono text-sm">78</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-yellow-500 rounded-full h-2" style={{ width: '45%' }} />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Communication Logs */}
        <Card variant="neu">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Communication Logs</CardTitle>
              <Button variant="outline" size="sm">
                Export Logs
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <p>Communication patterns in ElfAutomations:</p>
              <ul>
                <li><strong>Intra-team</strong>: Natural language communication within teams using CrewAI/LangGraph</li>
                <li><strong>Inter-team</strong>: Structured A2A protocol messages between team managers only</li>
                <li><strong>Audit Trail</strong>: All inter-team communications are logged for accountability</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
