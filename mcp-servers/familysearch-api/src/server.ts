/**
 * FamilySearch API Gateway - MCP Server
 * Intelligent wrapper for FamilySearch genealogy APIs
 *
 * This is an MCP Server that exposes tools, resources, and prompts
 * to MCP Clients (like Teams or Claude) via the Model Context Protocol.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
  ReadResourceRequestSchema,
  McpError,
  Tool,
  Resource,
  Prompt,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import axios, { AxiosInstance } from "axios";
import { load } from "js-yaml";

console.error("[FamilySearch API Gateway] Starting MCP Server...");


// API Configuration
const API_BASE_URL = "https://api.familysearch.org";
const API_DOCS_URL = "https://www.familysearch.org/developers/docs/api/swagger.json";
const API_KEY_NAME = "X-API-Key";
const API_KEY_TYPE = "header";

// Cache for API documentation
let apiSchema: any = null;
let endpointCache: Map<string, any> = new Map();


// Tool schemas for parameter validation
const queryApiSchema = z.object({
  query: z.string(.describe("Natural language query to execute"),
  context: z.object({}.describe("Additional context for the query").optional(),
});
type Query_apiArgs = z.infer<typeof queryApiSchema>;

const searchCapabilitiesSchema = z.object({
  search_term: z.string(.describe("Term to search for in API capabilities"),
});
type Search_capabilitiesArgs = z.infer<typeof searchCapabilitiesSchema>;

const getApiSchemaSchema = z.object({
  endpoint: z.string(.describe("API endpoint to get schema for"),
});
type Get_api_schemaArgs = z.infer<typeof getApiSchemaSchema>;

// Tools exposed by this server
const TOOLS: Tool[] = [
  {
    "name": "query_api",
    "description": "Execute high-level queries against the external API",
    "inputSchema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Natural language query to execute"
        },
        "context": {
          "type": "object",
          "description": "Additional context for the query",
          "required": false
        }
      },
      "required": [
        "query"
      ],
      "additionalProperties": false
    }
  },
  {
    "name": "search_capabilities",
    "description": "Search available API capabilities and endpoints",
    "inputSchema": {
      "type": "object",
      "properties": {
        "search_term": {
          "type": "string",
          "description": "Term to search for in API capabilities"
        }
      },
      "required": [
        "search_term"
      ],
      "additionalProperties": false
    }
  },
  {
    "name": "get_api_schema",
    "description": "Get schema information for specific API endpoints",
    "inputSchema": {
      "type": "object",
      "properties": {
        "endpoint": {
          "type": "string",
          "description": "API endpoint to get schema for"
        }
      },
      "required": [
        "endpoint"
      ],
      "additionalProperties": false
    }
  }
];

// Resources exposed by this server
const RESOURCES: Resource[] = [];

// Prompts provided by this server
const PROMPTS: Prompt[] = [];

/**
 * FamilySearch API Gateway MCP Server
 * This server can be used by any MCP Client through the Model Context Protocol
 */
class FamilysearchApiServer {
  private server: Server;
  private apiClient: AxiosInstance;
  private apiKey: string | null = null;
  private apiSchema: any = null;

  constructor() {
    console.error("[FamilySearch API Gateway] Initializing server...");

    this.server = new Server(
      {
        name: "familysearch-api",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {"listChanged": true},
          resources: {},
          prompts: {},
        },
      }
    );
    // Initialize API client
    this.apiClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "ELF-Automations-MCP-Server/1.0.0"
      }
    });

    // Load API documentation
    this.loadApiDocumentation();

    this.setupHandlers();
    console.error("[FamilySearch API Gateway] Server initialized successfully");
  }

  private setupHandlers() {
    // Register tool handlers
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      console.error("[FamilySearch API Gateway] Client requested tool list");
      return { tools: TOOLS };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name: toolName, arguments: args } = request.params;
      console.error(`[FamilySearch API Gateway] Client calling tool: ${toolName}`);

      try {
        switch (toolName) {
          case "query_api": {
            const validatedArgs = queryApiSchema.parse(args);
            const result = await this.queryApi(validatedArgs);
            return [{ type: "text", text: JSON.stringify(result, null, 2) }];
          }
          case "search_capabilities": {
            const validatedArgs = searchCapabilitiesSchema.parse(args);
            const result = await this.searchCapabilities(validatedArgs);
            return [{ type: "text", text: JSON.stringify(result, null, 2) }];
          }
          case "get_api_schema": {
            const validatedArgs = getApiSchemaSchema.parse(args);
            const result = await this.getApiSchema(validatedArgs);
            return [{ type: "text", text: JSON.stringify(result, null, 2) }];
          }
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${toolName}`
            );
        }
      } catch (error) {
        if (error instanceof z.ZodError) {
          throw new McpError(
            ErrorCode.InvalidParams,
            `Invalid parameters: ${error.message}`
          );
        }
        throw error;
      }
    });

    // Register resource handlers
    if (RESOURCES.length > 0) {
      this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
        console.error("[FamilySearch API Gateway] Client requested resource list");
        return { resources: RESOURCES };
      });

      this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
        const { uri } = request.params;
        console.error(`[FamilySearch API Gateway] Client reading resource: ${uri}`);

        const resource = RESOURCES.find((r) => r.uri === uri);
        if (!resource) {
          throw new McpError(
            ErrorCode.InvalidParams,
            `Unknown resource: ${uri}`
          );
        }

        return {
          contents: [
            {
              uri,
              mimeType: resource.mimeType,
              text: await this.readResource(uri),
            },
          ],
        };
      });
    }

    // Register prompt handlers
    if (PROMPTS.length > 0) {
      this.server.setRequestHandler(ListPromptsRequestSchema, async () => {
        console.error("[FamilySearch API Gateway] Client requested prompt list");
        return { prompts: PROMPTS };
      });

      this.server.setRequestHandler(GetPromptRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;
        console.error(`[FamilySearch API Gateway] Client getting prompt: ${name}`);

        const prompt = PROMPTS.find((p) => p.name === name);
        if (!prompt) {
          throw new McpError(
            ErrorCode.InvalidParams,
            `Unknown prompt: ${name}`
          );
        }

        return {
          description: prompt.description,
          messages: await this.getPromptMessages(name, args),
        };
      });
    }
  }

  private async queryApi(args: Query_apiArgs): Promise<any> {
    console.error("[query_api] Forwarding to external MCP server");

    try {
      // TODO: Forward this request to the external MCP server
      // Example using axios:
      // const response = await axios.post(`${this.externalUrl}/tools/query_api`, args);
      // return response.data;

      return {
        success: true,
        message: "Forwarded to external server",
        result: {}
      };
    } catch (error) {
      console.error("[query_api] External server error:", error);
      throw new McpError(ErrorCode.InternalError, "External server error");
    }
  }

  private async searchCapabilities(args: Search_capabilitiesArgs): Promise<any> {
    console.error("[search_capabilities] Forwarding to external MCP server");

    try {
      // TODO: Forward this request to the external MCP server
      // Example using axios:
      // const response = await axios.post(`${this.externalUrl}/tools/search_capabilities`, args);
      // return response.data;

      return {
        success: true,
        message: "Forwarded to external server",
        result: {}
      };
    } catch (error) {
      console.error("[search_capabilities] External server error:", error);
      throw new McpError(ErrorCode.InternalError, "External server error");
    }
  }

  private async getApiSchema(args: Get_api_schemaArgs): Promise<any> {
    console.error("[get_api_schema] Forwarding to external MCP server");

    try {
      // TODO: Forward this request to the external MCP server
      // Example using axios:
      // const response = await axios.post(`${this.externalUrl}/tools/get_api_schema`, args);
      // return response.data;

      return {
        success: true,
        message: "Forwarded to external server",
        result: {}
      };
    } catch (error) {
      console.error("[get_api_schema] External server error:", error);
      throw new McpError(ErrorCode.InternalError, "External server error");
    }
  }

  private async readResource(uri: string): Promise<string> {
    console.error(`[FamilySearch API Gateway] Reading resource: ${uri}`);
    // TODO: Implement resource reading logic
    return JSON.stringify({
      message: "Resource content for " + uri,
      timestamp: new Date().toISOString()
    });
  }

  private async getPromptMessages(name: string, args?: Record<string, string>): Promise<any[]> {
    console.error(`[FamilySearch API Gateway] Generating prompt: ${name}`);
    // TODO: Implement prompt generation logic
    return [
      {
        role: "user",
        content: {
          type: "text",
          text: `Prompt ${name} with args: ${JSON.stringify(args)}`,
        },
      },
    ];
  }
  private async loadApiDocumentation(): Promise<void> {
    try {
      console.error("[API Facade] Loading API documentation...");
      const response = await axios.get(API_DOCS_URL);

      if (API_DOCS_URL.endsWith('.json')) {
        this.apiSchema = response.data;
      } else if (API_DOCS_URL.endsWith('.yaml') || API_DOCS_URL.endsWith('.yml')) {
        this.apiSchema = load(response.data);
      } else {
        console.error("[API Facade] Unsupported documentation format");
        return;
      }

      console.error(`[API Facade] Loaded API schema with ${Object.keys(this.apiSchema.paths || {}).length} endpoints`);
    } catch (error) {
      console.error(`[API Facade] Failed to load API documentation: ${error}`);
    }
  }

  private async makeApiRequest(endpoint: string, method: string = 'GET', data?: any): Promise<any> {
    try {
      const config: any = {
        method,
        url: endpoint,
        data
      };

      // Add API key if required
      if (this.apiKey) {
        if (API_KEY_TYPE === 'header') {
          config.headers = { [API_KEY_NAME]: this.apiKey };
        } else if (API_KEY_TYPE === 'query') {
          config.params = { [API_KEY_NAME]: this.apiKey };
        } else if (API_KEY_TYPE === 'bearer') {
          config.headers = { Authorization: `Bearer ${this.apiKey}` };
        }
      }

      const response = await this.apiClient.request(config);
      return response.data;
    } catch (error: any) {
      console.error(`[API Facade] API request failed: ${error.message}`);
      throw new McpError(
        ErrorCode.InternalError,
        `API request failed: ${error.message}`
      );
    }
  }

  private async findBestEndpoint(query: string): Promise<string | null> {
    if (!this.apiSchema?.paths) {
      return null;
    }

    // Simple matching - find endpoints that match query terms
    const queryLower = query.toLowerCase();
    const endpoints = Object.keys(this.apiSchema.paths);

    // Score endpoints based on path and description matches
    const scored = endpoints.map(endpoint => {
      let score = 0;
      const endpointLower = endpoint.toLowerCase();

      // Direct path matches
      if (endpointLower.includes(queryLower)) score += 10;

      // Check operation descriptions
      const operations = this.apiSchema.paths[endpoint];
      Object.values(operations || {}).forEach((op: any) => {
        if (op.summary?.toLowerCase().includes(queryLower)) score += 5;
        if (op.description?.toLowerCase().includes(queryLower)) score += 3;
        op.tags?.forEach((tag: string) => {
          if (tag.toLowerCase().includes(queryLower)) score += 2;
        });
      });

      return { endpoint, score };
    })
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score);

    return scored.length > 0 ? scored[0].endpoint : null;
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("[FamilySearch API Gateway] MCP Server running - ready for client connections");
  }
}

// Start the MCP Server
const server = new FamilysearchApiServer();
server.run().catch((error) => {
  console.error("[FamilySearch API Gateway] Server error:", error);
  process.exit(1);
});
