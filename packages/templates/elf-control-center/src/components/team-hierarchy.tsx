'use client'

import { motion } from 'framer-motion'
import { ChevronRight, Users, Brain, Shield, Zap } from 'lucide-react'
import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { api, TeamInfo } from '@/services/api'
import { Loading } from '@/components/ui/loading'

interface Team {
  id: string
  name: string
  type: 'executive' | 'operational' | 'technical'
  members: number
  children?: Team[]
  status?: string
  framework?: string
  llm_provider?: string
}

function transformTeamsToHierarchy(teams: TeamInfo[]): Team {
  // Create a map for quick lookup
  const teamMap = new Map<string, Team>()

  // First pass: create all teams
  teams.forEach(team => {
    const teamType = team.department === 'executive' ? 'executive' :
                    team.department === 'engineering' ? 'technical' : 'operational'

    teamMap.set(team.name, {
      id: team.id,
      name: team.display_name,
      type: teamType,
      members: team.member_count,
      status: team.status,
      framework: team.framework,
      llm_provider: team.llm_provider,
      children: []
    })
  })

  // Second pass: build hierarchy
  const rootTeams: Team[] = []
  teams.forEach(team => {
    const currentTeam = teamMap.get(team.name)!

    if (team.reports_to && teamMap.has(team.reports_to)) {
      const parentTeam = teamMap.get(team.reports_to)!
      if (!parentTeam.children) parentTeam.children = []
      parentTeam.children.push(currentTeam)
    } else if (!team.reports_to || team.department === 'executive') {
      rootTeams.push(currentTeam)
    }
  })

  // Find executive team or create a virtual root
  const executiveTeam = rootTeams.find(t => t.name.includes('Executive')) || {
    id: 'root',
    name: 'ElfAutomations Teams',
    type: 'executive' as const,
    members: teams.reduce((sum, t) => sum + t.member_count, 0),
    children: rootTeams
  }

  return executiveTeam
}

const typeIcons = {
  executive: Brain,
  operational: Users,
  technical: Zap
}

const typeColors = {
  executive: 'text-purple-500',
  operational: 'text-blue-500',
  technical: 'text-green-500'
}

function TeamNode({ team, level = 0 }: { team: Team; level?: number }) {
  const [expanded, setExpanded] = useState(level < 2)
  const Icon = typeIcons[team.type]

  return (
    <div className="select-none">
      <motion.div
        className={cn(
          "flex items-center gap-2 p-2 rounded-lg hover:bg-accent cursor-pointer transition-colors",
          level === 0 && "font-semibold"
        )}
        onClick={() => setExpanded(!expanded)}
        whileHover={{ x: 2 }}
        style={{ paddingLeft: `${level * 24}px` }}
      >
        {team.children && (
          <motion.div
            animate={{ rotate: expanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronRight className="h-4 w-4" />
          </motion.div>
        )}

        <Icon className={cn("h-4 w-4", typeColors[team.type])} />

        <span className="flex-1">{team.name}</span>

        <span className="text-sm text-muted-foreground">
          {team.members} members
        </span>
      </motion.div>

      {expanded && team.children && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.3 }}
        >
          {team.children.map((child) => (
            <TeamNode key={child.id} team={child} level={level + 1} />
          ))}
        </motion.div>
      )}
    </div>
  )
}

export function TeamHierarchy() {
  const [teams, setTeams] = useState<Team | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchTeams()
  }, [])

  const fetchTeams = async () => {
    try {
      setLoading(true)
      const teamData = await api.getTeams()
      const hierarchy = transformTeamsToHierarchy(teamData)
      setTeams(hierarchy)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch teams:', err)
      setError('Failed to load team hierarchy')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loading variant="dots" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <p>{error}</p>
        <button
          onClick={fetchTeams}
          className="mt-2 text-sm text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  if (!teams) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No teams found
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <TeamNode team={teams} />
    </div>
  )
}
