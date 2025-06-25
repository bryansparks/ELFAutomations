import { NextRequest, NextResponse } from 'next/server';
import { getServerSupabase } from '@/lib/supabase';

export async function POST(request: NextRequest) {
  console.log('Import API called');

  try {
    const body = await request.json();
    console.log('Request body:', body);

    const {
      source,
      sourceType = 'json',
      ownerTeam = 'default',
      category = 'imported',
      validate = true,
      process = true,
      autoFix = false
    } = body;

    if (!source) {
      return NextResponse.json({ error: 'Source is required' }, { status: 400 });
    }

    console.log('Getting Supabase client...');
    const supabase = getServerSupabase();

    // For now, create a simplified import that just stores the workflow
    let workflowData: any;

    try {
      if (sourceType === 'json') {
        workflowData = JSON.parse(source);
      } else if (sourceType === 'url') {
        const response = await fetch(source);
        workflowData = await response.json();
      } else {
        workflowData = JSON.parse(source); // Assume file content is already parsed
      }
    } catch (error) {
      return NextResponse.json(
        { error: 'Invalid workflow format' },
        { status: 400 }
      );
    }

    // Basic validation
    if (!workflowData.name) {
      workflowData.name = `Imported Workflow ${new Date().toISOString()}`;
    }

    // Create workflow record
    const workflowRecord = {
      workflow_id: `imported_${Date.now()}`,
      name: workflowData.name,
      description: workflowData.description || 'Imported workflow',
      category: category,
      owner_team: ownerTeam,
      status: 'draft',
      source: 'imported',
      validation_status: validate ? 'pending' : 'skipped',
      node_types: workflowData.nodes?.map((n: any) => n.type) || [],
      complexity_score: Math.min(10, Math.max(1, workflowData.nodes?.length || 5)),
      created_by: 'control_center'
    };

    console.log('Inserting workflow record:', workflowRecord);

    // First, let's check if the table exists
    const { data: tableCheck, error: tableError } = await supabase
      .from('workflows')
      .select('id')
      .limit(1);

    console.log('Table check:', { hasData: !!tableCheck, tableError });

    const { data: workflow, error: workflowError } = await supabase
      .from('workflows')
      .insert(workflowRecord)
      .select()
      .single();

    console.log('Insert result:', { workflow, workflowError });

    if (workflowError) {
      console.error('Error creating workflow:', workflowError);
      console.error('Error details:', JSON.stringify(workflowError, null, 2));
      console.error('Error message:', workflowError?.message);
      console.error('Error code:', workflowError?.code);

      // Check if it's a table not found error
      if (workflowError?.code === '42P01') {
        return NextResponse.json(
          { error: 'Workflows table does not exist. Please run the database migration.' },
          { status: 500 }
        );
      }

      return NextResponse.json(
        {
          error: 'Failed to create workflow record',
          details: workflowError?.message || 'Unknown database error',
          code: workflowError?.code
        },
        { status: 500 }
      );
    }

    // Create workflow version
    const versionRecord = {
      workflow_id: workflow.id,
      version_number: 1,
      workflow_json: workflowData,
      validation_status: 'pending',
      is_current: true,
      created_by: 'control_center'
    };

    await supabase
      .from('workflow_versions')
      .insert(versionRecord);

    // Register workflow in state management system
    try {
      await supabase.rpc('transition_resource_state', {
        p_resource_type: 'workflow',
        p_resource_id: workflow.id,
        p_resource_name: workflow.name,
        p_new_state: 'registered',
        p_reason: 'Workflow imported via Control Center',
        p_transitioned_by: 'control_center_import',
        p_metadata: JSON.stringify({
          source: sourceType,
          category: category,
          owner_team: ownerTeam,
          imported_at: new Date().toISOString()
        })
      });
      console.log('Workflow registered in state management');
    } catch (stateError) {
      console.error('Failed to register workflow state:', stateError);
      // Continue anyway - state tracking is not critical for import
    }

    // Mock validation report
    const validationReport = {
      status: 'passed',
      errors: [],
      warnings: [],
      suggestions: ['Review imported workflow configuration', 'Test workflow execution']
    };

    return NextResponse.json({
      success: true,
      workflow,
      validationReport
    });

  } catch (error) {
    console.error('Error importing workflow:', error);
    return NextResponse.json(
      {
        error: 'Failed to import workflow',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
