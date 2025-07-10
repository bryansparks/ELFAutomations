/**
 * Health Status - MCP Server
 * This MCP Server will monitor the infractructure parts of this system and make sure they are healthy. This will include the Qdrant Vecctor DB, the Neo4j db, the N8N service, the kubernetes secrets manager, and others.
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

console.error("[Health Status] Starting MCP Server...");

// Tool schemas for parameter validation


// Tools exposed by this server
const TOOLS: Tool[] = [
  {
    "name": "overall-status",
    "description": "Provides an aggregrate health status of the monitored services.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    }
  },
  {
    "name": "qdrant-status",
    "description": "This tool with give specific health status on the Qdrant Vector DB",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    }
  },
  {
    "name": "n8n-status",
    "description": "This tool will give health status for the N8N service.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    }
  },
  {
    "name": "kube-status",
    "description": "This tool gives a general kubernetes status but more specifically the secrets manager of k3s.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    }
  }
];

// Resources exposed by this server
const RESOURCES: Resource[] = [];

// Prompts provided by this server
const PROMPTS: Prompt[] = [];

/**
 * Health Status MCP Server
 * This server can be used by any MCP Client through the Model Context Protocol
 */
class HealthStatusServer {
  private server: Server;

  constructor() {
    console.error("[Health Status] Initializing server...");

    this.server = new Server(
      {
        name: "health-status",
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

    this.setupHandlers();
    console.error("[Health Status] Server initialized successfully");
  }

  private setupHandlers() {
    // Register tool handlers
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      console.error("[Health Status] Client requested tool list");
      return { tools: TOOLS };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name: toolName, arguments: args } = request.params;
      console.error(`[Health Status] Client calling tool: ${toolName}`);

      try {
        switch (toolName) {
          case "overall-status": {

            const result = await this.overall-status(args);
            return [{ type: "text", text: JSON.stringify(result, null, 2) }];
          }
          case "qdrant-status": {

            const result = await this.qdrant-status(args);
            return [{ type: "text", text: JSON.stringify(result, null, 2) }];
          }
          case "n8n-status": {

            const result = await this.n8n-status(args);
            return [{ type: "text", text: JSON.stringify(result, null, 2) }];
          }
          case "kube-status": {

            const result = await this.kube-status(args);
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
        console.error("[Health Status] Client requested resource list");
        return { resources: RESOURCES };
      });

      this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
        const { uri } = request.params;
        console.error(`[Health Status] Client reading resource: ${uri}`);

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
        console.error("[Health Status] Client requested prompt list");
        return { prompts: PROMPTS };
      });

      this.server.setRequestHandler(GetPromptRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;
        console.error(`[Health Status] Client getting prompt: ${name}`);

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

  private async overall-status(args: any): Promise<any> {
    console.error("[overall-status] Processing request");

    // TODO: Implement overall-status logic
    // This is where the actual tool functionality goes

    return {
      success: true,
      message: "Successfully executed overall-status",
      result: {
        // Return actual results here
      }
    };
  }

  private async qdrant-status(args: any): Promise<any> {
    console.error("[qdrant-status] Processing request");

    // TODO: Implement qdrant-status logic
    // This is where the actual tool functionality goes

    return {
      success: true,
      message: "Successfully executed qdrant-status",
      result: {
        // Return actual results here
      }
    };
  }

  private async n8n-status(args: any): Promise<any> {
    console.error("[n8n-status] Processing request");

    // TODO: Implement n8n-status logic
    // This is where the actual tool functionality goes

    return {
      success: true,
      message: "Successfully executed n8n-status",
      result: {
        // Return actual results here
      }
    };
  }

  private async kube-status(args: any): Promise<any> {
    console.error("[kube-status] Processing request");

    // TODO: Implement kube-status logic
    // This is where the actual tool functionality goes

    return {
      success: true,
      message: "Successfully executed kube-status",
      result: {
        // Return actual results here
      }
    };
  }

  private async readResource(uri: string): Promise<string> {
    console.error(`[Health Status] Reading resource: ${uri}`);
    // TODO: Implement resource reading logic
    return JSON.stringify({
      message: "Resource content for " + uri,
      timestamp: new Date().toISOString()
    });
  }

  private async getPromptMessages(name: string, args?: Record<string, string>): Promise<any[]> {
    console.error(`[Health Status] Generating prompt: ${name}`);
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

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("[Health Status] MCP Server running - ready for client connections");
  }
}

// Start the MCP Server
const server = new HealthStatusServer();
server.run().catch((error) => {
  console.error("[Health Status] Server error:", error);
  process.exit(1);
});
