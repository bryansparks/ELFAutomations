'use client'

import { Card } from '@/components/ui/card'
import { Users, ChevronRight } from 'lucide-react'

interface TeamHierarchyProps {
  teams: any[] | undefined
}

export function TeamHierarchy({ teams }: TeamHierarchyProps) {
  if (!teams || teams.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No team hierarchy data available
      </div>
    )
  }

  // Group teams by department
  const teamsByDepartment = teams.reduce((acc: any, team: any) => {
    const dept = team.department || 'other'
    if (!acc[dept]) acc[dept] = []
    acc[dept].push(team)
    return acc
  }, {})

  return (
    <div className="space-y-4">
      {Object.entries(teamsByDepartment).map(([department, deptTeams]: [string, any]) => (
        <div key={department}>
          <h3 className="text-sm font-semibold text-muted-foreground uppercase mb-2">
            {department}
          </h3>
          <div className="space-y-2">
            {deptTeams.map((team: any) => (
              <Card key={team.team_name} className="p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">{team.team_name}</span>
                  </div>
                  {team.parent_entity_name && (
                    <div className="flex items-center text-xs text-muted-foreground">
                      <span>Reports to {team.parent_entity_name}</span>
                      <ChevronRight className="h-3 w-3 ml-1" />
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
