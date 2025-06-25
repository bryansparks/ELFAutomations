'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Plus, Users, Bot, Network } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export function TeamManager() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newTeam, setNewTeam] = useState({
    name: '',
    description: '',
    framework: 'CrewAI',
    llm_provider: 'OpenAI',
    llm_model: 'gpt-4',
    placement: '',
  })

  const { data: teams, isLoading } = useQuery({
    queryKey: ['teams'],
    queryFn: api.getTeams,
  })

  const createTeamMutation = useMutation({
    mutationFn: api.createTeam,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
      setCreateDialogOpen(false)
      setNewTeam({
        name: '',
        description: '',
        framework: 'CrewAI',
        llm_provider: 'OpenAI',
        llm_model: 'gpt-4',
        placement: '',
      })
      toast({
        title: "Team created",
        description: "The new team has been created successfully.",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to create team",
        variant: "destructive",
      })
    },
  })

  const handleCreateTeam = () => {
    createTeamMutation.mutate(newTeam)
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading teams...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>AI Teams</CardTitle>
            <CardDescription>
              Manage your autonomous AI teams
            </CardDescription>
          </div>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Team
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[525px]">
              <DialogHeader>
                <DialogTitle>Create New Team</DialogTitle>
                <DialogDescription>
                  Define a new AI team with natural language description
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Team Name</Label>
                  <Input
                    id="name"
                    value={newTeam.name}
                    onChange={(e) => setNewTeam({ ...newTeam, name: e.target.value })}
                    placeholder="e.g., marketing-analytics-team"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={newTeam.description}
                    onChange={(e) => setNewTeam({ ...newTeam, description: e.target.value })}
                    placeholder="What should this team do?"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="framework">Framework</Label>
                  <Select
                    value={newTeam.framework}
                    onValueChange={(value) => setNewTeam({ ...newTeam, framework: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CrewAI">CrewAI</SelectItem>
                      <SelectItem value="LangGraph">LangGraph</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="placement">Organizational Placement</Label>
                  <Input
                    id="placement"
                    value={newTeam.placement}
                    onChange={(e) => setNewTeam({ ...newTeam, placement: e.target.value })}
                    placeholder="e.g., marketing.analytics"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateTeam} disabled={createTeamMutation.isPending}>
                  {createTeamMutation.isPending ? 'Creating...' : 'Create Team'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {teams?.map((team: any) => (
              <Card key={team.team_name}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Users className="h-5 w-5 text-muted-foreground" />
                      <CardTitle className="text-base">{team.team_name}</CardTitle>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`status-indicator ${team.status || 'active'}`}>
                        {team.status || 'active'}
                      </span>
                      <Badge variant="outline">{team.department}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Members</p>
                      <p className="font-medium">{team.member_count || 0}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Framework</p>
                      <p className="font-medium">{team.framework || 'CrewAI'}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Manager</p>
                      <p className="font-medium">{team.manager_count || 0}</p>
                    </div>
                  </div>
                  {team.members && team.members.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-sm text-muted-foreground mb-2">Team Members:</p>
                      <div className="flex flex-wrap gap-1">
                        {team.members.map((member: string, idx: number) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            <Bot className="h-3 w-3 mr-1" />
                            {member}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Team Network
          </CardTitle>
          <CardDescription>
            Visualize team relationships and communication patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] bg-muted/50 rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground">Team network visualization coming soon</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function Badge({ children, variant = "default", className = "" }: any) {
  const variants = {
    default: "bg-primary text-primary-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    outline: "border border-input bg-background",
  }

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors ${variants[variant as keyof typeof variants]} ${className}`}>
      {children}
    </span>
  )
}
