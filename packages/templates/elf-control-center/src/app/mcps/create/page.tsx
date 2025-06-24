'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Plus, Trash2, Code, FileJson, Rocket, AlertCircle } from 'lucide-react'
import Link from 'next/link'
import { mcpFactory } from '@/services/mcp-factory'

interface ToolParameter {
  name: string
  type: string
  description: string
  required: boolean
}

interface Tool {
  name: string
  description: string
  parameters: ToolParameter[]
}

export default function CreateMCPPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    name: '',
    displayName: '',
    description: '',
    language: 'typescript',
    useTemplate: false,
    template: '',
    tools: [] as Tool[],
    hasResources: false,
    resources: [] as any[],
    complexity: 'simple',
    dependencies: [] as string[],
    useMock: false,
    environment: {} as Record<string, string>,
  })

  const [currentTool, setCurrentTool] = useState<Tool>({
    name: '',
    description: '',
    parameters: [],
  })

  const [currentParam, setCurrentParam] = useState<ToolParameter>({
    name: '',
    type: 'string',
    description: '',
    required: true,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const templates = [
    { value: 'file-system', label: 'File System Operations' },
    { value: 'database', label: 'Database Operations' },
    { value: 'api-client', label: 'API Client' },
    { value: 'data-processing', label: 'Data Processing' },
    { value: 'integration', label: 'Third-party Integration' },
  ]

  const paramTypes = [
    'string',
    'number',
    'boolean',
    'object',
    'array',
    'enum',
    'any',
  ]

  const validateStep = (stepNumber: number): boolean => {
    const newErrors: Record<string, string> = {}

    switch (stepNumber) {
      case 1:
        if (!formData.name) newErrors.name = 'Name is required'
        if (!/^[a-z0-9-]+$/.test(formData.name)) {
          newErrors.name = 'Name must be lowercase with hyphens only'
        }
        if (!formData.description) newErrors.description = 'Description is required'
        break
      case 2:
        if (formData.tools.length === 0) {
          newErrors.tools = 'At least one tool is required'
        }
        break
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const nextStep = () => {
    if (validateStep(step)) {
      setStep(step + 1)
    }
  }

  const prevStep = () => {
    setStep(step - 1)
  }

  const addParameter = () => {
    if (currentParam.name && currentParam.description) {
      setCurrentTool({
        ...currentTool,
        parameters: [...currentTool.parameters, currentParam],
      })
      setCurrentParam({
        name: '',
        type: 'string',
        description: '',
        required: true,
      })
    }
  }

  const removeParameter = (index: number) => {
    setCurrentTool({
      ...currentTool,
      parameters: currentTool.parameters.filter((_, i) => i !== index),
    })
  }

  const addTool = () => {
    if (currentTool.name && currentTool.description) {
      setFormData({
        ...formData,
        tools: [...formData.tools, currentTool],
      })
      setCurrentTool({
        name: '',
        description: '',
        parameters: [],
      })
    }
  }

  const removeTool = (index: number) => {
    setFormData({
      ...formData,
      tools: formData.tools.filter((_, i) => i !== index),
    })
  }

  const determineComplexity = () => {
    const toolCount = formData.tools.length
    const hasComplexTypes = formData.tools.some(tool =>
      tool.parameters.some(p => ['object', 'array'].includes(p.type))
    )

    if (toolCount > 10 || hasComplexTypes) return 'complex'
    if (toolCount > 5) return 'moderate'
    return 'simple'
  }

  const handleSubmit = async () => {
    if (!validateStep(3)) return

    const complexity = determineComplexity()

    const mcpConfig = {
      ...formData,
      complexity,
      displayName: formData.displayName || formData.name.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    }

    try {
      // Show loading state
      const submitButton = document.querySelector('[data-submit-button]') as HTMLButtonElement
      if (submitButton) {
        submitButton.disabled = true
        submitButton.textContent = 'Creating MCP...'
      }

      // Call the MCP factory service
      const result = await mcpFactory.createMCP(mcpConfig)

      if (result.success) {
        // Generate command for manual execution
        const command = mcpFactory.generateFactoryCommand(mcpConfig)
        console.log('MCP Factory Command:\n', command)

        alert(`Success! ${result.message}\n\nCheck the console for the manual command if needed.`)
        router.push('/mcps')
      } else {
        alert(`Failed to create MCP: ${result.message}`)
      }
    } catch (error) {
      console.error('Error creating MCP:', error)
      alert('An error occurred while creating the MCP. Check the console for details.')
    } finally {
      // Restore button state
      const submitButton = document.querySelector('[data-submit-button]') as HTMLButtonElement
      if (submitButton) {
        submitButton.disabled = false
        submitButton.textContent = 'Create MCP'
      }
    }
  }

  return (
    <PageTransition variant="slide">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/mcps">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold">Create Internal MCP</h1>
              <p className="text-muted-foreground mt-1">
                Step {step} of 3: {step === 1 ? 'Basic Information' : step === 2 ? 'Define Tools' : 'Review & Create'}
              </p>
            </div>
          </div>
        </div>

        {/* Progress indicator */}
        <div className="flex gap-2">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`h-2 flex-1 rounded-full transition-colors ${
                s <= step ? 'bg-primary' : 'bg-muted'
              }`}
            />
          ))}
        </div>

        {/* Step 1: Basic Information */}
        {step === 1 && (
          <Card variant="glass">
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">MCP Name*</label>
                <input
                  type="text"
                  className={`w-full mt-1 px-3 py-2 rounded-md bg-background border ${
                    errors.name ? 'border-red-500' : ''
                  }`}
                  placeholder="e.g., analytics-tools"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
                {errors.name && (
                  <p className="text-sm text-red-500 mt-1">{errors.name}</p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  Lowercase letters, numbers, and hyphens only
                </p>
              </div>

              <div>
                <label className="text-sm font-medium">Display Name</label>
                <input
                  type="text"
                  className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                  placeholder="e.g., Analytics Tools"
                  value={formData.displayName}
                  onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Description*</label>
                <textarea
                  className={`w-full mt-1 px-3 py-2 rounded-md bg-background border ${
                    errors.description ? 'border-red-500' : ''
                  }`}
                  placeholder="Describe what this MCP does..."
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
                {errors.description && (
                  <p className="text-sm text-red-500 mt-1">{errors.description}</p>
                )}
              </div>

              <div>
                <label className="text-sm font-medium">Implementation Language</label>
                <select
                  className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                  value={formData.language}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                >
                  <option value="typescript">TypeScript</option>
                  <option value="python">Python</option>
                </select>
              </div>

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="toggle"
                    checked={formData.useTemplate}
                    onChange={(e) => setFormData({ ...formData, useTemplate: e.target.checked })}
                  />
                  <span className="text-sm">Use a template as starting point</span>
                </label>
              </div>

              {formData.useTemplate && (
                <div>
                  <label className="text-sm font-medium">Select Template</label>
                  <select
                    className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                    value={formData.template}
                    onChange={(e) => setFormData({ ...formData, template: e.target.value })}
                  >
                    <option value="">Choose a template...</option>
                    {templates.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex justify-end gap-4 pt-4">
                <Button variant="default" onClick={nextStep}>
                  Next: Define Tools
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Define Tools */}
        {step === 2 && (
          <div className="space-y-6">
            <Card variant="gradient">
              <CardHeader>
                <CardTitle>Define Tools</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Current Tool Form */}
                  <div className="p-4 rounded-lg bg-background/50 space-y-4">
                    <h3 className="font-semibold">Add New Tool</h3>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <label className="text-sm font-medium">Tool Name</label>
                        <input
                          type="text"
                          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                          placeholder="e.g., analyze_data"
                          value={currentTool.name}
                          onChange={(e) => setCurrentTool({ ...currentTool, name: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Description</label>
                        <input
                          type="text"
                          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                          placeholder="What does this tool do?"
                          value={currentTool.description}
                          onChange={(e) => setCurrentTool({ ...currentTool, description: e.target.value })}
                        />
                      </div>
                    </div>

                    {/* Parameters */}
                    <div>
                      <h4 className="text-sm font-medium mb-2">Parameters</h4>

                      {currentTool.parameters.length > 0 && (
                        <div className="space-y-2 mb-4">
                          {currentTool.parameters.map((param, index) => (
                            <div key={index} className="flex items-center gap-2 p-2 rounded bg-muted/50">
                              <span className="font-mono text-sm">{param.name}</span>
                              <span className="text-xs px-2 py-1 rounded bg-primary/20">
                                {param.type}
                              </span>
                              <span className="text-sm text-muted-foreground flex-1">
                                {param.description}
                              </span>
                              {!param.required && (
                                <span className="text-xs text-yellow-500">optional</span>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => removeParameter(index)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="grid gap-2 md:grid-cols-4 items-end">
                        <div>
                          <label className="text-xs">Name</label>
                          <input
                            type="text"
                            className="w-full px-2 py-1 text-sm rounded bg-background border"
                            placeholder="param_name"
                            value={currentParam.name}
                            onChange={(e) => setCurrentParam({ ...currentParam, name: e.target.value })}
                          />
                        </div>
                        <div>
                          <label className="text-xs">Type</label>
                          <select
                            className="w-full px-2 py-1 text-sm rounded bg-background border"
                            value={currentParam.type}
                            onChange={(e) => setCurrentParam({ ...currentParam, type: e.target.value })}
                          >
                            {paramTypes.map((type) => (
                              <option key={type} value={type}>
                                {type}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="text-xs">Description</label>
                          <input
                            type="text"
                            className="w-full px-2 py-1 text-sm rounded bg-background border"
                            placeholder="Parameter description"
                            value={currentParam.description}
                            onChange={(e) => setCurrentParam({ ...currentParam, description: e.target.value })}
                          />
                        </div>
                        <div className="flex gap-2">
                          <label className="flex items-center gap-1">
                            <input
                              type="checkbox"
                              checked={currentParam.required}
                              onChange={(e) => setCurrentParam({ ...currentParam, required: e.target.checked })}
                            />
                            <span className="text-xs">Required</span>
                          </label>
                          <Button size="sm" variant="outline" onClick={addParameter}>
                            Add
                          </Button>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button
                        variant="default"
                        onClick={addTool}
                        disabled={!currentTool.name || !currentTool.description}
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add Tool
                      </Button>
                    </div>
                  </div>

                  {/* Tools List */}
                  {formData.tools.length > 0 && (
                    <div className="space-y-3">
                      <h3 className="font-semibold">Defined Tools ({formData.tools.length})</h3>
                      {errors.tools && (
                        <p className="text-sm text-red-500 flex items-center gap-2">
                          <AlertCircle className="h-4 w-4" />
                          {errors.tools}
                        </p>
                      )}
                      {formData.tools.map((tool, index) => (
                        <div key={index} className="p-3 rounded-lg bg-muted/50">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="font-medium">{tool.name}</h4>
                              <p className="text-sm text-muted-foreground">{tool.description}</p>
                              <div className="mt-2 flex gap-2">
                                {tool.parameters.map((param, pIndex) => (
                                  <span key={pIndex} className="text-xs px-2 py-1 rounded bg-background">
                                    {param.name}: {param.type}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removeTool(index)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex justify-between gap-4 pt-6">
                  <Button variant="outline" onClick={prevStep}>
                    Previous
                  </Button>
                  <Button variant="default" onClick={nextStep}>
                    Next: Review
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Step 3: Review & Create */}
        {step === 3 && (
          <div className="space-y-6">
            <Card variant="neu">
              <CardHeader>
                <CardTitle>Review Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-3">Basic Information</h3>
                  <dl className="grid gap-2">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Name:</dt>
                      <dd className="font-mono">{formData.name}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Display Name:</dt>
                      <dd>{formData.displayName || formData.name.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Language:</dt>
                      <dd>{formData.language}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Complexity:</dt>
                      <dd className="capitalize">{determineComplexity()}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Description</h3>
                  <p className="text-sm">{formData.description}</p>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Tools ({formData.tools.length})</h3>
                  <div className="space-y-2">
                    {formData.tools.map((tool, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <Code className="h-4 w-4 text-muted-foreground" />
                        <span className="font-mono text-sm">{tool.name}</span>
                        <span className="text-sm text-muted-foreground">
                          ({tool.parameters.length} parameters)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-muted/50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <FileJson className="h-4 w-4" />
                    What will be created:
                  </h3>
                  <ul className="space-y-1 text-sm">
                    <li>• MCP server implementation in {formData.language}</li>
                    <li>• Dockerfile for containerization</li>
                    <li>• Kubernetes deployment manifests</li>
                    <li>• README with documentation</li>
                    <li>• Test suite for all tools</li>
                    <li>• AgentGateway registration</li>
                  </ul>
                </div>

                <div className="flex justify-between gap-4 pt-4">
                  <Button variant="outline" onClick={prevStep}>
                    Previous
                  </Button>
                  <Button variant="gradient" onClick={handleSubmit} className="gap-2" data-submit-button>
                    <Rocket className="h-4 w-4" />
                    Create MCP
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </PageTransition>
  )
}
