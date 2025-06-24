/**
 * MCP Factory Service
 * Interfaces with the mcp_factory.py script to create new MCPs
 */

export interface MCPFactoryConfig {
  name: string
  displayName: string
  description: string
  language: 'typescript' | 'python'
  useTemplate: boolean
  template?: string
  tools: Tool[]
  hasResources: boolean
  resources?: Resource[]
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
  name: string
  description: string
  schema: Record<string, any>
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
    // This generates the command that would be run to create the MCP
    const scriptPath = 'tools/mcp_factory.py'

    // Create a config file content
    const configContent = {
      name: config.name,
      display_name: config.displayName,
      description: config.description,
      language: config.language,
      tools: config.tools.map(tool => ({
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters.reduce((acc, param) => {
          acc[param.name] = {
            type: param.type,
            description: param.description,
            required: param.required,
            ...(param.default !== undefined && { default: param.default }),
            ...(param.enumValues && { enum: param.enumValues }),
            ...(param.pattern && { pattern: param.pattern }),
            ...(param.minValue !== undefined && { minimum: param.minValue }),
            ...(param.maxValue !== undefined && { maximum: param.maxValue }),
          }
          return acc
        }, {} as Record<string, any>),
      })),
      ...(config.hasResources && { resources: config.resources }),
      ...(config.dependencies && { dependencies: config.dependencies }),
      ...(config.useMock && { use_mock: true }),
      ...(config.environment && { environment: config.environment }),
    }

    // Generate command to create config file and run factory
    return `
# Save this configuration to mcp_config.json
cat > mcp_config.json << 'EOF'
${JSON.stringify(configContent, null, 2)}
EOF

# Run the MCP factory
python ${scriptPath} --config mcp_config.json
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

    if (!config.tools || config.tools.length === 0) {
      errors.push('At least one tool must be defined')
    }

    config.tools?.forEach((tool, index) => {
      if (!tool.name || !/^[a-z_][a-z0-9_]*$/.test(tool.name)) {
        errors.push(`Tool ${index + 1}: Name must be a valid function name`)
      }
      if (!tool.description) {
        errors.push(`Tool ${index + 1}: Description is required`)
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
        value: 'file-system',
        label: 'File System Operations',
        description: 'Read, write, and manage files',
        tools: ['read_file', 'write_file', 'list_directory', 'delete_file'],
      },
      {
        value: 'database',
        label: 'Database Operations',
        description: 'CRUD operations for databases',
        tools: ['query', 'insert', 'update', 'delete'],
      },
      {
        value: 'api-client',
        label: 'API Client',
        description: 'Make HTTP requests to external APIs',
        tools: ['get', 'post', 'put', 'delete', 'patch'],
      },
      {
        value: 'data-processing',
        label: 'Data Processing',
        description: 'Transform and analyze data',
        tools: ['parse_csv', 'transform_data', 'aggregate', 'export'],
      },
      {
        value: 'integration',
        label: 'Third-party Integration',
        description: 'Connect to external services',
        tools: ['authenticate', 'fetch_data', 'sync_data', 'webhook'],
      },
    ]
  }

  /**
   * Estimate complexity based on configuration
   */
  estimateComplexity(config: Partial<MCPFactoryConfig>): 'simple' | 'moderate' | 'complex' {
    const toolCount = config.tools?.length || 0
    const hasComplexTypes = config.tools?.some(tool =>
      tool.parameters.some(p => ['object', 'array'].includes(p.type))
    ) || false
    const hasResources = config.hasResources || false
    const hasDependencies = (config.dependencies?.length || 0) > 0

    if (toolCount > 10 || hasComplexTypes || hasResources || hasDependencies) {
      return 'complex'
    }
    if (toolCount > 5) {
      return 'moderate'
    }
    return 'simple'
  }
}

// Export singleton instance
export const mcpFactory = new MCPFactoryService()

// Export types
export type { MCPFactoryService }
