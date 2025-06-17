import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';

export abstract class BaseMCPServer {
  protected server: Server;
  protected serverName: string;
  protected serverVersion: string;

  constructor(name: string, version: string = '1.0.0') {
    this.serverName = name;
    this.serverVersion = version;
    this.server = new Server(
      {
        name: this.serverName,
        version: this.serverVersion,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: this.getTools(),
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      return await this.handleToolCall(name, args || {});
    });
  }

  protected abstract getTools(): Tool[];
  protected abstract handleToolCall(name: string, args: any): Promise<any>;

  protected createTool(
    name: string,
    description: string,
    inputSchema: z.ZodSchema
  ): Tool {
    return {
      name,
      description,
      inputSchema: inputSchema as any,
    };
  }

  protected validateInput<T>(schema: z.ZodSchema<T>, input: unknown): T {
    try {
      return schema.parse(input);
    } catch (error) {
      throw new Error(`Invalid input: ${error}`);
    }
  }

  protected createSuccessResponse(content: any): any {
    return {
      content: [
        {
          type: 'text',
          text: typeof content === 'string' ? content : JSON.stringify(content, null, 2),
        },
      ],
    };
  }

  protected createErrorResponse(error: string): any {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error}`,
        },
      ],
      isError: true,
    };
  }

  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error(`${this.serverName} MCP server running on stdio`);
  }
}
