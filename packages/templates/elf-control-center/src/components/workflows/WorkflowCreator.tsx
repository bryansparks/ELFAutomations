'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Plus, Sparkles, Loader2, AlertCircle } from 'lucide-react'
import { api } from '@/services/api'
import { WorkflowVisualizer } from './WorkflowVisualizer'
import { WorkflowChat } from './WorkflowChat'

interface WorkflowCreatorProps {
  onWorkflowCreated?: (workflow: any) => void
  teams?: Array<{ id: string; name: string; display_name: string }>
}

export function WorkflowCreator({ onWorkflowCreated, teams = [] }: WorkflowCreatorProps) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('describe')

  // Form state
  const [description, setDescription] = useState('')
  const [workflowName, setWorkflowName] = useState('')
  const [selectedTeam, setSelectedTeam] = useState('')
  const [category, setCategory] = useState('automation')

  // Generated workflow state
  const [generatedWorkflow, setGeneratedWorkflow] = useState<any>(null)
  const [workflowMetadata, setWorkflowMetadata] = useState<any>(null)

  const handleGenerateWorkflow = async () => {
    if (!description.trim()) {
      setError('Please provide a workflow description')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await api.generateWorkflow({
        description,
        name: workflowName || `Generated Workflow ${new Date().toISOString()}`,
        team: selectedTeam || 'default',
        category
      })

      setGeneratedWorkflow(response.workflow)
      setWorkflowMetadata(response.metadata)
      setActiveTab('preview')
    } catch (err: any) {
      setError(err.message || 'Failed to generate workflow')
    } finally {
      setLoading(false)
    }
  }

  const handleDeployWorkflow = async () => {
    if (!generatedWorkflow) return

    setLoading(true)
    setError(null)

    try {
      const response = await api.deployWorkflow({
        workflow: generatedWorkflow,
        metadata: workflowMetadata
      })

      if (onWorkflowCreated) {
        onWorkflowCreated(response)
      }

      // Reset form
      setDescription('')
      setWorkflowName('')
      setGeneratedWorkflow(null)
      setWorkflowMetadata(null)
      setActiveTab('describe')
      setOpen(false)
    } catch (err: any) {
      setError(err.message || 'Failed to deploy workflow')
    } finally {
      setLoading(false)
    }
  }

  const suggestedDescriptions = [
    "When a customer submits a support ticket, categorize it by urgency and route to the appropriate team",
    "Every Monday at 9am, fetch sales data from the database and email a report to the sales team",
    "Monitor inventory levels and send alerts when items fall below minimum threshold",
    "Process incoming invoices, extract data, and update accounting system"
  ]

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="gradient" className="gap-2">
          <Plus className="h-4 w-4" />
          Create Workflow
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Create N8N Workflow with AI</DialogTitle>
          <DialogDescription>
            Describe your workflow in natural language and let AI generate it for you
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="describe">Describe</TabsTrigger>
            <TabsTrigger value="preview" disabled={!generatedWorkflow}>Preview</TabsTrigger>
            <TabsTrigger value="chat">AI Assistant</TabsTrigger>
          </TabsList>

          <TabsContent value="describe" className="space-y-4 max-h-[60vh] overflow-y-auto">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="description">Workflow Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe what you want your workflow to do..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="min-h-[120px]"
                />
                <p className="text-sm text-muted-foreground">
                  Be specific about triggers, actions, conditions, and outputs
                </p>
              </div>

              {/* Suggested examples */}
              <div className="space-y-2">
                <Label>Examples to get you started</Label>
                <div className="grid grid-cols-1 gap-2">
                  {suggestedDescriptions.map((example, idx) => (
                    <Card
                      key={idx}
                      className="cursor-pointer hover:bg-accent transition-colors"
                      onClick={() => setDescription(example)}
                    >
                      <CardContent className="p-3">
                        <p className="text-sm">{example}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Workflow Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Customer Support Router"
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="team">Owner Team</Label>
                  <Select value={selectedTeam} onValueChange={setSelectedTeam}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a team" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default Team</SelectItem>
                      {teams.map((team) => (
                        <SelectItem key={team.id} value={team.name}>
                          {team.display_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Select value={category} onValueChange={setCategory}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="automation">Automation</SelectItem>
                    <SelectItem value="data-pipeline">Data Pipeline</SelectItem>
                    <SelectItem value="integration">Integration</SelectItem>
                    <SelectItem value="notification">Notification</SelectItem>
                    <SelectItem value="approval">Approval</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button
                onClick={handleGenerateWorkflow}
                disabled={loading || !description.trim()}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Workflow
                  </>
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="preview" className="space-y-4">
            {generatedWorkflow && (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>Generated Workflow</CardTitle>
                    <CardDescription>
                      Review the AI-generated workflow before deployment
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <WorkflowVisualizer workflow={generatedWorkflow} />
                  </CardContent>
                </Card>

                {workflowMetadata && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Workflow Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Pattern</p>
                          <p className="font-medium">{workflowMetadata.pattern || 'Custom'}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Trigger Type</p>
                          <p className="font-medium">{workflowMetadata.trigger_type || 'Unknown'}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Services Used</p>
                          <p className="font-medium">
                            {workflowMetadata.services ? Object.values(workflowMetadata.services).filter(Boolean).join(', ') : 'None'}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Nodes</p>
                          <p className="font-medium">{generatedWorkflow.nodes?.length || 0} nodes</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setActiveTab('describe')}
                    className="flex-1"
                  >
                    Back to Edit
                  </Button>
                  <Button
                    onClick={handleDeployWorkflow}
                    disabled={loading}
                    className="flex-1"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Deploying...
                      </>
                    ) : (
                      'Deploy to N8N'
                    )}
                  </Button>
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="chat" className="space-y-4">
            <WorkflowChat
              onDescriptionUpdate={(desc) => {
                setDescription(desc)
                setActiveTab('describe')
              }}
              currentDescription={description}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
