# MCP SDK Best Practices and Standards

## Overview

This document outlines the best practices for creating MCP (Model Context Protocol) servers that properly follow Anthropic's official SDK patterns. The MCP SDK provides a standardized way for AI assistants to interact with external tools and resources.

## Official MCP SDK Structure

### Core Components

1. **Server Class** - From `@modelcontextprotocol/sdk`
2. **Transport Layer** - stdio, HTTP, or SSE
3. **Request Handlers** - Typed schema validation
4. **Type Definitions** - Strict typing for all interfaces

### TypeScript Example (SDK-Compliant)

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  McpError,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
```

### Python Example (SDK-Compliant)

```python
from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent, INVALID_PARAMS
```

## Key Differences from Our Previous Implementation

### 1. **Tool Definition Structure**

**SDK-Compliant (Correct):**
```json
{
  "name": "query_data",
  "description": "Query data from database",
  "inputSchema": {
    "type": "object",
    "properties": {
      "table": {
        "type": "string",
        "description": "Table name"
      }
    },
    "required": ["table"],
    "additionalProperties": false
  }
}
```

**Our Previous (Incorrect):**
```json
{
  "name": "query_data",
  "description": "Query data from database",
  "parameters": {
    "table": "string"  // Too simplified
  }
}
```

### 2. **Request Handler Pattern**

**SDK-Compliant:**
```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  // Proper validation and error handling
});
```

**Our Previous:**
```typescript
async handleToolCall(name: string, args: any): Promise<any> {
  // Manual routing without SDK patterns
}
```

### 3. **Error Handling**

**SDK-Compliant:**
```typescript
throw new McpError(
  ErrorCode.InvalidParams,
  `Invalid parameters: ${error.message}`
);
```

**Our Previous:**
```typescript
throw new Error("Invalid parameters");  // Generic errors
```

## Best Practices

### 1. **Always Use JSON Schema for Tool Parameters**

Tools must define parameters using full JSON Schema:

```typescript
const toolSchema = {
  type: "object",
  properties: {
    query: {
      type: "string",
      description: "SQL query to execute",
      minLength: 1,
      maxLength: 1000
    },
    limit: {
      type: "integer",
      description: "Maximum rows to return",
      minimum: 1,
      maximum: 1000,
      default: 100
    }
  },
  required: ["query"],
  additionalProperties: false
};
```

### 2. **Implement All Three MCP Primitives**

Even if not all are used initially:

```typescript
capabilities: {
  tools: {},      // For actions
  resources: {},  // For data access
  prompts: {}     // For LLM interactions
}
```

### 3. **Use Proper Transport Initialization**

**stdio (Most Common):**
```typescript
const transport = new StdioServerTransport();
await server.connect(transport);
```

**HTTP:**
```typescript
const transport = new HttpServerTransport({ port: 3000 });
await server.connect(transport);
```

### 4. **Implement Health Checks**

Always include a lightweight health check tool:

```typescript
{
  name: "health_check",
  description: "Check server health",
  inputSchema: {
    type: "object",
    properties: {},
    additionalProperties: false
  }
}
```

### 5. **Resource URIs Should Be Meaningful**

Use proper URI schemes:
- `file://path/to/resource`
- `db://table/users`
- `config://settings/api`
- `memory://conversations/latest`

### 6. **Validate Everything**

Use Zod (TypeScript) or Pydantic (Python):

```typescript
const QuerySchema = z.object({
  table: z.string().min(1).max(64),
  filter: z.record(z.any()).optional(),
  limit: z.number().int().min(1).max(1000).default(100)
});

// In handler
const validated = QuerySchema.parse(args);
```

### 7. **Return Structured Responses**

Always return consistent response formats:

```typescript
return {
  success: true,
  data: results,
  metadata: {
    count: results.length,
    executionTime: Date.now() - startTime
  }
};
```

## Common Mistakes to Avoid

### 1. **Not Using the SDK Types**
❌ `interface Tool { name: string; ... }`
✅ `import { Tool } from "@modelcontextprotocol/sdk/types.js"`

### 2. **Weak Parameter Validation**
❌ `if (!args.table) throw new Error("Missing table")`
✅ Use JSON Schema with proper validation

### 3. **Ignoring Transport Abstraction**
❌ Direct stdin/stdout handling
✅ Use SDK transport classes

### 4. **Missing Error Codes**
❌ `throw new Error("Not found")`
✅ `throw new McpError(ErrorCode.InvalidParams, "Not found")`

### 5. **No Capability Declaration**
❌ Implementing handlers without declaring capabilities
✅ Always declare in initialization options

## Migration Guide

To migrate existing MCPs to SDK-compliant versions:

1. **Update Imports**
   - Add official SDK imports
   - Remove custom protocol implementations

2. **Restructure Tool Definitions**
   - Convert simple parameters to JSON Schema
   - Add proper descriptions and constraints

3. **Use SDK Request Handlers**
   - Replace custom routing with `setRequestHandler`
   - Implement proper error handling

4. **Add Type Safety**
   - Use TypeScript/Python types throughout
   - Validate all inputs and outputs

5. **Test with MCP Inspector**
   - Validate against official MCP inspector
   - Ensure all capabilities work correctly

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io)
- [TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)

## Conclusion

Following the official MCP SDK patterns ensures:
- **Compatibility** with all MCP clients
- **Type Safety** throughout the implementation
- **Better Error Handling** with proper error codes
- **Future Proofing** as the protocol evolves
- **Easier Debugging** with standardized patterns

Always use the SDK-compliant factory (`mcp_factory_sdk_compliant.py`) for new MCPs to ensure proper implementation from the start.
