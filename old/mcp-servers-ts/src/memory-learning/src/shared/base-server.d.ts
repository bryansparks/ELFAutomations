import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
export declare abstract class BaseMCPServer {
    protected server: Server;
    protected serverName: string;
    protected serverVersion: string;
    constructor(name: string, version?: string);
    private setupHandlers;
    protected abstract getTools(): Tool[];
    protected abstract handleToolCall(name: string, args: any): Promise<any>;
    protected createTool(name: string, description: string, inputSchema: z.ZodSchema): Tool;
    protected validateInput<T>(schema: z.ZodSchema<T>, input: unknown): T;
    protected createSuccessResponse(content: any): any;
    protected createErrorResponse(error: string): any;
    start(): Promise<void>;
}
//# sourceMappingURL=base-server.d.ts.map