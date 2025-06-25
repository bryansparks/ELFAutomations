import { NextRequest, NextResponse } from 'next/server';
import { getServerSupabase } from '@/lib/supabase';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const workflowId = searchParams.get('workflowId');
    const format = searchParams.get('format') || 'json';
    const includeMetadata = searchParams.get('includeMetadata') === 'true';

    if (!workflowId) {
      return NextResponse.json({ error: 'Workflow ID is required' }, { status: 400 });
    }

    const supabase = getServerSupabase();

    // Fetch workflow and its current version
    const [workflowResult, versionResult] = await Promise.all([
      supabase
        .from('workflows')
        .select('*')
        .eq('workflow_id', workflowId)
        .single(),
      supabase
        .from('workflow_versions')
        .select('*')
        .eq('workflow_id', workflowId)
        .eq('is_current', true)
        .single()
    ]);

    if (workflowResult.error || !workflowResult.data) {
      return NextResponse.json({ error: 'Workflow not found' }, { status: 404 });
    }

    const workflow = workflowResult.data;
    const version = versionResult.data;

    // Get the workflow JSON
    const workflowJson = version?.workflow_json || version?.processed_json || {};

    let exportData: any;
    let filename: string;
    let contentType: string;

    if (format === 'json') {
      exportData = includeMetadata ? {
        workflow: workflowJson,
        metadata: {
          exported_at: new Date().toISOString(),
          exported_from: 'elf-control-center',
          workflow_id: workflow.workflow_id,
          name: workflow.name,
          description: workflow.description,
          category: workflow.category,
          tags: workflow.tags,
          complexity_score: workflow.complexity_score,
          integrations: workflow.integrations
        }
      } : workflowJson;

      filename = `${workflow.workflow_id}_export.json`;
      contentType = 'application/json';
    } else {
      // For other formats, just return JSON for now
      exportData = workflowJson;
      filename = `${workflow.workflow_id}_export.json`;
      contentType = 'application/json';
    }

    const response = new NextResponse(JSON.stringify(exportData, null, 2));
    response.headers.set('Content-Type', contentType);
    response.headers.set('Content-Disposition', `attachment; filename="${filename}"`);

    return response;

  } catch (error) {
    console.error('Error exporting workflow:', error);
    return NextResponse.json(
      {
        error: 'Failed to export workflow',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
