# MCP Factory Improvement Analysis

## Why Memory & Learning MCP Couldn't Be Built with mcp_factory.py

### Current Limitations

1. **Simplified Tool Definition**
   - **Current**: Only collects name and description
   - **Needed**: Complex parameter schemas with types, validation, optional/required fields
   - **Example**: `retrieve_memories` needed filters object with nested properties

2. **No Complex Schema Support**
   - **Current**: Fixed `inputSchema` with empty properties
   - **Needed**: Zod schemas, enums, nested objects, arrays, validation rules
   - **Example**: `StoreMemorySchema` with enum types, optional fields, min/max values

3. **Limited Implementation Scaffolding**
   - **Current**: TODO placeholders in generated code
   - **Needed**: Method stubs, error handling, type definitions
   - **Missing**: No way to specify dependencies, imports, or helper methods

4. **No TypeScript MCP Infrastructure**
   - **Current**: `_generate_typescript_mcp()` is empty stub
   - **Needed**: Full TypeScript generation with proper imports, types, classes
   - **Missing**: Base class extension, proper SDK usage patterns

5. **No External Dependencies Management**
   - **Current**: Basic requirements.txt with mcp, asyncio, pydantic
   - **Needed**: Specify additional dependencies (supabase, uuid, custom packages)
   - **Example**: Memory MCP needed @supabase/supabase-js, uuid, zod

6. **No Mock/Development Mode Support**
   - **Current**: Generates production-only code
   - **Needed**: Development vs production switches, mock implementations
   - **Example**: MockQdrantClient for when real service unavailable

7. **No Resource Definition**
   - **Current**: Only tools, no resources
   - **Needed**: Resources like memory_stats, learning_patterns
   - **Missing**: Resource schema and implementation

8. **Limited Environment Configuration**
   - **Current**: Basic env var collection
   - **Needed**: Required vs optional, defaults, validation
   - **Example**: Fallback behavior when QDRANT_URL not set

## Improvements Needed for Complex MCPs

### 1. Enhanced Tool Definition
```python
# Instead of simple name/description
tools = []
while True:
    tool = {
        "name": prompt("Tool name"),
        "description": prompt("Description"),
        "parameters": collect_parameters(),  # New
        "returns": define_return_type(),     # New
        "errors": define_error_cases(),      # New
    }
```

### 2. Parameter Schema Builder
```python
def collect_parameters():
    params = {}
    while True:
        param_name = prompt("Parameter name")
        if not param_name:
            break

        param_type = prompt("Type", choices=["string", "number", "boolean", "object", "array", "enum"])
        required = confirm("Required?")

        if param_type == "enum":
            values = prompt("Enum values (comma-separated)").split(",")

        if param_type == "object":
            properties = collect_parameters()  # Recursive

        params[param_name] = build_schema(param_type, required, ...)
```

### 3. TypeScript Generation Support
```python
def _generate_typescript_mcp(self, config: MCPConfig, mcp_dir: Path):
    # Generate proper TypeScript with:
    # - Zod schemas
    # - Type definitions
    # - Base class extension
    # - Async/await patterns
    # - Error handling
```

### 4. Dependency Management
```python
# During MCP creation
dependencies = prompt("Additional dependencies (comma-separated)")
dev_dependencies = prompt("Dev dependencies (comma-separated)")

# In package.json generation
"dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    **parse_dependencies(dependencies)
}
```

### 5. Template System
```python
# Use templates for complex patterns
TEMPLATES = {
    "supabase_integration": load_template("supabase.ts"),
    "vector_search": load_template("vector_search.ts"),
    "mock_client": load_template("mock_client.ts"),
}

# Let user choose patterns
patterns = prompt("Integration patterns", choices=list(TEMPLATES.keys()))
```

### 6. Advanced Configuration
```yaml
# Generate config.yaml for complex MCPs
mcp_config:
  development:
    use_mocks: true
    mock_implementations:
      - qdrant: MockQdrantClient
      - embeddings: MockEmbeddings

  production:
    services:
      - name: qdrant
        url: ${QDRANT_URL}
        fallback: mock
```

### 7. Interactive Schema Designer
```python
# Visual/interactive way to build complex schemas
schema_designer = SchemaDesigner()
schema_designer.add_field("content", "string", required=True)
schema_designer.add_field("type", "enum", values=["learning", "decision"])
schema_designer.add_nested("context", {...})
```

### 8. Code Generation from OpenAPI/AsyncAPI
```python
# Import from existing API specs
if prompt("Import from OpenAPI spec?"):
    spec_file = prompt("OpenAPI spec path")
    tools = parse_openapi_to_tools(spec_file)
```

### 9. Testing Infrastructure
```python
# Generate test files automatically
def generate_tests(config: MCPConfig):
    # Generate test file with:
    # - Mock client setup
    # - Test cases for each tool
    # - Integration tests
    # - Error case tests
```

### 10. MCP Composition
```python
# Combine multiple smaller MCPs
base_mcps = prompt("Base MCPs to extend", multiselect=True)
# Generate MCP that composes/extends others
```

## Recommended Approach

1. **Keep mcp_factory.py for simple MCPs** (3-5 basic tools)
2. **Create mcp_factory_advanced.py** for complex MCPs with:
   - Schema builder UI
   - Template system
   - Dependency management
   - Mock support
3. **Build a library of templates** for common patterns:
   - Database integration
   - Vector search
   - External API wrapper
   - Analytics/monitoring
4. **Consider a DSL or YAML format** for MCP definitions:
   ```yaml
   name: memory-learning
   tools:
     - name: store_memory
       params:
         content:
           type: string
           required: true
         type:
           type: enum
           values: [learning, decision]
   ```

This would make the factory much more capable while keeping it maintainable.
