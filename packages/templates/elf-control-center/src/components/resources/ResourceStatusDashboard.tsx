'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { StateBadge } from '@/components/ui/state-badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import {
  Search,
  RefreshCw,
  Filter,
  ArrowRight,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react'

interface ResourceState {
  resource_type: string
  resource_id: string
  resource_name: string
  current_state: string
  previous_state?: string
  state_reason?: string
  transitioned_at: string
  transitioned_by: string
  state_metadata?: any
}

interface StateOverview {
  [resourceType: string]: {
    [state: string]: {
      count: number
      last_transition: string
    }
  }
}

export function ResourceStatusDashboard() {
  const [resources, setResources] = useState<ResourceState[]>([])
  const [awaitingAction, setAwaitingAction] = useState<ResourceState[]>([])
  const [overview, setOverview] = useState<StateOverview>({})
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedState, setSelectedState] = useState<string>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchResourceData()
  }, [])

  const fetchResourceData = async () => {
    try {
      setLoading(true)

      // Fetch overview
      const overviewRes = await fetch('/api/resources/overview')
      const overviewData = await overviewRes.json()
      setOverview(overviewData)

      // Fetch resources awaiting action
      const awaitingRes = await fetch('/api/resources/awaiting-action')
      const awaitingData = await awaitingRes.json()
      setAwaitingAction(awaitingData)

      // Fetch all resources
      const resourcesRes = await fetch('/api/resources')
      const resourcesData = await resourcesRes.json()
      setResources(resourcesData)

    } catch (error) {
      console.error('Failed to fetch resource data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredResources = resources.filter(resource => {
    const matchesSearch = resource.resource_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || resource.resource_type === selectedType
    const matchesState = selectedState === 'all' || resource.current_state === selectedState
    return matchesSearch && matchesType && matchesState
  })

  const resourceTypes = ['all', ...new Set(resources.map(r => r.resource_type))]
  const states = ['all', ...new Set(resources.map(r => r.current_state))]

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'workflow': return '🔄'
      case 'mcp_server': return '🔌'
      case 'team': return '👥'
      default: return '📦'
    }
  }

  const renderStateTransition = (resource: ResourceState) => {
    if (!resource.previous_state) return null

    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <StateBadge state={resource.previous_state} size="sm" showIcon={false} />
        <ArrowRight className="h-3 w-3" />
        <StateBadge state={resource.current_state} size="sm" showIcon={false} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Resource Status</h2>
          <p className="text-muted-foreground">Monitor deployment states across all resources</p>
        </div>
        <Button onClick={fetchResourceData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Resources Awaiting Action */}
      {awaitingAction.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
              Resources Awaiting Action
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {awaitingAction.slice(0, 5).map((resource) => (
                <div key={`${resource.resource_type}-${resource.resource_id}`}
                     className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getResourceIcon(resource.resource_type)}</span>
                    <div>
                      <p className="font-medium">{resource.resource_name}</p>
                      <p className="text-sm text-muted-foreground">{resource.state_reason}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StateBadge state={resource.current_state} size="sm" />
                    <Button size="sm" variant="outline">
                      Take Action
                    </Button>
                  </div>
                </div>
              ))}
              {awaitingAction.length > 5 && (
                <p className="text-sm text-center text-muted-foreground">
                  And {awaitingAction.length - 5} more...
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* State Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        {Object.entries(overview).map(([resourceType, states]) => {
          const totalCount = Object.values(states).reduce((sum, state) => sum + state.count, 0)
          const activeCount = states.active?.count || 0
          const failedCount = (states.failed?.count || 0) + (states.error?.count || 0)

          return (
            <Card key={resourceType}>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <span className="text-2xl">{getResourceIcon(resourceType)}</span>
                    {resourceType.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="text-2xl font-bold">{totalCount}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Active</span>
                    <span className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      {activeCount}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Failed</span>
                    <span className="flex items-center gap-2">
                      <XCircle className="h-4 w-4 text-red-500" />
                      {failedCount}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Other</span>
                    <span className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-gray-500" />
                      {totalCount - activeCount - failedCount}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Detailed Resource List */}
      <Card>
        <CardHeader>
          <CardTitle>All Resources</CardTitle>

          {/* Filters */}
          <div className="flex gap-4 mt-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search resources..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-2 border rounded-md"
            >
              {resourceTypes.map(type => (
                <option key={type} value={type}>
                  {type === 'all' ? 'All Types' : type.replace('_', ' ')}
                </option>
              ))}
            </select>

            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="px-3 py-2 border rounded-md"
            >
              {states.map(state => (
                <option key={state} value={state}>
                  {state === 'all' ? 'All States' : state.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {filteredResources.map((resource) => (
              <div key={`${resource.resource_type}-${resource.resource_id}`}
                   className="flex items-center justify-between p-4 hover:bg-accent rounded-lg transition-colors">
                <div className="flex items-center gap-4">
                  <span className="text-2xl">{getResourceIcon(resource.resource_type)}</span>
                  <div>
                    <p className="font-medium">{resource.resource_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {resource.resource_type} • Last updated {new Date(resource.transitioned_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {renderStateTransition(resource)}
                  <StateBadge state={resource.current_state} />
                  <Button size="sm" variant="ghost">
                    View Details
                  </Button>
                </div>
              </div>
            ))}

            {filteredResources.length === 0 && (
              <p className="text-center py-8 text-muted-foreground">
                No resources found matching your filters
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
