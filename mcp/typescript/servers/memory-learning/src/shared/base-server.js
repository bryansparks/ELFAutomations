import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema, } from '@modelcontextprotocol/sdk/types.js';
export class BaseMCPServer {
    server;
    serverName;
    serverVersion;
    constructor(name, version = '1.0.0') {
        this.serverName = name;
        this.serverVersion = version;
        this.server = new Server({
            name: this.serverName,
            version: this.serverVersion,
        }, {
            capabilities: {
                tools: {},
            },
        });
        this.setupHandlers();
    }
    setupHandlers() {
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
    createTool(name, description, inputSchema) {
        return {
            name,
            description,
            inputSchema: inputSchema,
        };
    }
    validateInput(schema, input) {
        try {
            return schema.parse(input);
        }
        catch (error) {
            throw new Error(`Invalid input: ${error}`);
        }
    }
    createSuccessResponse(content) {
        return {
            content: [
                {
                    type: 'text',
                    text: typeof content === 'string' ? content : JSON.stringify(content, null, 2),
                },
            ],
        };
    }
    createErrorResponse(error) {
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
    async start() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error(`${this.serverName} MCP server running on stdio`);
    }
}
//# sourceMappingURL=base-server.js.map