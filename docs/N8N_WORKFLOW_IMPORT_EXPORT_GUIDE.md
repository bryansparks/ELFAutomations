# N8N Workflow Import/Export and Validation System

## Overview

The N8N Workflow Import/Export system provides comprehensive workflow management capabilities including:
- Import workflows from N8N exports
- Export workflows in various formats
- Version control for workflows
- Comprehensive validation (security, performance, best practices)
- Template management
- Sync with N8N instances

## Architecture

### Database Schema

The unified workflow registry uses PostgreSQL with the following main tables:
- `workflow_registry` - Main workflow storage with full JSON and metadata
- `workflow_versions` - Version history for each workflow
- `workflow_executions` - Execution tracking
- `workflow_templates` - Reusable workflow templates
- `workflow_validation_log` - Validation history
- `workflow_import_export_log` - Import/export audit trail

### Components

1. **WorkflowImporter** (`workflow_importer.py`)
   - Imports workflows from JSON files or strings
   - Validates structure before import
   - Extracts metadata automatically
   - Creates version history

2. **WorkflowExporter** (`workflow_exporter.py`)
   - Exports workflows to various formats
   - Supports versioned exports
   - Bulk export to archives
   - Template creation from workflows

3. **WorkflowValidator** (`workflow_validator.py`)
   - Schema validation
   - Security checks (hardcoded secrets, credentials)
   - Performance analysis
   - Best practices validation
   - Team permission checks

4. **N8NClient** (`client.py`)
   - Unified interface for all operations
   - Async support for N8N sync
   - Integration with existing workflow execution

## Setup

### 1. Database Setup

Run the setup script to create the schema and migrate existing data:

```bash
cd scripts
python setup_unified_workflow_registry.py
```

This will:
- Create all necessary tables and indexes
- Optionally migrate data from existing workflow tables
- Set up views for analytics

### 2. Environment Configuration

Ensure your `.env` file has:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DATABASE_URL=your_database_url  # For direct PostgreSQL access
N8N_URL=http://n8n.n8n.svc.cluster.local:5678  # Your N8N instance
N8N_API_KEY=your_n8n_api_key  # Optional
```

## Usage

### Command Line Interface

The `n8n_workflow_manager.py` script provides full CLI access:

#### Import Workflow
```bash
# Import from file
python scripts/n8n_workflow_manager.py import workflow.json \
  --category customer-onboarding \
  --team marketing-team \
  --description "Handles new customer signups" \
  --tags onboarding email \
  --validate

# Import sample workflow
python scripts/n8n_workflow_manager.py import examples/sample_n8n_workflow.json \
  --category customer-onboarding \
  --team marketing-team
```

#### Export Workflow
```bash
# Export by name
python scripts/n8n_workflow_manager.py export "Customer Onboarding" \
  --output customer_onboarding_backup.json

# Export by ID with specific version
python scripts/n8n_workflow_manager.py export 123e4567-e89b-12d3-a456-426614174000 \
  --version 3 \
  --output workflow_v3.json

# Export without metadata (just N8N format)
python scripts/n8n_workflow_manager.py export my-workflow \
  --no-metadata
```

#### Validate Workflow
```bash
# Validate from file
python scripts/n8n_workflow_manager.py validate workflow.json \
  --deep \
  --team marketing-team

# Validate existing workflow
python scripts/n8n_workflow_manager.py validate "Customer Onboarding" --deep
```

#### Sync with N8N
```bash
# Sync all active workflows
python scripts/n8n_workflow_manager.py sync

# Sync specific workflows
python scripts/n8n_workflow_manager.py sync \
  --workflows id1 id2 id3

# Sync everything
python scripts/n8n_workflow_manager.py sync --all
```

### Python API

```python
from elf_automations.shared.n8n import N8NClient

client = N8NClient()

# Import workflow
workflow = client.import_from_file(
    "workflow.json",
    category="customer_onboarding",
    owner_team="marketing-team",
    imported_by="john.doe"
)

# Validate workflow
validation_result = client.validate_workflow(
    workflow_json=workflow["n8n_workflow_json"],
    owner_team="marketing-team",
    deep_validation=True
)

# Export workflow
export_data = client.export_workflow(
    workflow_slug="customer-onboarding",
    include_metadata=True
)

# Export to file
output_path = client.export_to_file(
    workflow_slug="customer-onboarding",
    output_path="backup.json"
)
```

### Async Operations

```python
import asyncio

async def sync_workflows():
    async with N8NClient() as client:
        results = await client.sync_with_n8n(sync_all=True)
        print(f"Synced: {len(results['synced'])} workflows")

asyncio.run(sync_workflows())
```

## Validation

### Validation Checks

The validator performs comprehensive checks:

1. **Structure Validation**
   - Required fields (nodes, connections)
   - Valid JSON structure
   - Node name uniqueness

2. **Security Validation**
   - Hardcoded API keys/passwords
   - Exposed credentials
   - Insecure HTTP connections
   - Credential configuration

3. **Performance Validation**
   - Complexity score calculation
   - Execution time estimation
   - Cost per run estimation
   - AI node usage

4. **Best Practices**
   - Meaningful node names
   - Error handling presence
   - Logging for complex workflows
   - Workflow documentation

### Validation Results

Validation returns detailed results:
```json
{
  "status": "warning",
  "errors": [],
  "warnings": [
    {
      "code": "NODE_007",
      "message": "Workflow has no trigger node",
      "severity": "warning"
    }
  ],
  "security_issues": [],
  "metrics": {
    "node_count": 7,
    "complexity_score": 12.5,
    "estimated_execution_time": 4.2,
    "estimated_cost_per_run": 0.0123
  }
}
```

## Workflow Lifecycle

### States
- `imported` - Just imported, not validated
- `validating` - Currently being validated
- `validated` - Passed validation
- `testing` - Under test
- `approved` - Approved for deployment
- `deployed` - Active in N8N
- `running` - Executable
- `paused` - Temporarily disabled
- `deprecated` - Phased out
- `archived` - No longer active

### Version Management

Every change creates a new version:
```python
# Update workflow
updated = client.importer.update_workflow(
    workflow_id="workflow-id",
    workflow_json=new_json,
    change_summary="Added error handling",
    changed_by="john.doe"
)
```

## Templates

### Create Template from Workflow
```python
template = client.exporter.export_as_template(
    workflow_id="workflow-id",
    template_name="Customer Onboarding Template",
    parameters={
        "webhook_path": {
            "type": "string",
            "default": "/customer",
            "description": "Webhook endpoint path"
        }
    }
)
```

### Use Template
```python
workflow = client.importer.create_workflow_from_template(
    template_id="template-id",
    name="New Customer Workflow",
    parameters={"webhook_path": "/new-customer"},
    owner_team="sales-team"
)
```

## Best Practices

1. **Always Validate Before Deployment**
   ```bash
   python scripts/n8n_workflow_manager.py import workflow.json --validate
   ```

2. **Use Meaningful Names and Descriptions**
   - Workflow names should be descriptive
   - Add descriptions explaining the purpose
   - Use tags for categorization

3. **Version Control Integration**
   - Export workflows to Git for version control
   - Use the metadata format for full tracking
   - Create branches for workflow changes

4. **Security**
   - Never hardcode credentials in workflows
   - Use N8N's credential system
   - Run security validation regularly

5. **Performance**
   - Monitor complexity scores
   - Optimize workflows with many AI nodes
   - Use parallel execution where possible

## Troubleshooting

### Common Issues

1. **Import Fails with Validation Errors**
   - Check the workflow JSON structure
   - Ensure all node types are valid
   - Verify connections reference existing nodes

2. **Export Shows Empty Workflow**
   - Workflow may not have been synced from N8N
   - Run sync command first
   - Check if workflow has n8n_workflow_json populated

3. **Sync Fails**
   - Verify N8N_URL and N8N_API_KEY
   - Check network connectivity to N8N
   - Ensure workflow has n8n_workflow_id

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration from Old System

If you have workflows in the old registry:

1. Run the migration script:
   ```bash
   python scripts/setup_unified_workflow_registry.py
   ```

2. Sync with N8N to populate workflow JSON:
   ```bash
   python scripts/n8n_workflow_manager.py sync --all
   ```

3. Validate all workflows:
   ```bash
   for workflow in $(python scripts/n8n_workflow_manager.py list | grep "✓" | cut -d' ' -f2); do
     python scripts/n8n_workflow_manager.py validate "$workflow"
   done
   ```

## API Reference

### WorkflowImporter
- `import_workflow()` - Import single workflow
- `import_from_file()` - Import from JSON file
- `import_batch()` - Import multiple workflows
- `update_workflow()` - Create new version

### WorkflowExporter
- `export_workflow()` - Export single workflow
- `export_to_file()` - Export to JSON file
- `export_batch()` - Export multiple workflows
- `export_to_archive()` - Create ZIP archive
- `export_as_template()` - Create template

### WorkflowValidator
- `validate_workflow()` - Comprehensive validation
- `validate_and_store()` - Validate and save results

## Future Enhancements

1. **Parameterized Templates**
   - Full template parameter substitution
   - Template inheritance
   - Template marketplace

2. **Advanced Validation**
   - Custom validation rules
   - Team-specific requirements
   - Compliance checks

3. **Workflow Testing**
   - Automated test execution
   - Test data generation
   - Performance benchmarking

4. **GitOps Integration**
   - Automatic Git commits on changes
   - PR-based workflow approval
   - Rollback capabilities
