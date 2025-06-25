import { NextRequest, NextResponse } from 'next/server';
import { getServerSupabase } from '@/lib/supabase';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = getServerSupabase();
    const { id } = params;

    // Get the workflow
    const { data: workflow, error: workflowError } = await supabase
      .from('workflows')
      .select('*')
      .eq('id', id)
      .single();

    if (workflowError || !workflow) {
      return NextResponse.json(
        { error: 'Workflow not found' },
        { status: 404 }
      );
    }

    // Get the current version
    const { data: version, error: versionError } = await supabase
      .from('workflow_versions')
      .select('workflow_json')
      .eq('workflow_id', id)
      .eq('is_current', true)
      .single();

    if (versionError || !version) {
      // Fallback to first version if no current version marked
      const { data: firstVersion } = await supabase
        .from('workflow_versions')
        .select('workflow_json')
        .eq('workflow_id', id)
        .order('version_number', { ascending: true })
        .limit(1)
        .single();

      if (!firstVersion) {
        return NextResponse.json(
          { error: 'No workflow version found' },
          { status: 404 }
        );
      }

      version.workflow_json = firstVersion.workflow_json;
    }

    // Return the workflow JSON with metadata
    const exportData = {
      ...version.workflow_json,
      _metadata: {
        exported_at: new Date().toISOString(),
        workflow_id: workflow.workflow_id,
        name: workflow.name,
        description: workflow.description,
        category: workflow.category,
        tags: workflow.tags,
        owner_team: workflow.owner_team,
        elf_automations_version: '1.0.0'
      }
    };

    // Set appropriate headers for file download
    const headers = new Headers();
    headers.set('Content-Type', 'application/json');
    headers.set('Content-Disposition', `attachment; filename="${workflow.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_workflow.json"`);

    return new NextResponse(
      JSON.stringify(exportData, null, 2),
      { headers }
    );

  } catch (error) {
    console.error('Error exporting workflow:', error);
    return NextResponse.json(
      { error: 'Failed to export workflow' },
      { status: 500 }
    );
  }
}
