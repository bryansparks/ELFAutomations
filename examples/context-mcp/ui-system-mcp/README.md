# UI System Context MCP Server

Example implementation of a Context MCP server that provides UI/UX design system information to AI IDE tools.

## Architecture

```
ui-system-mcp/
├── src/
│   ├── server.ts          # Main MCP server
│   ├── rag/              # RAG integration
│   │   ├── client.ts     # Qdrant client
│   │   └── indexer.ts    # Document indexer
│   ├── registry/         # Component registry
│   │   ├── components.ts # Component specs
│   │   └── validator.ts  # Implementation validator
│   └── knowledge/        # Knowledge sources
│       ├── loader.ts     # Load design docs
│       └── parser.ts     # Parse component specs
├── data/                 # Design system data
│   ├── components/       # Component specs
│   ├── patterns/        # Design patterns
│   └── tokens/          # Design tokens
└── k8s/                 # Kubernetes manifests
```

## Quick Start

```bash
# Install dependencies
npm install

# Index design documentation into RAG
npm run index-docs

# Start the MCP server
npm start

# Or run in development mode
npm run dev
```

## Tools Provided

### 1. `get_component_spec`
Get detailed specifications for a UI component.

```json
{
  "component": "Button",
  "result": {
    "name": "Button",
    "category": "interactive",
    "props": [
      {
        "name": "variant",
        "type": "string",
        "enum": ["primary", "secondary", "ghost"],
        "default": "primary"
      }
    ],
    "examples": ["<Button variant='primary'>Click me</Button>"],
    "accessibility": {
      "aria": ["label", "pressed"],
      "keyboard": ["Enter", "Space"]
    }
  }
}
```

### 2. `search_design_patterns`
Search for design patterns and best practices.

```json
{
  "query": "responsive layout",
  "results": [
    {
      "pattern": "Grid System",
      "description": "12-column responsive grid",
      "usage": "Use for page layouts",
      "example": "..."
    }
  ]
}
```

### 3. `validate_implementation`
Check if code follows design system rules.

```json
{
  "code": "<Button color='red'>Test</Button>",
  "violations": [
    {
      "level": "error",
      "message": "Invalid prop 'color'. Use 'variant' instead."
    }
  ]
}
```

## Configuration

### Environment Variables
```bash
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=ui_system_docs
OPENAI_API_KEY=your-key-here
DESIGN_SYSTEM_PATH=/data/design-system
```

### Design System Structure
```
/data/design-system/
├── components/
│   ├── button.yaml
│   ├── card.yaml
│   └── form.yaml
├── tokens/
│   ├── colors.json
│   ├── spacing.json
│   └── typography.json
└── patterns/
    ├── layouts.md
    ├── navigation.md
    └── data-display.md
```

## Integration with AI Tools

### Claude Code (via MCP)
```json
{
  "mcpServers": {
    "ui-system": {
      "command": "node",
      "args": ["/path/to/ui-system-mcp/dist/server.js"]
    }
  }
}
```

### AgentGateway Registration
```python
gateway.register_mcp({
    "name": "ui-system-context",
    "endpoint": "http://ui-system-mcp:8080",
    "description": "UI/UX design system context",
    "category": "context-provider"
})
```

## Example Usage in AI IDE

When using Claude Code or similar tools:

```
User: "Create a login form following our design system"

Claude Code:
1. Uses get_component_spec('Form')
2. Uses get_component_spec('Input')
3. Uses search_design_patterns('authentication')
4. Generates code following the specs
5. Uses validate_implementation() to verify

Result: Perfectly compliant form implementation
```

## Extending the Server

### Adding New Component Types
1. Add spec to `/data/components/`
2. Run `npm run index-docs` to update RAG
3. Component automatically available

### Adding Custom Validation Rules
```typescript
// src/registry/custom-rules.ts
export const customRules = [
  {
    name: "no-inline-styles",
    check: (ast) => !ast.hasInlineStyles(),
    message: "Use design tokens instead of inline styles"
  }
];
```

### Adding New Tools
```typescript
// src/tools/new-tool.ts
export const checkAccessibility = {
  name: "check_accessibility",
  description: "Check component accessibility",
  handler: async (params) => {
    // Implementation
  }
};
```

## Performance Considerations

- RAG queries are cached for 5 minutes
- Component specs are loaded into memory on startup
- Validation uses AST parsing for efficiency
- Supports concurrent requests

## Deployment

```bash
# Build Docker image
docker build -t elf/ui-system-mcp .

# Deploy to K8s
kubectl apply -f k8s/

# Or use with ElfAutomations pipeline
cd /tools && python mcp_factory.py --type context --name ui-system
```
