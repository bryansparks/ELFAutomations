import { NextResponse } from 'next/server';
import { getServerSupabase } from '@/lib/supabase';

export async function GET() {
  try {
    const supabase = getServerSupabase();

    // Fetch real data from Supabase
    const [
      teamsResult,
      workflowsResult,
      costResult
    ] = await Promise.all([
      supabase.from('teams').select('*'),
      supabase.from('workflows').select('*'),
      supabase.from('api_usage').select('*').order('created_at', { ascending: false }).limit(100)
    ]);

    // Calculate system metrics
    const activeTeams = teamsResult.data?.filter(t => t.status === 'active').length || 0;
    const totalTeams = teamsResult.data?.length || 0;
    const activeWorkflows = workflowsResult.data?.filter(w => w.status === 'active').length || 0;

    // Calculate today's costs
    const today = new Date().toISOString().split('T')[0];
    const todaysCosts = costResult.data?.filter(c =>
      c.created_at?.startsWith(today)
    ) || [];
    const todayTotal = todaysCosts.reduce((sum, c) => sum + (c.cost || 0), 0);

    // Calculate monthly costs
    const thisMonth = new Date().toISOString().substring(0, 7); // YYYY-MM
    const monthlyCosts = costResult.data?.filter(c =>
      c.created_at?.startsWith(thisMonth)
    ) || [];
    const monthTotal = monthlyCosts.reduce((sum, c) => sum + (c.cost || 0), 0);

    // Group costs by team for top teams
    const costsByTeam = {};
    costResult.data?.forEach(cost => {
      const team = cost.team_name || 'unknown';
      if (!costsByTeam[team]) {
        costsByTeam[team] = { total_cost: 0, request_count: 0 };
      }
      costsByTeam[team].total_cost += cost.cost || 0;
      costsByTeam[team].request_count += 1;
    });

    const topTeams = Object.entries(costsByTeam)
      .map(([team_name, data]) => ({ team_name, ...data }))
      .sort((a, b) => b.total_cost - a.total_cost)
      .slice(0, 5);

    // Group costs by model
    const costsByModel = {};
    costResult.data?.forEach(cost => {
      const model = cost.model_name || 'unknown';
      costsByModel[model] = (costsByModel[model] || 0) + (cost.cost || 0);
    });

    const dashboardData = {
      system_status: {
        status: activeTeams > 0 ? "operational" : "starting",
        health_score: Math.min(100, Math.max(0, 70 + (activeTeams * 5) + (activeWorkflows * 2))),
        active_teams: activeTeams,
        total_teams: totalTeams,
        active_workflows: activeWorkflows,
        system_load: Math.random() * 50 + 25, // Mock system load
        api_availability: {
          supabase: !!teamsResult.data,
          openai: true, // Could check API status
          anthropic: true,
          n8n: true
        },
        last_updated: new Date().toISOString()
      },
      teams: teamsResult.data?.map(team => ({
        id: team.id,
        name: team.name,
        display_name: team.display_name || team.name,
        department: team.department || 'general',
        placement: team.placement || team.name,
        status: team.status,
        framework: team.framework || 'crewai',
        llm_provider: team.llm_provider || 'openai',
        llm_model: team.llm_model || 'gpt-4',
        member_count: team.member_count || 3,
        is_manager: team.is_manager || false,
        reports_to: team.reports_to,
        subordinate_teams: team.subordinate_teams || []
      })) || [],
      cost_metrics: {
        today_cost: todayTotal,
        today_budget: 100, // Could be configurable
        today_percentage: (todayTotal / 100) * 100,
        month_cost: monthTotal,
        month_budget: 3000, // Could be configurable
        trend: todayTotal > (monthTotal / 30) ? "up" : "down",
        top_teams: topTeams,
        cost_by_model: costsByModel,
        hourly_costs: Array.from({ length: 24 }, (_, i) => ({
          hour: i,
          cost: todaysCosts.filter(c =>
            new Date(c.created_at).getHours() === i
          ).reduce((sum, c) => sum + (c.cost || 0), 0)
        }))
      },
      workflows: workflowsResult.data?.map(workflow => ({
        id: workflow.id,
        name: workflow.name,
        status: workflow.status,
        executions_today: 0, // Would need execution tracking
        success_rate: 95, // Mock - would need execution history
        avg_duration: 10, // Mock
        last_run: workflow.updated_at
      })) || [],
      communication_volume: {
        total_messages: 0, // Would need A2A message tracking
        a2a_messages: 0,
        internal_messages: 0,
        messages_by_team: {}
      },
      activity_feed: [] // Would need activity tracking
    };

    return NextResponse.json(dashboardData);
  } catch (error) {
    console.error('Dashboard API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch dashboard data' },
      { status: 500 }
    );
  }
}
