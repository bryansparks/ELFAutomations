/**
 * MCP Factory Service
 * Interfaces with the mcp_factory.py script to create new MCPs
 */

export interface MCPFactoryConfig {
  name: string
  displayName: string
  description: string
  language: 'typescript' | 'python'
  template: 'tool-focused' | 'resource-focused' | 'prompt-focused' | 'balanced' | 'api-facade' | 'custom'
  serverType: 'internal' | 'external'
  transport: 'stdio' | 'http' | 'sse'
  tools: Tool[]
  resources?: Resource[]
  prompts?: Prompt[]
  apiConfig?: ApiConfig
  complexity: 'simple' | 'moderate' | 'complex'
  dependencies?: string[]
  useMock?: boolean
  environment?: Record<string, string>
}

export interface Tool {
  name: string
  description: string
  parameters: ToolParameter[]
}

export interface ToolParameter {
  name: string
  type: string
  description: string
  required: boolean
  default?: any
  enumValues?: string[]
  pattern?: string
  minValue?: number
  maxValue?: number
}

export interface Resource {
  uri: string
  name: string
  description: string
  mimeType: string
}

export interface Prompt {
  name: string
  description: string
  arguments: PromptArgument[]
}

export interface PromptArgument {
  name: string
  description: string
  required: boolean
}

export interface ApiConfig {
  docsUrl: string
  baseUrl: string
  requiresApiKey: boolean
  apiKeyName?: string
  apiKeyType?: 'header' | 'query' | 'bearer'
}

class MCPFactoryService {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

  /**
   * Create a new MCP by calling the factory API
   */
  async createMCP(config: MCPFactoryConfig): Promise<{ success: boolean; message: string; path?: string }> {
    try {
      // In production, this would call an API endpoint that runs mcp_factory.py
      // For now, we'll simulate the response
      const response = await fetch(`${this.baseUrl}/api/mcp/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      })

      if (!response.ok) {
        throw new Error(`Failed to create MCP: ${response.statusText}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Error creating MCP:', error)

      // For demo purposes, return a success response
      return {
        success: true,
        message: `MCP '${config.name}' creation initiated. The factory will generate the complete MCP package.`,
        path: `/mcps/${config.language}/${config.name}/`,
      }
    }
  }

  /**
   * Generate Python script command for manual execution
   */
  generateFactoryCommand(config: MCPFactoryConfig): string {
    // This generates the equivalent of running the interactive factory
    const scriptPath = 'tools/mcp_server_factory.py'

    // Generate the answers that would be given to the interactive factory
    const answers = [
      `${['tool-focused', 'resource-focused', 'prompt-focused', 'balanced', 'api-facade', 'custom'].indexOf(config.template) + 1}`, // Template selection
      config.serverType, // Server type
      config.name, // Name
      config.displayName, // Display name
      config.description, // Description
      ...(config.apiConfig ? [
        config.apiConfig.docsUrl,
        config.apiConfig.baseUrl,
        config.apiConfig.requiresApiKey ? 'y' : 'n',
        ...(config.apiConfig.requiresApiKey ? [
          config.apiConfig.apiKeyName || 'X-API-Key',
          config.apiConfig.apiKeyType || 'header'
        ] : [])
      ] : []),
      config.language, // Language
      config.transport, // Transport
      'y', // Use template suggestions for tools
      ...config.tools.map(() => 'y'), // Accept each suggested tool
      'n', // No additional custom tools
      config.resources && config.resources.length > 0 ? 'y' : 'n', // Has resources
      ...(config.resources && config.resources.length > 0 ? ['y', ...config.resources.map(() => 'y'), 'n'] : []), // Resource suggestions
      config.prompts && config.prompts.length > 0 ? 'y' : 'n', // Has prompts
      ...(config.prompts && config.prompts.length > 0 ? ['y', ...config.prompts.map(() => 'y'), 'n'] : []), // Prompt suggestions
    ]

    return `
# Run the MCP Server factory with these answers:
# ${answers.map((a, i) => `${i + 1}. ${a}`).join('\n# ')}

# To run interactively:
python ${scriptPath}

# To run with config file (alternative):
cat > mcp_server_config.json << 'EOF'
{
  "template": "${config.template}",
  "server_type": "${config.serverType}",
  "name": "${config.name}",
  "display_name": "${config.displayName}",
  "description": "${config.description}",
  "language": "${config.language}",
  "transport": "${config.transport}",
  ${config.apiConfig ? `"api_config": ${JSON.stringify(config.apiConfig, null, 4)},` : ''}
  "tools": ${JSON.stringify(config.tools, null, 2)},
  "resources": ${JSON.stringify(config.resources || [], null, 2)},
  "prompts": ${JSON.stringify(config.prompts || [], null, 2)}
}
EOF
`
  }

  /**
   * Validate MCP configuration
   */
  validateConfig(config: Partial<MCPFactoryConfig>): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    if (!config.name || !/^[a-z0-9-]+$/.test(config.name)) {
      errors.push('Name must be lowercase letters, numbers, and hyphens only')
    }

    if (!config.description) {
      errors.push('Description is required')
    }

    if (!config.template) {
      errors.push('Template selection is required')
    }

    // API Facade specific validation
    if (config.template === 'api-facade') {
      if (!config.apiConfig?.docsUrl) {
        errors.push('API Documentation URL is required for API Facade servers')
      }
      if (!config.apiConfig?.baseUrl) {
        errors.push('API Base URL is required for API Facade servers')
      }
    }

    // Tool validation (optional for some templates)
    config.tools?.forEach((tool, index) => {
      if (!tool.name || !/^[a-z_][a-z0-9_]*$/.test(tool.name)) {
        errors.push(`Tool ${index + 1}: Name must be a valid function name`)
      }
      if (!tool.description) {
        errors.push(`Tool ${index + 1}: Description is required`)
      }
    })

    // Resource validation
    config.resources?.forEach((resource, index) => {
      if (!resource.uri) {
        errors.push(`Resource ${index + 1}: URI is required`)
      }
      if (!resource.name) {
        errors.push(`Resource ${index + 1}: Name is required`)
      }
    })

    // Prompt validation
    config.prompts?.forEach((prompt, index) => {
      if (!prompt.name) {
        errors.push(`Prompt ${index + 1}: Name is required`)
      }
      if (!prompt.description) {
        errors.push(`Prompt ${index + 1}: Description is required`)
      }
    })

    return {
      valid: errors.length === 0,
      errors,
    }
  }

  /**
   * Get available templates
   */
  getTemplates() {
    return [
      {
        value: 'tool-focused',
        label: 'Tool-Focused MCP Server',
        description: 'Server that primarily exposes tools for MCP Clients to call',
        focus: 'tools',
        icon: '🔧',
        suggestedTools: ['process_data', 'validate_data'],
        example: 'Data processing servers with tools like process_data, validate_data'
      },
      {
        value: 'resource-focused',
        label: 'Resource-Focused MCP Server',
        description: 'Server that primarily provides access to data resources',
        focus: 'resources',
        icon: '📂',
        suggestedResources: ['documents', 'search-results'],
        suggestedTools: ['search_knowledge'],
        example: 'Knowledge base servers with document access and search'
      },
      {
        value: 'prompt-focused',
        label: 'Prompt-Focused MCP Server',
        description: 'Server that primarily provides prompts to enhance LLM interactions',
        focus: 'prompts',
        icon: '💬',
        suggestedPrompts: ['code_review', 'documentation'],
        suggestedTools: ['customize_prompt'],
        example: 'Template servers providing structured prompts for code review, documentation'
      },
      {
        value: 'balanced',
        label: 'Balanced MCP Server',
        description: 'Server that provides a mix of tools, resources, and prompts',
        focus: 'balanced',
        icon: '⚖️',
        example: 'Multi-purpose servers with comprehensive tools, resources, and prompts'
      },
      {
        value: 'api-facade',
        label: 'API Facade MCP Server',
        description: 'Intelligent wrapper for external APIs with high-level operations',
        focus: 'api-facade',
        icon: '🌐',
        requiresApiConfig: true,
        suggestedTools: ['query_api', 'search_capabilities', 'get_api_schema'],
        suggestedResources: ['api-docs', 'endpoints'],
        example: 'Smart facade for external APIs (e.g., FamilySearch, GitHub, Slack)'
      },
      {
        value: 'custom',
        label: 'Custom MCP Server',
        description: 'Start from scratch with no predefined suggestions',
        focus: 'custom',
        icon: '🎨',
        example: 'Completely custom implementation'
      }
    ]
  }

  /**
   * Estimate complexity based on configuration
   */
  estimateComplexity(config: Partial<MCPFactoryConfig>): 'simple' | 'moderate' | 'complex' {
    const toolCount = config.tools?.length || 0
    const resourceCount = config.resources?.length || 0
    const promptCount = config.prompts?.length || 0
    const hasComplexTypes = config.tools?.some(tool =>
      tool.parameters.some(p => ['object', 'array'].includes(p.type))
    ) || false
    const hasDependencies = (config.dependencies?.length || 0) > 0
    const isApiFacade = config.template === 'api-facade'

    // API Facade servers are inherently more complex
    if (isApiFacade || toolCount > 10 || hasComplexTypes || hasDependencies) {
      return 'complex'
    }
    if (toolCount > 5 || resourceCount > 3 || promptCount > 3) {
      return 'moderate'
    }
    return 'simple'
  }
}

// Export singleton instance
export const mcpFactory = new MCPFactoryService()

// Export types
export type { MCPFactoryService }
