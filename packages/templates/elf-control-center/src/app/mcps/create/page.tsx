'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Plus, Trash2, Code, FileJson, Rocket, AlertCircle, Check, X, Globe, Database, MessageSquare, Package, Palette, Settings } from 'lucide-react'
import Link from 'next/link'
import { mcpFactory } from '@/services/mcp-factory'

// Import types from the service
import type { Tool, ToolParameter, Resource, Prompt, PromptArgument, ApiConfig } from '@/services/mcp-factory'

export default function CreateMCPPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    // Step 1: Template Selection
    template: '',

    // Step 2: Basic Information
    serverType: 'internal',
    transport: 'http',
    name: '',
    displayName: '',
    description: '',
    language: 'typescript',
    apiConfig: null as ApiConfig | null,

    // Step 3: Tools/Resources/Prompts
    tools: [] as Tool[],
    resources: [] as Resource[],
    prompts: [] as Prompt[],

    // Additional
    complexity: 'simple',
    dependencies: [] as string[],
    useMock: false,
    environment: {} as Record<string, string>,
  })

  // Template suggestions acceptance state
  const [templateSuggestions, setTemplateSuggestions] = useState<{
    tools: { suggestion: Tool; accepted: boolean }[]
    resources: { suggestion: Resource; accepted: boolean }[]
    prompts: { suggestion: Prompt; accepted: boolean }[]
  }>({
    tools: [],
    resources: [],
    prompts: [],
  })

  const [currentTool, setCurrentTool] = useState<Tool>({
    name: '',
    description: '',
    parameters: [],
  })

  const [currentResource, setCurrentResource] = useState<Resource>({
    uri: '',
    name: '',
    description: '',
    mimeType: 'application/json',
  })

  const [currentPrompt, setCurrentPrompt] = useState<Prompt>({
    name: '',
    description: '',
    arguments: [],
  })

  const [currentParam, setCurrentParam] = useState<ToolParameter>({
    name: '',
    type: 'string',
    description: '',
    required: true,
  })

  const [currentPromptArg, setCurrentPromptArg] = useState<PromptArgument>({
    name: '',
    description: '',
    required: true,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const templates = mcpFactory.getTemplates()

  const paramTypes = [
    'string',
    'number',
    'boolean',
    'object',
    'array',
    'enum',
    'any',
  ]

  const mimeTypes = [
    'application/json',
    'text/plain',
    'text/html',
    'text/markdown',
    'application/xml',
    'application/pdf',
    'image/png',
    'image/jpeg',
  ]

  // Load template suggestions when template is selected
  const loadTemplateSuggestions = (templateValue: string) => {
    const template = templates.find(t => t.value === templateValue)
    if (!template) return

    const toolSuggestions: Tool[] = []
    const resourceSuggestions: Resource[] = []
    const promptSuggestions: Prompt[] = []

    // Create suggestions based on template type
    if (template.value === 'tool-focused') {
      toolSuggestions.push(
        {
          name: 'process_data',
          description: 'Process and transform data',
          parameters: [
            { name: 'input_data', type: 'object', description: 'Data to process', required: true },
            { name: 'operation', type: 'string', description: 'Processing operation', required: true },
          ],
        },
        {
          name: 'validate_data',
          description: 'Validate data against schema',
          parameters: [
            { name: 'data', type: 'object', description: 'Data to validate', required: true },
            { name: 'schema', type: 'object', description: 'Validation schema', required: true },
          ],
        }
      )
    } else if (template.value === 'resource-focused') {
      resourceSuggestions.push(
        { uri: 'documents://list', name: 'documents', description: 'Access to document collection', mimeType: 'application/json' },
        { uri: 'search://results', name: 'search-results', description: 'Search results from knowledge base', mimeType: 'application/json' }
      )
      toolSuggestions.push({
        name: 'search_knowledge',
        description: 'Search the knowledge base',
        parameters: [
          { name: 'query', type: 'string', description: 'Search query', required: true },
          { name: 'limit', type: 'number', description: 'Maximum results', required: false },
        ],
      })
    } else if (template.value === 'prompt-focused') {
      promptSuggestions.push(
        {
          name: 'code_review',
          description: 'Review code for best practices and issues',
          arguments: [
            { name: 'language', description: 'Programming language', required: true },
            { name: 'code', description: 'Code to review', required: true },
          ],
        },
        {
          name: 'documentation',
          description: 'Generate documentation for code',
          arguments: [
            { name: 'code', description: 'Code to document', required: true },
            { name: 'format', description: 'Documentation format', required: false },
          ],
        }
      )
      toolSuggestions.push({
        name: 'customize_prompt',
        description: 'Customize prompt parameters',
        parameters: [
          { name: 'prompt_name', type: 'string', description: 'Name of prompt to customize', required: true },
          { name: 'parameters', type: 'object', description: 'Custom parameters', required: true },
        ],
      })
    } else if (template.value === 'api-facade') {
      toolSuggestions.push(
        {
          name: 'query_api',
          description: 'Query the external API with smart parsing',
          parameters: [
            { name: 'endpoint', type: 'string', description: 'API endpoint', required: true },
            { name: 'params', type: 'object', description: 'Query parameters', required: false },
          ],
        },
        {
          name: 'search_capabilities',
          description: 'Search API capabilities and endpoints',
          parameters: [
            { name: 'query', type: 'string', description: 'Search query', required: true },
          ],
        },
        {
          name: 'get_api_schema',
          description: 'Get API schema and documentation',
          parameters: [
            { name: 'endpoint', type: 'string', description: 'Endpoint to get schema for', required: false },
          ],
        }
      )
      resourceSuggestions.push(
        { uri: 'api://docs', name: 'api-docs', description: 'API documentation', mimeType: 'text/markdown' },
        { uri: 'api://endpoints', name: 'endpoints', description: 'Available API endpoints', mimeType: 'application/json' }
      )
    }

    setTemplateSuggestions({
      tools: toolSuggestions.map(s => ({ suggestion: s, accepted: true })),
      resources: resourceSuggestions.map(s => ({ suggestion: s, accepted: true })),
      prompts: promptSuggestions.map(s => ({ suggestion: s, accepted: true })),
    })
  }

  const validateStep = (stepNumber: number): boolean => {
    const newErrors: Record<string, string> = {}

    switch (stepNumber) {
      case 1:
        if (!formData.template) newErrors.template = 'Please select a template'
        break
      case 2:
        if (!formData.name) newErrors.name = 'Name is required'
        if (formData.name && !/^[a-z0-9-]+$/.test(formData.name)) {
          newErrors.name = 'Name must be lowercase with hyphens only'
        }
        if (!formData.description) newErrors.description = 'Description is required'

        // API Facade validation
        if (formData.template === 'api-facade') {
          if (!formData.apiConfig?.docsUrl) newErrors.docsUrl = 'API Documentation URL is required'
          if (!formData.apiConfig?.baseUrl) newErrors.baseUrl = 'API Base URL is required'
        }
        break
      case 3:
        // Accept template suggestions and any custom additions
        const acceptedTools = templateSuggestions.tools.filter(t => t.accepted).map(t => t.suggestion)
        const acceptedResources = templateSuggestions.resources.filter(r => r.accepted).map(r => r.suggestion)
        const acceptedPrompts = templateSuggestions.prompts.filter(p => p.accepted).map(p => p.suggestion)

        const totalTools = [...acceptedTools, ...formData.tools]
        const totalResources = [...acceptedResources, ...formData.resources]
        const totalPrompts = [...acceptedPrompts, ...formData.prompts]

        if (totalTools.length === 0 && totalResources.length === 0 && totalPrompts.length === 0) {
          newErrors.empty = 'At least one tool, resource, or prompt is required'
        }
        break
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const nextStep = () => {
    if (validateStep(step)) {
      // When moving from template selection to basic info, load suggestions
      if (step === 1 && formData.template) {
        loadTemplateSuggestions(formData.template)
      }
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

  const addResource = () => {
    if (currentResource.uri && currentResource.name) {
      setFormData({
        ...formData,
        resources: [...formData.resources, currentResource],
      })
      setCurrentResource({
        uri: '',
        name: '',
        description: '',
        mimeType: 'application/json',
      })
    }
  }

  const removeResource = (index: number) => {
    setFormData({
      ...formData,
      resources: formData.resources.filter((_, i) => i !== index),
    })
  }

  const addPromptArg = () => {
    if (currentPromptArg.name && currentPromptArg.description) {
      setCurrentPrompt({
        ...currentPrompt,
        arguments: [...currentPrompt.arguments, currentPromptArg],
      })
      setCurrentPromptArg({
        name: '',
        description: '',
        required: true,
      })
    }
  }

  const removePromptArg = (index: number) => {
    setCurrentPrompt({
      ...currentPrompt,
      arguments: currentPrompt.arguments.filter((_, i) => i !== index),
    })
  }

  const addPrompt = () => {
    if (currentPrompt.name && currentPrompt.description) {
      setFormData({
        ...formData,
        prompts: [...formData.prompts, currentPrompt],
      })
      setCurrentPrompt({
        name: '',
        description: '',
        arguments: [],
      })
    }
  }

  const removePrompt = (index: number) => {
    setFormData({
      ...formData,
      prompts: formData.prompts.filter((_, i) => i !== index),
    })
  }

  const handleSubmit = async () => {
    if (!validateStep(4)) return

    // Merge accepted suggestions with custom additions
    const acceptedTools = templateSuggestions.tools.filter(t => t.accepted).map(t => t.suggestion)
    const acceptedResources = templateSuggestions.resources.filter(r => r.accepted).map(r => r.suggestion)
    const acceptedPrompts = templateSuggestions.prompts.filter(p => p.accepted).map(p => p.suggestion)

    const mcpConfig = {
      ...formData,
      tools: [...acceptedTools, ...formData.tools],
      resources: [...acceptedResources, ...formData.resources],
      prompts: [...acceptedPrompts, ...formData.prompts],
      displayName: formData.displayName || formData.name.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      complexity: mcpFactory.estimateComplexity(formData),
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

  const getTemplateIcon = (value: string) => {
    switch (value) {
      case 'tool-focused': return <Settings className="h-8 w-8" />
      case 'resource-focused': return <Database className="h-8 w-8" />
      case 'prompt-focused': return <MessageSquare className="h-8 w-8" />
      case 'balanced': return <Package className="h-8 w-8" />
      case 'api-facade': return <Globe className="h-8 w-8" />
      case 'custom': return <Palette className="h-8 w-8" />
      default: return <Code className="h-8 w-8" />
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
              <h1 className="text-3xl font-bold">Create MCP Server</h1>
              <p className="text-muted-foreground mt-1">
                Step {step} of 4: {
                  step === 1 ? 'Choose Template' :
                  step === 2 ? 'Basic Information' :
                  step === 3 ? 'Configure Components' :
                  'Review & Create'
                }
              </p>
            </div>
          </div>
        </div>

        {/* Progress indicator */}
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={`h-2 flex-1 rounded-full transition-colors ${
                s <= step ? 'bg-primary' : 'bg-muted'
              }`}
            />
          ))}
        </div>

        {/* Step 1: Template Selection */}
        {step === 1 && (
          <div>
            <Card variant="glass" className="mb-4">
              <CardHeader>
                <CardTitle>Choose a Template</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-6">
                  Select a template that best matches your MCP server's purpose. Each template provides tailored suggestions and structure.
                </p>
                {errors.template && (
                  <p className="text-sm text-red-500 mb-4 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    {errors.template}
                  </p>
                )}
              </CardContent>
            </Card>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {templates.map((template) => (
                <Card
                  key={template.value}
                  className={`cursor-pointer transition-all hover:shadow-lg ${
                    formData.template === template.value
                      ? 'ring-2 ring-primary bg-primary/5'
                      : 'hover:border-primary/50'
                  }`}
                  onClick={() => setFormData({ ...formData, template: template.value })}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="text-primary">
                        {getTemplateIcon(template.value)}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold mb-1">{template.label}</h3>
                        <p className="text-sm text-muted-foreground mb-2">
                          {template.description}
                        </p>
                        <p className="text-xs text-muted-foreground italic">
                          Example: {template.example}
                        </p>
                      </div>
                    </div>
                    {formData.template === template.value && (
                      <div className="mt-4 flex justify-end">
                        <Check className="h-5 w-5 text-primary" />
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="flex justify-end gap-4 pt-6">
              <Button variant="default" onClick={nextStep}>
                Next: Basic Information
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Basic Information */}
        {step === 2 && (
          <Card variant="glass">
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">Server Type</label>
                  <select
                    className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                    value={formData.serverType}
                    onChange={(e) => setFormData({ ...formData, serverType: e.target.value as 'internal' | 'external' })}
                  >
                    <option value="internal">Internal (new implementation)</option>
                    <option value="external">External (wrapper for existing server)</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium">Transport Type</label>
                  <select
                    className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                    value={formData.transport}
                    onChange={(e) => setFormData({ ...formData, transport: e.target.value as 'stdio' | 'http' | 'sse' })}
                  >
                    <option value="http">HTTP (recommended)</option>
                    <option value="stdio">Standard I/O</option>
                    <option value="sse">Server-Sent Events</option>
                  </select>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
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
                  onChange={(e) => setFormData({ ...formData, language: e.target.value as 'typescript' | 'python' })}
                >
                  <option value="typescript">TypeScript</option>
                  <option value="python">Python</option>
                </select>
              </div>

              {/* API Configuration for API Facade template */}
              {formData.template === 'api-facade' && (
                <Card className="p-4 bg-muted/50">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Globe className="h-5 w-5" />
                    API Configuration
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">API Documentation URL*</label>
                      <input
                        type="url"
                        className={`w-full mt-1 px-3 py-2 rounded-md bg-background border ${
                          errors.docsUrl ? 'border-red-500' : ''
                        }`}
                        placeholder="e.g., https://api.example.com/docs"
                        value={formData.apiConfig?.docsUrl || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          apiConfig: {
                            ...formData.apiConfig,
                            docsUrl: e.target.value
                          } as ApiConfig
                        })}
                      />
                      {errors.docsUrl && (
                        <p className="text-sm text-red-500 mt-1">{errors.docsUrl}</p>
                      )}
                    </div>

                    <div>
                      <label className="text-sm font-medium">API Base URL*</label>
                      <input
                        type="url"
                        className={`w-full mt-1 px-3 py-2 rounded-md bg-background border ${
                          errors.baseUrl ? 'border-red-500' : ''
                        }`}
                        placeholder="e.g., https://api.example.com/v1"
                        value={formData.apiConfig?.baseUrl || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          apiConfig: {
                            ...formData.apiConfig,
                            baseUrl: e.target.value
                          } as ApiConfig
                        })}
                      />
                      {errors.baseUrl && (
                        <p className="text-sm text-red-500 mt-1">{errors.baseUrl}</p>
                      )}
                    </div>

                    <div>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          className="toggle"
                          checked={formData.apiConfig?.requiresApiKey || false}
                          onChange={(e) => setFormData({
                            ...formData,
                            apiConfig: {
                              ...formData.apiConfig,
                              requiresApiKey: e.target.checked
                            } as ApiConfig
                          })}
                        />
                        <span className="text-sm">API requires authentication</span>
                      </label>
                    </div>

                    {formData.apiConfig?.requiresApiKey && (
                      <div className="grid gap-4 md:grid-cols-2 pl-6">
                        <div>
                          <label className="text-sm font-medium">API Key Header Name</label>
                          <input
                            type="text"
                            className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                            placeholder="e.g., X-API-Key"
                            value={formData.apiConfig?.apiKeyName || 'X-API-Key'}
                            onChange={(e) => setFormData({
                              ...formData,
                              apiConfig: {
                                ...formData.apiConfig,
                                apiKeyName: e.target.value
                              } as ApiConfig
                            })}
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium">API Key Type</label>
                          <select
                            className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                            value={formData.apiConfig?.apiKeyType || 'header'}
                            onChange={(e) => setFormData({
                              ...formData,
                              apiConfig: {
                                ...formData.apiConfig,
                                apiKeyType: e.target.value as 'header' | 'query' | 'bearer'
                              } as ApiConfig
                            })}
                          >
                            <option value="header">Header</option>
                            <option value="query">Query Parameter</option>
                            <option value="bearer">Bearer Token</option>
                          </select>
                        </div>
                      </div>
                    )}

                    <div className="text-sm text-muted-foreground bg-background/50 p-3 rounded">
                      <p className="font-medium mb-1">Example: FamilySearch API</p>
                      <p className="text-xs">
                        Docs URL: https://www.familysearch.org/developers/docs/api<br />
                        Base URL: https://api.familysearch.org<br />
                        Auth: Bearer token required
                      </p>
                    </div>
                  </div>
                </Card>
              )}

              <div className="flex justify-between gap-4 pt-4">
                <Button variant="outline" onClick={prevStep}>
                  Previous
                </Button>
                <Button variant="default" onClick={nextStep}>
                  Next: Configure Components
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Configure Components (Tools/Resources/Prompts) */}
        {step === 3 && (
          <div className="space-y-6">
            {/* Template Suggestions */}
            {(templateSuggestions.tools.length > 0 ||
              templateSuggestions.resources.length > 0 ||
              templateSuggestions.prompts.length > 0) && (
              <Card variant="gradient">
                <CardHeader>
                  <CardTitle>Template Suggestions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {templateSuggestions.tools.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3">Suggested Tools</h3>
                      <div className="space-y-2">
                        {templateSuggestions.tools.map((item, index) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-background/50">
                            <div className="flex items-start gap-3">
                              <button
                                onClick={() => {
                                  const newSuggestions = [...templateSuggestions.tools]
                                  newSuggestions[index].accepted = !newSuggestions[index].accepted
                                  setTemplateSuggestions({ ...templateSuggestions, tools: newSuggestions })
                                }}
                                className={`mt-0.5 ${item.accepted ? 'text-green-500' : 'text-muted-foreground'}`}
                              >
                                {item.accepted ? <Check className="h-5 w-5" /> : <X className="h-5 w-5" />}
                              </button>
                              <div className="flex-1">
                                <h4 className="font-medium">{item.suggestion.name}</h4>
                                <p className="text-sm text-muted-foreground">{item.suggestion.description}</p>
                                <div className="mt-1 flex gap-2">
                                  {item.suggestion.parameters.map((param, pIndex) => (
                                    <span key={pIndex} className="text-xs px-2 py-1 rounded bg-background">
                                      {param.name}: {param.type}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {templateSuggestions.resources.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3">Suggested Resources</h3>
                      <div className="space-y-2">
                        {templateSuggestions.resources.map((item, index) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-background/50">
                            <div className="flex items-start gap-3">
                              <button
                                onClick={() => {
                                  const newSuggestions = [...templateSuggestions.resources]
                                  newSuggestions[index].accepted = !newSuggestions[index].accepted
                                  setTemplateSuggestions({ ...templateSuggestions, resources: newSuggestions })
                                }}
                                className={`mt-0.5 ${item.accepted ? 'text-green-500' : 'text-muted-foreground'}`}
                              >
                                {item.accepted ? <Check className="h-5 w-5" /> : <X className="h-5 w-5" />}
                              </button>
                              <div className="flex-1">
                                <h4 className="font-medium">{item.suggestion.name}</h4>
                                <p className="text-sm text-muted-foreground">{item.suggestion.description}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                  URI: {item.suggestion.uri} • Type: {item.suggestion.mimeType}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {templateSuggestions.prompts.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3">Suggested Prompts</h3>
                      <div className="space-y-2">
                        {templateSuggestions.prompts.map((item, index) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-background/50">
                            <div className="flex items-start gap-3">
                              <button
                                onClick={() => {
                                  const newSuggestions = [...templateSuggestions.prompts]
                                  newSuggestions[index].accepted = !newSuggestions[index].accepted
                                  setTemplateSuggestions({ ...templateSuggestions, prompts: newSuggestions })
                                }}
                                className={`mt-0.5 ${item.accepted ? 'text-green-500' : 'text-muted-foreground'}`}
                              >
                                {item.accepted ? <Check className="h-5 w-5" /> : <X className="h-5 w-5" />}
                              </button>
                              <div className="flex-1">
                                <h4 className="font-medium">{item.suggestion.name}</h4>
                                <p className="text-sm text-muted-foreground">{item.suggestion.description}</p>
                                <div className="mt-1 flex gap-2">
                                  {item.suggestion.arguments.map((arg, aIndex) => (
                                    <span key={aIndex} className="text-xs px-2 py-1 rounded bg-background">
                                      {arg.name}{arg.required ? '' : '?'}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Custom Tools */}
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Custom Tools</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Current Tool Form */}
                  <div className="p-4 rounded-lg bg-background/50 space-y-4">
                    <h3 className="font-semibold">Add Custom Tool</h3>

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

                  {/* Custom Tools List */}
                  {formData.tools.length > 0 && (
                    <div className="space-y-3">
                      <h3 className="font-semibold">Custom Tools ({formData.tools.length})</h3>
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
              </CardContent>
            </Card>

            {/* Custom Resources */}
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Custom Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-background/50 space-y-4">
                    <h3 className="font-semibold">Add Custom Resource</h3>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <label className="text-sm font-medium">Resource URI</label>
                        <input
                          type="text"
                          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                          placeholder="e.g., file://docs, db://users"
                          value={currentResource.uri}
                          onChange={(e) => setCurrentResource({ ...currentResource, uri: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Resource Name</label>
                        <input
                          type="text"
                          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                          placeholder="e.g., documentation"
                          value={currentResource.name}
                          onChange={(e) => setCurrentResource({ ...currentResource, name: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <label className="text-sm font-medium">Description</label>
                        <input
                          type="text"
                          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                          placeholder="What does this resource provide?"
                          value={currentResource.description}
                          onChange={(e) => setCurrentResource({ ...currentResource, description: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">MIME Type</label>
                        <select
                          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                          value={currentResource.mimeType}
                          onChange={(e) => setCurrentResource({ ...currentResource, mimeType: e.target.value })}
                        >
                          {mimeTypes.map((type) => (
                            <option key={type} value={type}>
                              {type}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button
                        variant="default"
                        onClick={addResource}
                        disabled={!currentResource.uri || !currentResource.name}
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add Resource
                      </Button>
                    </div>
                  </div>

                  {/* Custom Resources List */}
                  {formData.resources.length > 0 && (
                    <div className="space-y-3">
                      <h3 className="font-semibold">Custom Resources ({formData.resources.length})</h3>
                      {formData.resources.map((resource, index) => (
                        <div key={index} className="p-3 rounded-lg bg-muted/50">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="font-medium">{resource.name}</h4>
                              <p className="text-sm text-muted-foreground">{resource.description}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                URI: {resource.uri} • Type: {resource.mimeType}
                              </p>
                            </div>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removeResource(index)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Custom Prompts */}
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Custom Prompts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-background/50 space-y-4">
                    <h3 className="font-semibold">Add Custom Prompt</h3>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <label className="text-sm font-medium">Prompt Name</label>
                        <input
                          type="text"
                          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                          placeholder="e.g., generate_test"
                          value={currentPrompt.name}
                          onChange={(e) => setCurrentPrompt({ ...currentPrompt, name: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Description</label>
                        <input
                          type="text"
                          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                          placeholder="What does this prompt do?"
                          value={currentPrompt.description}
                          onChange={(e) => setCurrentPrompt({ ...currentPrompt, description: e.target.value })}
                        />
                      </div>
                    </div>

                    {/* Arguments */}
                    <div>
                      <h4 className="text-sm font-medium mb-2">Arguments</h4>

                      {currentPrompt.arguments.length > 0 && (
                        <div className="space-y-2 mb-4">
                          {currentPrompt.arguments.map((arg, index) => (
                            <div key={index} className="flex items-center gap-2 p-2 rounded bg-muted/50">
                              <span className="font-mono text-sm">{arg.name}</span>
                              <span className="text-sm text-muted-foreground flex-1">
                                {arg.description}
                              </span>
                              {!arg.required && (
                                <span className="text-xs text-yellow-500">optional</span>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => removePromptArg(index)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="grid gap-2 md:grid-cols-3 items-end">
                        <div>
                          <label className="text-xs">Name</label>
                          <input
                            type="text"
                            className="w-full px-2 py-1 text-sm rounded bg-background border"
                            placeholder="arg_name"
                            value={currentPromptArg.name}
                            onChange={(e) => setCurrentPromptArg({ ...currentPromptArg, name: e.target.value })}
                          />
                        </div>
                        <div>
                          <label className="text-xs">Description</label>
                          <input
                            type="text"
                            className="w-full px-2 py-1 text-sm rounded bg-background border"
                            placeholder="Argument description"
                            value={currentPromptArg.description}
                            onChange={(e) => setCurrentPromptArg({ ...currentPromptArg, description: e.target.value })}
                          />
                        </div>
                        <div className="flex gap-2">
                          <label className="flex items-center gap-1">
                            <input
                              type="checkbox"
                              checked={currentPromptArg.required}
                              onChange={(e) => setCurrentPromptArg({ ...currentPromptArg, required: e.target.checked })}
                            />
                            <span className="text-xs">Required</span>
                          </label>
                          <Button size="sm" variant="outline" onClick={addPromptArg}>
                            Add
                          </Button>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button
                        variant="default"
                        onClick={addPrompt}
                        disabled={!currentPrompt.name || !currentPrompt.description}
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add Prompt
                      </Button>
                    </div>
                  </div>

                  {/* Custom Prompts List */}
                  {formData.prompts.length > 0 && (
                    <div className="space-y-3">
                      <h3 className="font-semibold">Custom Prompts ({formData.prompts.length})</h3>
                      {formData.prompts.map((prompt, index) => (
                        <div key={index} className="p-3 rounded-lg bg-muted/50">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="font-medium">{prompt.name}</h4>
                              <p className="text-sm text-muted-foreground">{prompt.description}</p>
                              <div className="mt-2 flex gap-2">
                                {prompt.arguments.map((arg, aIndex) => (
                                  <span key={aIndex} className="text-xs px-2 py-1 rounded bg-background">
                                    {arg.name}{arg.required ? '' : '?'}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removePrompt(index)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {errors.empty && (
              <p className="text-sm text-red-500 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                {errors.empty}
              </p>
            )}

            <div className="flex justify-between gap-4">
              <Button variant="outline" onClick={prevStep}>
                Previous
              </Button>
              <Button variant="default" onClick={() => {
                if (validateStep(3)) {
                  setStep(4)
                }
              }}>
                Next: Review
              </Button>
            </div>
          </div>
        )}

        {/* Step 4: Review & Create */}
        {step === 4 && (
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
                      <dt className="text-muted-foreground">Template:</dt>
                      <dd className="font-medium">{templates.find(t => t.value === formData.template)?.label}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Server Type:</dt>
                      <dd className="capitalize">{formData.serverType}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Transport:</dt>
                      <dd className="uppercase">{formData.transport}</dd>
                    </div>
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
                      <dd className="capitalize">{formData.language}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Complexity:</dt>
                      <dd className="capitalize">{mcpFactory.estimateComplexity(formData)}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Description</h3>
                  <p className="text-sm">{formData.description}</p>
                </div>

                {formData.apiConfig && (
                  <div>
                    <h3 className="font-semibold mb-3">API Configuration</h3>
                    <dl className="grid gap-2 text-sm">
                      <div className="flex justify-between">
                        <dt className="text-muted-foreground">Documentation URL:</dt>
                        <dd className="font-mono text-xs truncate max-w-xs">{formData.apiConfig.docsUrl}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-muted-foreground">Base URL:</dt>
                        <dd className="font-mono text-xs truncate max-w-xs">{formData.apiConfig.baseUrl}</dd>
                      </div>
                      {formData.apiConfig.requiresApiKey && (
                        <>
                          <div className="flex justify-between">
                            <dt className="text-muted-foreground">API Key Name:</dt>
                            <dd className="font-mono">{formData.apiConfig.apiKeyName}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-muted-foreground">API Key Type:</dt>
                            <dd>{formData.apiConfig.apiKeyType}</dd>
                          </div>
                        </>
                      )}
                    </dl>
                  </div>
                )}

                <div>
                  <h3 className="font-semibold mb-3">Components Summary</h3>
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="p-3 rounded-lg bg-muted/50 text-center">
                      <Code className="h-6 w-6 mx-auto mb-2 text-primary" />
                      <div className="text-2xl font-bold">
                        {templateSuggestions.tools.filter(t => t.accepted).length + formData.tools.length}
                      </div>
                      <div className="text-sm text-muted-foreground">Tools</div>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/50 text-center">
                      <Database className="h-6 w-6 mx-auto mb-2 text-primary" />
                      <div className="text-2xl font-bold">
                        {templateSuggestions.resources.filter(r => r.accepted).length + formData.resources.length}
                      </div>
                      <div className="text-sm text-muted-foreground">Resources</div>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/50 text-center">
                      <MessageSquare className="h-6 w-6 mx-auto mb-2 text-primary" />
                      <div className="text-2xl font-bold">
                        {templateSuggestions.prompts.filter(p => p.accepted).length + formData.prompts.length}
                      </div>
                      <div className="text-sm text-muted-foreground">Prompts</div>
                    </div>
                  </div>
                </div>

                <div className="bg-muted/50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <FileJson className="h-4 w-4" />
                    What will be created:
                  </h3>
                  <ul className="space-y-1 text-sm">
                    <li>• MCP server implementation in {formData.language}</li>
                    <li>• Complete project structure with all dependencies</li>
                    {formData.serverType === 'internal' && (
                      <>
                        <li>• Dockerfile for containerization</li>
                        <li>• Kubernetes deployment manifests</li>
                      </>
                    )}
                    <li>• README with documentation and examples</li>
                    <li>• Test suite for all components</li>
                    <li>• MCP manifest.json configuration</li>
                    {formData.template === 'api-facade' && (
                      <li>• API client with documentation parsing</li>
                    )}
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
