'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Workflow, CheckCircle, XCircle, Clock, Plus } from 'lucide-react'
import { format } from 'date-fns'

export function WorkflowManager() {
  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.getWorkflows,
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading workflows...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-muted animate-pulse rounded" />
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
            <CardTitle>N8N Workflows</CardTitle>
            <CardDescription>
              Manage and monitor automated workflows
            </CardDescription>
          </div>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Workflow
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {workflows?.map((workflow: any) => (
              <Card key={workflow.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Workflow className="h-5 w-5 text-muted-foreground" />
                      <CardTitle className="text-base">{workflow.name}</CardTitle>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={workflow.is_active ? 'default' : 'secondary'}>
                        {workflow.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      <Badge variant="outline">{workflow.category}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Owner Team</p>
                      <p className="font-medium">{workflow.owner_team}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Total Runs</p>
                      <p className="font-medium">{workflow.total_executions || 0}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Success Rate</p>
                      <p className="font-medium">
                        {workflow.total_executions > 0
                          ? `${Math.round((workflow.successful_executions / workflow.total_executions) * 100)}%`
                          : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Last Run</p>
                      <p className="font-medium">
                        {workflow.last_execution
                          ? format(new Date(workflow.last_execution), 'MMM d, h:mm a')
                          : 'Never'}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span className="text-sm">{workflow.successful_executions || 0} Success</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <XCircle className="h-4 w-4 text-red-500" />
                      <span className="text-sm">{workflow.failed_executions || 0} Failed</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm">{workflow.running_executions || 0} Running</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Workflow Analytics</CardTitle>
          <CardDescription>
            Performance metrics and execution trends
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] bg-muted/50 rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground">Workflow analytics visualization coming soon</p>
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
