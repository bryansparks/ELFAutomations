# MCP Factory Complexity Detection & Code Paths

## Complexity Levels

### 🟢 SIMPLE
- **1-5 tools**
- **Basic parameter types only** (string, number, boolean)
- **No resources**

### 🟡 MODERATE
- **6-10 tools** OR
- **Has complex parameter types** (object, array)
- **May have resources**

### 🔴 COMPLEX
- **More than 10 tools**
- **Complex schemas and integrations**
- **Multiple resources**

## Detection Logic

```python
def _determine_complexity(self, tools, resources) -> ComplexityLevel:
    tool_count = len(tools)

    # Check for complex parameters
    has_complex_params = any(
        any(p.type in [ParameterType.OBJECT, ParameterType.ARRAY]
            for p in tool.parameters.values())
        for tool in tools
    )

    # Decision tree
    if tool_count <= 5 and not has_complex_params and len(resources) == 0:
        return ComplexityLevel.SIMPLE
    elif tool_count <= 10 or has_complex_params:
        return ComplexityLevel.MODERATE
    else:
        return ComplexityLevel.COMPLEX
```

## Code Path Differences

### 1. **User Prompts** (Lines 294-309)

#### SIMPLE MCPs:
- ❌ Skip dependency collection
- ❌ Skip mock implementation prompt
- ❌ Skip environment variables

#### MODERATE/COMPLEX MCPs:
- ✅ Ask about additional dependencies
- ✅ Offer mock implementations
- ✅ Collect environment variables

```python
if complexity != ComplexityLevel.SIMPLE:
    # Dependencies
    if Confirm.ask("\nAdd additional dependencies?", default=True):
        dependencies = self._collect_dependencies(language, templates)

    # Mock support
    use_mock = Confirm.ask("\nInclude mock implementations for development?", default=True)

    # Environment variables
    environment = self._collect_environment_vars()
```

### 2. **Generated Code Structure**

#### All Complexity Levels Get:
- ✅ server.ts with tool implementations
- ✅ package.json
- ✅ tsconfig.json
- ✅ README.md
- ✅ config.json

#### MODERATE/COMPLEX Additionally Get:
- ✅ Mock implementations (if use_mock=True)
- ✅ Enhanced dependencies in package.json
- ✅ Environment variable configuration
- ✅ More detailed README sections

### 3. **Schema Generation Differences**

#### SIMPLE:
```typescript
// Basic parameter types only
const SimpleToolSchema = z.object({
    name: z.string(),
    age: z.number(),
    active: z.boolean()
});
```

#### MODERATE/COMPLEX:
```typescript
// Complex nested schemas
const ComplexToolSchema = z.object({
    query: z.string(),
    filters: z.object({  // Nested object
        tags: z.array(z.string()),  // Array type
        status: z.enum(['active', 'pending']),  // Enum
        score: z.number().min(0).max(100)  // Constraints
    }).optional()
});
```

## Decision Flow Diagram

```
User starts MCP creation
    ↓
Define tools (1-N)
    ↓
Define parameters for each tool
    ↓
Add resources? (optional)
    ↓
┌─────────────────────────────────┐
│  COMPLEXITY DETECTION           │
│  - Count tools                  │
│  - Check for OBJECT/ARRAY types │
│  - Count resources              │
└─────────────────────────────────┘
    ↓
┌─────────────────┬────────────────┬─────────────────┐
│   SIMPLE        │   MODERATE     │    COMPLEX      │
│  (≤5 tools,     │  (6-10 tools   │   (>10 tools)   │
│   basic types,  │   OR complex   │                 │
│   no resources) │   types)       │                 │
└─────────────────┴────────────────┴─────────────────┘
    ↓                ↓                    ↓
Skip advanced    Ask about:           Ask about:
prompts          - Dependencies       - Dependencies
                 - Mocks              - Mocks
                 - Env vars           - Env vars
    ↓                ↓                    ↓
Generate basic   Generate enhanced    Generate full
structure        structure            structure
```

## Examples

### SIMPLE MCP Example
```
Tools: 3
- send_email (to: string, subject: string, body: string)
- get_weather (location: string)
- calculate_tax (amount: number, rate: number)

Resources: 0
Complex types: None

Result: SIMPLE
- No dependency prompts
- No mock generation
- Basic structure only
```

### MODERATE MCP Example
```
Tools: 4
- search_products (filters: object {category, price_range})
- get_recommendations (user_id: string, preferences: array)
- update_inventory (items: array)
- generate_report (options: object)

Resources: 1
Complex types: Objects and arrays

Result: MODERATE
- Prompts for dependencies
- Offers mock support
- Enhanced structure
```

### COMPLEX MCP Example
```
Tools: 12
- Multiple tools with nested objects
- Arrays of objects
- Enums with constraints
- Number ranges

Resources: 3
Complex types: Many

Result: COMPLEX
- Full feature set
- All advanced options
- Complete scaffolding
```

## Key Insight

The complexity detection is **smart but conservative**:
- Even 1 complex parameter type (object/array) bumps you to MODERATE
- This ensures users get helpful features like mocks when they might need them
- Resources automatically exclude SIMPLE classification
- The system errs on the side of providing more features rather than less
