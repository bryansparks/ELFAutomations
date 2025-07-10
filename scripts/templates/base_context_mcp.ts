/**
 * Base Context MCP Server
 *
 * Provides a template for creating domain-specific context MCP servers
 * that integrate with the Context-as-a-Service RAG backend.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  Resource,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import { z } from "zod";

// Configuration schema
const ConfigSchema = z.object({
  domain: z.string().describe("Context domain (e.g., 'ui-system', 'architecture')"),
  contextApiUrl: z.string().url().default("http://localhost:8080"),
  apiKey: z.string().describe("API key for Context-as-a-Service"),
  collection: z.string().default("default").describe("Qdrant collection name"),
  name: z.string().optional(),
  description: z.string().optional(),
});

type Config = z.infer<typeof ConfigSchema>;

/**
 * Base class for context MCP servers
 */
export abstract class BaseContextMCP {
  protected server: Server;
  protected config: Config;
  protected contextApiClient: axios.AxiosInstance;

  constructor(config: Partial<Config>) {
    // Validate and merge config
    this.config = ConfigSchema.parse({
      ...config,
      name: config.name || `${config.domain}-context`,
      description: config.description || `Context provider for ${config.domain}`,
    });

    // Initialize server
    this.server = new Server(
      {
        name: this.config.name!,
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      }
    );

    // Initialize API client
    this.contextApiClient = axios.create({
      baseURL: this.config.contextApiUrl,
      headers: {
        "X-API-Key": this.config.apiKey,
        "Content-Type": "application/json",
      },
    });

    // Setup handlers
    this.setupBaseHandlers();
    this.setupDomainHandlers();
  }

  /**
   * Setup base handlers common to all context MCPs
   */
  private setupBaseHandlers(): void {
    // Handle tool listing
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const tools = [
        ...this.getBaseTools(),
        ...this.getDomainTools(),
      ];
      return { tools };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      // Base tools
      switch (name) {
        case "search_context":
          return await this.searchContext(args);
        case "get_related_concepts":
          return await this.getRelatedConcepts(args);
        case "validate_against_standards":
          return await this.validateAgainstStandards(args);
        default:
          // Try domain-specific tools
          return await this.handleDomainTool(name, args);
      }
    });

    // Handle resource listing
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      const resources = this.getDomainResources();
      return { resources };
    });

    // Handle resource reading
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;
      return await this.readDomainResource(uri);
    });
  }

  /**
   * Get base tools available in all context MCPs
   */
  private getBaseTools(): Tool[] {
    return [
      {
        name: "search_context",
        description: `Search for ${this.config.domain} context`,
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query",
            },
            limit: {
              type: "number",
              description: "Maximum results (default: 10)",
              default: 10,
            },
            filters: {
              type: "object",
              description: "Additional filters",
              additionalProperties: true,
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_related_concepts",
        description: "Get concepts related to a topic",
        inputSchema: {
          type: "object",
          properties: {
            concept: {
              type: "string",
              description: "The concept to find relations for",
            },
            depth: {
              type: "number",
              description: "Relationship depth (default: 1)",
              default: 1,
            },
          },
          required: ["concept"],
        },
      },
      {
        name: "validate_against_standards",
        description: `Validate content against ${this.config.domain} standards`,
        inputSchema: {
          type: "object",
          properties: {
            content: {
              type: "string",
              description: "Content to validate",
            },
            type: {
              type: "string",
              description: "Type of validation",
            },
          },
          required: ["content"],
        },
      },
    ];
  }

  /**
   * Search for context using the backend API
   */
  protected async searchContext(args: any): Promise<any> {
    try {
      const response = await this.contextApiClient.post("/api/v1/search", {
        query: args.query,
        collection: this.config.collection,
        limit: args.limit || 10,
        filters: {
          domain: this.config.domain,
          ...args.filters,
        },
      });

      // Format results for MCP response
      const results = response.data.results.map((result: any) => ({
        content: result.content,
        score: result.score,
        metadata: result.metadata,
      }));

      return {
        content: [
          {
            type: "text",
            text: this.formatSearchResults(results, args.query),
          },
        ],
      };
    } catch (error) {
      console.error("Context search failed:", error);
      return {
        content: [
          {
            type: "text",
            text: `Failed to search context: ${error.message}`,
          },
        ],
      };
    }
  }

  /**
   * Get related concepts (to be implemented with graph queries)
   */
  protected async getRelatedConcepts(args: any): Promise<any> {
    // This would query Neo4j or similar graph database
    // For now, use context search as fallback
    return await this.searchContext({
      query: `related concepts to ${args.concept}`,
      limit: 20,
    });
  }

  /**
   * Validate content against standards
   */
  protected async validateAgainstStandards(args: any): Promise<any> {
    // Search for relevant standards
    const standards = await this.searchContext({
      query: `${this.config.domain} standards validation rules ${args.type}`,
      limit: 5,
    });

    // In a real implementation, this would use LLM to validate
    return {
      content: [
        {
          type: "text",
          text: `Validation results for ${args.type}:\n\n${standards.content[0].text}`,
        },
      ],
    };
  }

  /**
   * Format search results for display
   */
  protected formatSearchResults(results: any[], query: string): string {
    if (results.length === 0) {
      return `No results found for: "${query}"`;
    }

    let formatted = `Found ${results.length} results for: "${query}"\n\n`;

    results.forEach((result, index) => {
      formatted += `### Result ${index + 1} (Score: ${result.score.toFixed(3)})\n`;
      formatted += `${result.content}\n`;

      if (result.metadata) {
        formatted += `\n**Metadata:**\n`;
        Object.entries(result.metadata).forEach(([key, value]) => {
          formatted += `- ${key}: ${value}\n`;
        });
      }
      formatted += "\n---\n\n";
    });

    return formatted;
  }

  /**
   * Start the MCP server
   */
  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error(`${this.config.name} MCP server started`);
  }

  // Abstract methods to be implemented by domain-specific MCPs
  protected abstract setupDomainHandlers(): void;
  protected abstract getDomainTools(): Tool[];
  protected abstract getDomainResources(): Resource[];
  protected abstract handleDomainTool(name: string, args: any): Promise<any>;
  protected abstract readDomainResource(uri: string): Promise<any>;
}

/**
 * Example implementation for UI System Context
 */
export class UISystemContextMCP extends BaseContextMCP {
  constructor() {
    super({
      domain: "ui-system",
      collection: "design_system_docs",
      apiKey: process.env.CONTEXT_API_KEY!,
      description: "UI/UX Design System Context Provider",
    });
  }

  protected setupDomainHandlers(): void {
    // Domain-specific setup
  }

  protected getDomainTools(): Tool[] {
    return [
      {
        name: "get_component_spec",
        description: "Get detailed component specifications",
        inputSchema: {
          type: "object",
          properties: {
            component: {
              type: "string",
              description: "Component name (e.g., Button, Card)",
            },
          },
          required: ["component"],
        },
      },
      {
        name: "suggest_ui_patterns",
        description: "Suggest UI patterns for use cases",
        inputSchema: {
          type: "object",
          properties: {
            useCase: {
              type: "string",
              description: "The use case to get patterns for",
            },
          },
          required: ["useCase"],
        },
      },
    ];
  }

  protected getDomainResources(): Resource[] {
    return [
      {
        uri: "design://components",
        name: "Component Library",
        description: "All available UI components",
        mimeType: "text/plain",
      },
      {
        uri: "design://tokens",
        name: "Design Tokens",
        description: "Design system tokens (colors, spacing, etc.)",
        mimeType: "text/plain",
      },
    ];
  }

  protected async handleDomainTool(name: string, args: any): Promise<any> {
    switch (name) {
      case "get_component_spec":
        return await this.searchContext({
          query: `${args.component} component specification props API examples`,
          filters: { type: "component_spec" },
        });

      case "suggest_ui_patterns":
        return await this.searchContext({
          query: `UI patterns for ${args.useCase}`,
          filters: { type: "pattern" },
        });

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  protected async readDomainResource(uri: string): Promise<any> {
    // Parse URI and return appropriate content
    if (uri === "design://components") {
      const components = await this.searchContext({
        query: "all UI components list",
        limit: 50,
      });
      return {
        contents: [
          {
            uri,
            mimeType: "text/plain",
            text: components.content[0].text,
          },
        ],
      };
    }

    throw new Error(`Unknown resource: ${uri}`);
  }
}

// Start server if run directly
if (require.main === module) {
  const mcp = new UISystemContextMCP();
  mcp.start().catch(console.error);
}
