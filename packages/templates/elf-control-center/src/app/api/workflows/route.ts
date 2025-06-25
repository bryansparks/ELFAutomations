import { NextResponse } from 'next/server';
import { getServerSupabase } from '@/lib/supabase';

export async function GET() {
  try {
    const supabase = getServerSupabase();

    // Fetch workflows from the unified registry
    const { data: workflows, error } = await supabase
      .from('workflows')
      .select(`
        id,
        workflow_id,
        name,
        description,
        category,
        status,
        owner_team,
        created_at,
        updated_at,
        estimated_cost_per_run,
        complexity_score
      `)
      .order('updated_at', { ascending: false });

    if (error) {
      console.error('Error fetching workflows:', error);
      return NextResponse.json(
        { error: 'Failed to fetch workflows' },
        { status: 500 }
      );
    }

    // Transform to match expected format
    const transformedWorkflows = workflows?.map(workflow => ({
      id: workflow.workflow_id || workflow.id,
      name: workflow.name,
      description: workflow.description,
      status: workflow.status,
      category: workflow.category,
      owner_team: workflow.owner_team,
      executions_today: 0, // Would need execution tracking
      success_rate: 95, // Mock - would need execution history
      avg_duration: 10 + (workflow.complexity_score || 0) * 2, // Estimate based on complexity
      last_run: workflow.updated_at,
      estimated_cost: workflow.estimated_cost_per_run || 0,
      complexity: workflow.complexity_score || 5
    })) || [];

    return NextResponse.json(transformedWorkflows);
  } catch (error) {
    console.error('Workflows API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch workflows' },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  const body = await request.json();

  // Mock workflow creation
  const newWorkflow = {
    id: `wf${Date.now()}`,
    name: body.name,
    description: body.description,
    status: "created",
    category: body.category,
    owner_team: body.team,
    created_at: new Date().toISOString()
  };

  return NextResponse.json({
    success: true,
    workflow: newWorkflow
  });
}
