'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TeamHierarchy } from '@/components/team-hierarchy'
import { useState, useEffect } from 'react'
import { api, TeamInfo } from '@/services/api'
import { Loading } from '@/components/ui/loading'
import { Plus, Users, Brain, Zap, Play, Pause, Trash2 } from 'lucide-react'

export default function TeamsPage() {
  const [teams, setTeams] = useState<TeamInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTeam, setSelectedTeam] = useState<TeamInfo | null>(null)

  useEffect(() => {
    fetchTeams()
  }, [])

  const fetchTeams = async () => {
    try {
      setLoading(true)
      const data = await api.getTeams()
      setTeams(data)
    } catch (error) {
      console.error('Failed to fetch teams:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTeamIcon = (department: string) => {
    switch (department) {
      case 'executive': return Brain
      case 'engineering': return Zap
      default: return Users
    }
  }

  return (
    <PageTransition variant="slide">
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Teams Management</h1>
            <p className="text-muted-foreground mt-1">
              Manage your autonomous AI teams and their configurations
            </p>
          </div>
          <Button variant="gradient" className="gap-2">
            <Plus className="h-4 w-4" />
            Create Team
          </Button>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Team Hierarchy */}
          <Card variant="glass" className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Team Hierarchy</CardTitle>
            </CardHeader>
            <CardContent>
              <TeamHierarchy />
            </CardContent>
          </Card>

          {/* Team List */}
          <Card variant="gradient" className="lg:col-span-2">
            <CardHeader>
              <CardTitle>All Teams</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <Loading variant="dots" />
                </div>
              ) : (
                <div className="space-y-4">
                  {teams.map((team) => {
                    const Icon = getTeamIcon(team.department)
                    return (
                      <div
                        key={team.id}
                        className="flex items-center justify-between p-4 rounded-lg bg-background/50 hover:bg-accent transition-colors cursor-pointer"
                        onClick={() => setSelectedTeam(team)}
                      >
                        <div className="flex items-center gap-4">
                          <div className="p-2 rounded-lg bg-primary/10">
                            <Icon className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <h3 className="font-semibold">{team.display_name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {team.member_count} members • {team.framework} • {team.llm_provider}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "px-2 py-1 text-xs rounded-full",
                            team.status === 'active'
                              ? "bg-green-500/20 text-green-500"
                              : "bg-gray-500/20 text-gray-500"
                          )}>
                            {team.status}
                          </span>
                          <div className="flex gap-1">
                            <Button size="sm" variant="ghost">
                              {team.status === 'active' ? (
                                <Pause className="h-4 w-4" />
                              ) : (
                                <Play className="h-4 w-4" />
                              )}
                            </Button>
                            <Button size="sm" variant="ghost">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Team Details Modal */}
        {selectedTeam && (
          <Card variant="neu">
            <CardHeader>
              <CardTitle>{selectedTeam.display_name} Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-sm text-muted-foreground">Department</p>
                  <p className="font-medium">{selectedTeam.department}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Framework</p>
                  <p className="font-medium">{selectedTeam.framework}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">LLM Provider</p>
                  <p className="font-medium">{selectedTeam.llm_provider} ({selectedTeam.llm_model})</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Reports To</p>
                  <p className="font-medium">{selectedTeam.reports_to || 'None'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </PageTransition>
  )
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}
