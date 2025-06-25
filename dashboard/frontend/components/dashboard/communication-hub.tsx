'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { MessageSquare, ArrowRight, Clock, AlertCircle, CheckCircle } from 'lucide-react'
import { format } from 'date-fns'

export function CommunicationHub() {
  const [selectedTeam, setSelectedTeam] = useState<string>('')

  const { data: teams } = useQuery({
    queryKey: ['teams'],
    queryFn: api.getTeams,
  })

  const { data: logs, isLoading } = useQuery({
    queryKey: ['communications', selectedTeam],
    queryFn: () => api.getCommunications(selectedTeam),
    enabled: !!selectedTeam,
  })

  const levelColors = {
    INFO: 'text-blue-500',
    WARNING: 'text-yellow-500',
    ERROR: 'text-red-500',
    DEBUG: 'text-gray-500',
  }

  const levelIcons = {
    INFO: CheckCircle,
    WARNING: AlertCircle,
    ERROR: AlertCircle,
    DEBUG: MessageSquare,
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>A2A Communication Logs</CardTitle>
          <CardDescription>
            Monitor inter-team communication and messages
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <Select value={selectedTeam} onValueChange={setSelectedTeam}>
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder="Select a team to view logs" />
              </SelectTrigger>
              <SelectContent>
                {teams?.map((team: any) => (
                  <SelectItem key={team.team_name} value={team.team_name}>
                    {team.team_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {!selectedTeam && (
            <div className="text-center py-8 text-muted-foreground">
              Select a team to view communication logs
            </div>
          )}

          {selectedTeam && isLoading && (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-muted animate-pulse rounded" />
              ))}
            </div>
          )}

          {selectedTeam && logs && logs.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No communication logs found for this team
            </div>
          )}

          {selectedTeam && logs && logs.length > 0 && (
            <div className="space-y-2">
              {logs.map((log: any, index: number) => {
                const Icon = levelIcons[log.level as keyof typeof levelIcons] || MessageSquare
                const colorClass = levelColors[log.level as keyof typeof levelColors] || 'text-gray-500'

                return (
                  <Card key={index} className="p-3">
                    <div className="flex items-start space-x-3">
                      <Icon className={`h-4 w-4 mt-0.5 ${colorClass}`} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{log.team}</span>
                          <span className="text-xs text-muted-foreground">
                            {log.timestamp}
                          </span>
                        </div>
                        <p className="text-sm">{log.message}</p>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Communication Flow</CardTitle>
          <CardDescription>
            Visualize message flow between teams
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] bg-muted/50 rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground">
              Communication flow visualization coming soon
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Communication Metrics</CardTitle>
          <CardDescription>
            Team communication statistics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">0</p>
              <p className="text-sm text-muted-foreground">Messages Today</p>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">0</p>
              <p className="text-sm text-muted-foreground">Active Conversations</p>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">0ms</p>
              <p className="text-sm text-muted-foreground">Avg Response Time</p>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">0%</p>
              <p className="text-sm text-muted-foreground">Success Rate</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
