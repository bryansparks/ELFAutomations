# N8N Workflow Import/Export System

## Overview

The N8N Workflow Import/Export system provides comprehensive capabilities for managing workflows across different environments. It supports multiple formats, validation, processing, and seamless integration with the ELF Automations platform.

## Features

### Import Capabilities

- **Multiple Sources**: Import from JSON, files, or URLs
- **Validation**: Comprehensive security, compatibility, and performance checks
- **Processing**: Automatic credential sanitization and environment adaptation
- **Auto-Fix**: Optional automatic fixing of common issues
- **AI Enhancement**: Uses AI to improve workflow documentation and suggest optimizations

### Export Capabilities

- **Multiple Formats**: JSON, YAML, Markdown documentation, ZIP archives
- **Metadata Inclusion**: Optional workflow metadata and history
- **Credential Sanitization**: Removes sensitive data for safe sharing
- **Batch Operations**: Export multiple workflows based on criteria
- **Version History**: Include all workflow versions in archives

## Architecture

### Components

1. **WorkflowImporter** (`workflow_importer.py`)
   - Handles all import operations
   - Validates and processes workflows
   - Stores in unified registry

2. **WorkflowExporter** (`workflow_exporter.py`)
   - Manages export operations
   - Supports multiple formats
   - Handles batch exports

3. **WorkflowValidator** (`workflow_validator.py`)
   - Comprehensive validation engine
   - Security scanning
   - Compatibility checking
   - Performance analysis

4. **N8NClient** (`client.py`)
   - High-level API for teams
   - Integrates all components
   - Async operations

### Database Schema

The system uses a unified workflow registry with:
- Main workflows table
- Version control
- Metadata storage
- Import/export audit logs
- Validation history

## Usage

### Import Workflow

```python
from elf_automations.shared.n8n import N8NClient

client = N8NClient()

# Import from JSON
result = await client.import_workflow(
    source='{"name": "My Workflow", "nodes": [...]}',
    source_type="json",
    owner_team="marketing",
    category="automation",
    validate=True,
    process=True,
    auto_fix=True
)

# Import from file
result = await client.import_workflow(
    source="/path/to/workflow.json",
    source_type="file",
    owner_team="sales"
)

# Import from URL
result = await client.import_workflow(
    source="https://example.com/workflow.json",
    source_type="url",
    owner_team="engineering"
)
```

### Export Workflow

```python
# Export as JSON with metadata
export_data = client.export_workflow(
    workflow_id="workflow_123",
    include_metadata=True
)

# Export to file
path = client.export_to_file(
    workflow_id="workflow_123",
    output_path="exports/my_workflow.json"
)

# Export as archive with versions
content, filename = await client.exporter.export_workflow(
    workflow_id="workflow_123",
    format="archive",
    include_versions=True
)
```

### Validation

```python
# Validate before import
validation_result = client.validate_workflow(
    workflow_json=workflow_data,
    owner_team="qa-team",
    check_permissions=True,
    deep_validation=True
)

if validation_result["status"] == "passed":
    # Safe to import
    pass
```

## Control Center UI

### Import Dialog

The Control Center provides a user-friendly import dialog with:
- Drag & drop file upload
- JSON paste area
- URL import
- Real-time validation feedback
- Import options (validate, process, auto-fix)

### Export Options

Each workflow in the UI has export capabilities:
- Download button for quick JSON export
- Format selection (JSON, YAML, Markdown, Archive)
- Batch export from workflow list

## Validation Rules

### Security Checks
- No hardcoded credentials
- HTTPS URLs only (with exceptions for localhost)
- Webhook authentication required
- No exposed secrets in parameters

### Compatibility Checks
- Node availability verification
- Credential mapping validation
- Environment variable requirements
- Webhook URL compatibility

### Performance Analysis
- Execution time estimates
- Resource usage predictions
- Cost per execution calculation
- Complexity scoring

## Best Practices

### For Import

1. **Always Validate**: Run validation before importing
2. **Use Processing**: Enable processing for environment compatibility
3. **Review Credentials**: Map required credentials after import
4. **Test First**: Import to development environment first
5. **Document Changes**: Add descriptions to imported workflows

### For Export

1. **Sanitize Always**: Enable credential sanitization
2. **Include Metadata**: Helps with reimport and documentation
3. **Use Archives**: For complete workflow backup with history
4. **Version Control**: Export before major changes
5. **Share Safely**: Use markdown format for documentation

## API Endpoints

### Import Endpoint
```
POST /api/workflows/import
{
  "source": "...",
  "sourceType": "json|file|url",
  "ownerTeam": "team-name",
  "category": "category",
  "validate": true,
  "process": true,
  "autoFix": false
}
```

### Export Endpoint
```
GET /api/workflows/export?workflowId=xxx&format=json&includeMetadata=true
```

## Error Handling

The system provides detailed error information:

```json
{
  "success": false,
  "error": "Import failed",
  "validationReport": {
    "status": "failed",
    "errors": [
      {
        "field": "security",
        "message": "Found hardcoded api_key in workflow",
        "severity": "critical",
        "suggestion": "Remove hardcoded api_key and use n8n credentials instead"
      }
    ],
    "warnings": [...],
    "suggestions": [...]
  }
}
```

## Future Enhancements

1. **Template Library Integration**: Import from curated templates
2. **Workflow Marketplace**: Share workflows with the community
3. **Version Diff**: Compare workflow versions before import
4. **Bulk Processing**: Import multiple workflows from archives
5. **CI/CD Integration**: Automated import/export in pipelines
