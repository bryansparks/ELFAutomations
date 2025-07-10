import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { RAGClient } from "./rag/client.js";
import { ComponentRegistry } from "./registry/components.js";
import { ImplementationValidator } from "./registry/validator.js";
import { KnowledgeLoader } from "./knowledge/loader.js";

class UISystemContextServer {
  private server: Server;
  private ragClient: RAGClient;
  private componentRegistry: ComponentRegistry;
  private validator: ImplementationValidator;

  constructor() {
    this.server = new Server(
      {
        name: "ui-system-context",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      }
    );

    // Initialize services
    this.ragClient = new RAGClient({
      url: process.env.QDRANT_URL || "http://localhost:6333",
      collection: process.env.QDRANT_COLLECTION || "ui_system_docs",
    });

    this.componentRegistry = new ComponentRegistry();
    this.validator = new ImplementationValidator(this.componentRegistry);

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "get_component_spec",
          description: "Get detailed specifications for a UI component including props, examples, and design tokens",
          inputSchema: {
            type: "object",
            properties: {
              component: {
                type: "string",
                description: "Name of the component (e.g., Button, Card, Form)",
              },
              includeExamples: {
                type: "boolean",
                description: "Include usage examples",
                default: true,
              },
            },
            required: ["component"],
          },
        },
        {
          name: "search_design_patterns",
          description: "Search design system documentation for patterns, best practices, and guidelines",
          inputSchema: {
            type: "object",
            properties: {
              query: {
                type: "string",
                description: "Search query (e.g., 'responsive layout', 'form validation')",
              },
              category: {
                type: "string",
                enum: ["layout", "color", "typography", "interaction", "accessibility", "all"],
                description: "Category to search within",
                default: "all",
              },
              limit: {
                type: "number",
                description: "Maximum number of results",
                default: 5,
              },
            },
            required: ["query"],
          },
        },
        {
          name: "validate_implementation",
          description: "Validate if component implementation follows design system rules and best practices",
          inputSchema: {
            type: "object",
            properties: {
              code: {
                type: "string",
                description: "React/JSX code to validate",
              },
              componentType: {
                type: "string",
                description: "Expected component type for validation",
              },
              strict: {
                type: "boolean",
                description: "Use strict validation (fail on warnings)",
                default: false,
              },
            },
            required: ["code"],
          },
        },
        {
          name: "get_design_tokens",
          description: "Get design tokens (colors, spacing, typography) for consistent styling",
          inputSchema: {
            type: "object",
            properties: {
              category: {
                type: "string",
                enum: ["colors", "spacing", "typography", "shadows", "borders", "all"],
                description: "Token category",
              },
              format: {
                type: "string",
                enum: ["css", "js", "scss"],
                description: "Output format",
                default: "js",
              },
            },
            required: ["category"],
          },
        },
        {
          name: "suggest_components",
          description: "Suggest appropriate components based on use case description",
          inputSchema: {
            type: "object",
            properties: {
              useCase: {
                type: "string",
                description: "Description of what you're trying to build",
              },
              requirements: {
                type: "array",
                items: { type: "string" },
                description: "Specific requirements (e.g., 'responsive', 'accessible')",
              },
            },
            required: ["useCase"],
          },
        },
      ],
    }));

    // List available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: "design://principles",
          name: "Design Principles",
          description: "Core design principles and philosophy of our design system",
          mimeType: "text/markdown",
        },
        {
          uri: "design://tokens/all",
          name: "All Design Tokens",
          description: "Complete design token reference (colors, spacing, typography)",
          mimeType: "application/json",
        },
        {
          uri: "design://components/catalog",
          name: "Component Catalog",
          description: "Full catalog of available UI components",
          mimeType: "application/json",
        },
        {
          uri: "design://patterns/overview",
          name: "Pattern Library",
          description: "Common UI patterns and their implementations",
          mimeType: "text/markdown",
        },
        {
          uri: "design://accessibility/guidelines",
          name: "Accessibility Guidelines",
          description: "WCAG compliance and accessibility best practices",
          mimeType: "text/markdown",
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "get_component_spec":
            return await this.getComponentSpec(args);

          case "search_design_patterns":
            return await this.searchDesignPatterns(args);

          case "validate_implementation":
            return await this.validateImplementation(args);

          case "get_design_tokens":
            return await this.getDesignTokens(args);

          case "suggest_components":
            return await this.suggestComponents(args);

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    });

    // Handle resource reads
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      try {
        const content = await this.readResource(uri);
        return {
          contents: [
            {
              uri,
              mimeType: uri.endsWith(".json") ? "application/json" : "text/markdown",
              text: content,
            },
          ],
        };
      } catch (error) {
        return {
          contents: [
            {
              uri,
              mimeType: "text/plain",
              text: `Error reading resource: ${error.message}`,
            },
          ],
        };
      }
    });
  }

  private async getComponentSpec(args: any) {
    const { component, includeExamples = true } = args;
    const spec = await this.componentRegistry.getComponentSpec(component);

    if (!spec) {
      return {
        content: [
          {
            type: "text",
            text: `Component '${component}' not found in the design system.`,
          },
        ],
      };
    }

    // Format the response
    let response = `# ${spec.name} Component\n\n`;
    response += `**Category:** ${spec.category}\n`;
    response += `**Description:** ${spec.description}\n\n`;

    // Props
    response += "## Props\n\n";
    for (const prop of spec.props) {
      response += `### ${prop.name}${prop.required ? " (required)" : ""}\n`;
      response += `- **Type:** ${prop.type}\n`;
      if (prop.enum) response += `- **Options:** ${prop.enum.join(", ")}\n`;
      if (prop.default) response += `- **Default:** ${prop.default}\n`;
      response += `- **Description:** ${prop.description}\n\n`;
    }

    // Design Tokens
    response += "## Design Tokens\n\n";
    response += `Use these tokens for consistent styling:\n`;
    for (const token of spec.designTokens) {
      response += `- ${token}\n`;
    }

    // Examples
    if (includeExamples && spec.examples.length > 0) {
      response += "\n## Examples\n\n";
      for (const example of spec.examples) {
        response += `### ${example.title}\n\n`;
        response += "```jsx\n" + example.code + "\n```\n\n";
      }
    }

    // Best Practices
    if (spec.bestPractices.length > 0) {
      response += "## Best Practices\n\n";
      for (const practice of spec.bestPractices) {
        response += `- ${practice}\n`;
      }
    }

    // Accessibility
    response += "\n## Accessibility\n\n";
    response += `- **ARIA attributes:** ${spec.accessibility.aria.join(", ")}\n`;
    response += `- **Keyboard support:** ${spec.accessibility.keyboard.join(", ")}\n`;

    return {
      content: [
        {
          type: "text",
          text: response,
        },
      ],
    };
  }

  private async searchDesignPatterns(args: any) {
    const { query, category = "all", limit = 5 } = args;

    // Use RAG to search documentation
    const results = await this.ragClient.searchDocumentation(query, {
      category,
      limit,
    });

    if (results.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: `No design patterns found matching "${query}".`,
          },
        ],
      };
    }

    let response = `# Design Patterns for "${query}"\n\n`;

    for (const result of results) {
      response += `## ${result.title}\n\n`;
      response += `**Relevance:** ${(result.relevance * 100).toFixed(0)}%\n`;
      response += `**Category:** ${result.category}\n`;
      response += `**Source:** ${result.source}\n\n`;
      response += result.content + "\n\n";

      if (result.relatedPatterns?.length > 0) {
        response += `**Related:** ${result.relatedPatterns.join(", ")}\n\n`;
      }

      response += "---\n\n";
    }

    return {
      content: [
        {
          type: "text",
          text: response,
        },
      ],
    };
  }

  private async validateImplementation(args: any) {
    const { code, componentType, strict = false } = args;

    const result = await this.validator.validateImplementation(code, componentType);

    let response = "# Validation Results\n\n";

    if (result.valid && result.violations.length === 0) {
      response += "✅ **Implementation is valid!**\n\n";
      response += "The code follows all design system rules and best practices.";
    } else {
      response += `❌ **Found ${result.violations.length} issue(s)**\n\n`;

      // Group by severity
      const errors = result.violations.filter((v) => v.level === "error");
      const warnings = result.violations.filter((v) => v.level === "warning");
      const suggestions = result.violations.filter((v) => v.level === "suggestion");

      if (errors.length > 0) {
        response += "## Errors (must fix)\n\n";
        for (const error of errors) {
          response += `- ${error.message}\n`;
          if (error.fix) response += `  **Fix:** ${error.fix}\n`;
        }
        response += "\n";
      }

      if (warnings.length > 0) {
        response += "## Warnings (should fix)\n\n";
        for (const warning of warnings) {
          response += `- ${warning.message}\n`;
          if (warning.fix) response += `  **Fix:** ${warning.fix}\n`;
        }
        response += "\n";
      }

      if (suggestions.length > 0) {
        response += "## Suggestions (consider)\n\n";
        for (const suggestion of suggestions) {
          response += `- ${suggestion.message}\n`;
        }
      }
    }

    // Add corrected example if fixes available
    if (result.correctedCode) {
      response += "\n## Corrected Implementation\n\n";
      response += "```jsx\n" + result.correctedCode + "\n```";
    }

    return {
      content: [
        {
          type: "text",
          text: response,
        },
      ],
    };
  }

  private async getDesignTokens(args: any) {
    const { category, format = "js" } = args;

    const tokens = await this.componentRegistry.getDesignTokens(category);

    let response = `# Design Tokens - ${category}\n\n`;

    switch (format) {
      case "css":
        response += "```css\n:root {\n";
        for (const [key, value] of Object.entries(tokens)) {
          response += `  --${key}: ${value};\n`;
        }
        response += "}\n```";
        break;

      case "scss":
        response += "```scss\n";
        for (const [key, value] of Object.entries(tokens)) {
          response += `$${key}: ${value};\n`;
        }
        response += "```";
        break;

      case "js":
      default:
        response += "```javascript\nexport const tokens = {\n";
        for (const [key, value] of Object.entries(tokens)) {
          response += `  ${key}: '${value}',\n`;
        }
        response += "};\n```";
    }

    return {
      content: [
        {
          type: "text",
          text: response,
        },
      ],
    };
  }

  private async suggestComponents(args: any) {
    const { useCase, requirements = [] } = args;

    // Use RAG to understand the use case
    const context = await this.ragClient.searchDocumentation(useCase, {
      category: "components",
      limit: 10,
    });

    // Get component suggestions based on context
    const suggestions = await this.componentRegistry.suggestComponents(useCase, requirements, context);

    let response = `# Component Suggestions for: ${useCase}\n\n`;

    if (requirements.length > 0) {
      response += `**Requirements:** ${requirements.join(", ")}\n\n`;
    }

    for (const suggestion of suggestions) {
      response += `## ${suggestion.component}\n`;
      response += `**Confidence:** ${(suggestion.confidence * 100).toFixed(0)}%\n`;
      response += `**Reason:** ${suggestion.reason}\n\n`;

      if (suggestion.example) {
        response += "**Example:**\n";
        response += "```jsx\n" + suggestion.example + "\n```\n";
      }

      if (suggestion.alternatives?.length > 0) {
        response += `**Alternatives:** ${suggestion.alternatives.join(", ")}\n`;
      }

      response += "\n---\n\n";
    }

    // Add composition suggestion if multiple components needed
    if (suggestions.length > 1) {
      response += "## Suggested Composition\n\n";
      response += "You might need to combine these components:\n\n";
      response += "```jsx\n";
      response += this.generateCompositionExample(suggestions);
      response += "\n```";
    }

    return {
      content: [
        {
          type: "text",
          text: response,
        },
      ],
    };
  }

  private async readResource(uri: string) {
    // Parse the URI
    const parts = uri.split("://")[1].split("/");
    const category = parts[0];
    const resource = parts.slice(1).join("/");

    switch (category) {
      case "principles":
        return await KnowledgeLoader.loadPrinciples();

      case "tokens":
        return JSON.stringify(await this.componentRegistry.getDesignTokens(resource), null, 2);

      case "components":
        if (resource === "catalog") {
          return JSON.stringify(await this.componentRegistry.getCatalog(), null, 2);
        }
        break;

      case "patterns":
        return await KnowledgeLoader.loadPattern(resource);

      case "accessibility":
        return await KnowledgeLoader.loadAccessibilityGuidelines();

      default:
        throw new Error(`Unknown resource category: ${category}`);
    }
  }

  private generateCompositionExample(suggestions: any[]): string {
    // Generate a basic composition example
    const mainComponent = suggestions[0].component;
    const childComponents = suggestions.slice(1).map((s) => s.component);

    let example = `<${mainComponent}>\n`;
    for (const child of childComponents) {
      example += `  <${child} />\n`;
    }
    example += `</${mainComponent}>`;

    return example;
  }

  async start() {
    // Initialize knowledge base
    await KnowledgeLoader.initialize();
    await this.componentRegistry.loadComponents();

    // Start the server
    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    console.error("UI System Context MCP server started");
  }
}

// Main entry point
const server = new UISystemContextServer();
server.start().catch(console.error);
