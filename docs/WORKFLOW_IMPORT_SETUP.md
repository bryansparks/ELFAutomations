# Workflow Import Setup Guide

## Current Status
The workflow import functionality is fully implemented but the database tables don't exist yet. This is causing the error code `42P01` (undefined_table).

## Quick Setup Steps

### 1. Create the Database Tables
Run the following SQL in your Supabase dashboard:
```sql
-- File: /sql/create_workflows_tables_only.sql
-- This creates the workflows and workflow_versions tables
```

Navigate to:
1. Supabase Dashboard → SQL Editor
2. Paste the contents of `/sql/create_workflows_tables_only.sql`
3. Click "Run"

### 2. Verify Tables Created
In Supabase Dashboard:
1. Go to Table Editor
2. You should see:
   - `workflows` table
   - `workflow_versions` table

### 3. Test the Import
In the Control Center UI (http://localhost:3003):
1. Go to Workflows page
2. Click "Import" button
3. Use "Load Demo" button to fill with valid JSON
4. Click "Import Workflow"

Alternatively, run the test script:
```bash
cd /Users/bryansparks/projects/ELFAutomations
node scripts/test_workflow_import.js
```

## What the Import Does

1. **Accepts workflow from**:
   - JSON text (paste directly)
   - File upload (.json files)
   - URL (fetches from remote)

2. **Creates workflow record** with:
   - Unique workflow_id
   - Name and description
   - Owner team assignment
   - Category tagging
   - Node type analysis
   - Complexity scoring

3. **Creates version record** with:
   - Full workflow JSON
   - Version numbering
   - Validation status

4. **Returns validation report** with:
   - Status (passed/warnings/failed)
   - Errors, warnings, suggestions

## Troubleshooting

### "Workflows table does not exist"
- Run the SQL script in step 1
- Make sure you're in the correct Supabase project

### "Invalid JSON format"
- Use the "Load Demo" button for valid JSON
- Ensure JSON is properly formatted
- Don't include extra text around the JSON

### "HTTP error! status: 500"
- Check that .env.local symlink exists
- Verify Supabase credentials are correct
- Check server logs for details

## Next Steps

Once tables are created and import works:
1. Test importing real N8N workflows
2. Implement workflow execution
3. Add workflow versioning UI
4. Build workflow marketplace features
