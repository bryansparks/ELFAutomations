import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { BaseMCPServer } from '../../shared/base-server.js';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Schema definitions for team registry operations
const RegisterTeamSchema = z.object({
  name: z.string().describe('Team name (e.g., marketing-team)'),
  display_name: z.string().describe('Display name (e.g., Marketing Team)'),
  department: z.string().describe('Department (e.g., marketing)'),
  placement: z.string().describe('Organizational placement (e.g., marketing.brand)'),
  purpose: z.string().describe('Team purpose/description'),
  framework: z.enum(['CrewAI', 'LangGraph']).describe('Framework used'),
  llm_provider: z.enum(['OpenAI', 'Anthropic']).describe('LLM provider'),
  llm_model: z.string().describe('LLM model name'),
  reports_to: z.string().optional().describe('Who this team reports to'),
});

const AddTeamMemberSchema = z.object({
  team_name: z.string().describe('Team name'),
  role: z.string().describe('Member role (e.g., Marketing Manager)'),
  is_manager: z.boolean().describe('Is this member the team manager?'),
  responsibilities: z.array(z.string()).describe('List of responsibilities'),
  skills: z.array(z.string()).describe('List of skills'),
  system_prompt: z.string().describe('Agent system prompt'),
});

const QueryTeamSchema = z.object({
  team_name: z.string().optional().describe('Team name to query'),
  department: z.string().optional().describe('Department to filter by'),
  executive_role: z.string().optional().describe('Executive role to find teams for'),
});

const UpdateTeamRelationshipSchema = z.object({
  child_team: z.string().describe('Child team name'),
  parent_entity: z.string().describe('Parent entity name (team or executive)'),
  entity_type: z.enum(['team', 'executive']).describe('Type of parent entity'),
  relationship_type: z.enum(['reports_to', 'collaborates_with']).default('reports_to'),
});

export class TeamRegistryMCPServer extends BaseMCPServer {
  private supabase: SupabaseClient;

  constructor() {
    super('team-registry-mcp-server', '1.0.0');

    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
      throw new Error('SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required');
    }

    this.supabase = createClient(supabaseUrl, supabaseKey);
  }

  protected getTools(): Tool[] {
    return [
      this.createTool(
        'register_team',
        'Register a new team in the team registry',
        RegisterTeamSchema
      ),
      this.createTool(
        'add_team_member',
        'Add a member to an existing team',
        AddTeamMemberSchema
      ),
      this.createTool(
        'query_teams',
        'Query teams by various criteria',
        QueryTeamSchema
      ),
      this.createTool(
        'get_team_hierarchy',
        'Get the complete team hierarchy',
        z.object({})
      ),
      this.createTool(
        'get_executive_teams',
        'Get all teams managed by an executive',
        z.object({
          executive_role: z.string().describe('Executive role (e.g., Chief Marketing Officer)'),
        })
      ),
      this.createTool(
        'update_team_relationship',
        'Update team reporting relationships',
        UpdateTeamRelationshipSchema
      ),
      this.createTool(
        'get_team_members',
        'Get all members of a team',
        z.object({
          team_name: z.string().describe('Team name'),
        })
      ),
      this.createTool(
        'get_team_composition',
        'Get team composition summary',
        z.object({})
      ),
    ];
  }

  protected async handleToolCall(name: string, args: any): Promise<any> {
    try {
      switch (name) {
        case 'register_team':
          return await this.registerTeam(args);
        case 'add_team_member':
          return await this.addTeamMember(args);
        case 'query_teams':
          return await this.queryTeams(args);
        case 'get_team_hierarchy':
          return await this.getTeamHierarchy();
        case 'get_executive_teams':
          return await this.getExecutiveTeams(args);
        case 'update_team_relationship':
          return await this.updateTeamRelationship(args);
        case 'get_team_members':
          return await this.getTeamMembers(args);
        case 'get_team_composition':
          return await this.getTeamComposition();
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }

  private async registerTeam(args: any) {
    const params = this.validateInput(RegisterTeamSchema, args);

    // Call the register_team function in Supabase
    const { data, error } = await this.supabase.rpc('register_team', {
      p_team_name: params.name,
      p_display_name: params.display_name,
      p_department: params.department,
      p_placement: params.placement,
      p_purpose: params.purpose,
      p_framework: params.framework,
      p_llm_provider: params.llm_provider,
      p_llm_model: params.llm_model,
      p_reports_to: params.reports_to || null,
    });

    if (error) {
      throw new Error(`Failed to register team: ${error.message}`);
    }

    return this.createSuccessResponse({
      message: `Team '${params.name}' registered successfully`,
      team_id: data,
    });
  }

  private async addTeamMember(args: any) {
    const params = this.validateInput(AddTeamMemberSchema, args);

    // First get the team ID
    const { data: team, error: teamError } = await this.supabase
      .from('teams')
      .select('id')
      .eq('name', params.team_name)
      .single();

    if (teamError || !team) {
      throw new Error(`Team '${params.team_name}' not found`);
    }

    // Add the team member
    const { error } = await this.supabase
      .from('team_members')
      .insert({
        team_id: team.id,
        role: params.role,
        is_manager: params.is_manager,
        responsibilities: params.responsibilities,
        skills: params.skills,
        system_prompt: params.system_prompt,
      });

    if (error) {
      throw new Error(`Failed to add team member: ${error.message}`);
    }

    return this.createSuccessResponse({
      message: `Added '${params.role}' to team '${params.team_name}'`,
    });
  }

  private async queryTeams(args: any) {
    const params = this.validateInput(QueryTeamSchema, args);

    let query = this.supabase.from('teams').select('*');

    if (params.team_name) {
      query = query.eq('name', params.team_name);
    }
    if (params.department) {
      query = query.eq('department', params.department);
    }
    if (params.executive_role) {
      // Join with executive_management table
      const { data: managedTeams, error: mgmtError } = await this.supabase
        .from('executive_management')
        .select('managed_team_id')
        .eq('executive_role', params.executive_role);

      if (mgmtError) {
        throw new Error(`Failed to query executive teams: ${mgmtError.message}`);
      }

      const teamIds = managedTeams?.map(t => t.managed_team_id) || [];
      query = query.in('id', teamIds);
    }

    const { data, error } = await query;

    if (error) {
      throw new Error(`Failed to query teams: ${error.message}`);
    }

    return this.createSuccessResponse(data || []);
  }

  private async getTeamHierarchy() {
    const { data, error } = await this.supabase
      .from('team_hierarchy')
      .select('*')
      .order('department', { ascending: true })
      .order('team_name', { ascending: true });

    if (error) {
      throw new Error(`Failed to get team hierarchy: ${error.message}`);
    }

    return this.createSuccessResponse(data || []);
  }

  private async getExecutiveTeams(args: any) {
    const { executive_role } = this.validateInput(
      z.object({
        executive_role: z.string(),
      }),
      args
    );

    const { data, error } = await this.supabase.rpc('get_executive_teams', {
      exec_role: executive_role,
    });

    if (error) {
      throw new Error(`Failed to get executive teams: ${error.message}`);
    }

    return this.createSuccessResponse(data || []);
  }

  private async updateTeamRelationship(args: any) {
    const params = this.validateInput(UpdateTeamRelationshipSchema, args);

    // Get child team ID
    const { data: childTeam, error: childError } = await this.supabase
      .from('teams')
      .select('id')
      .eq('name', params.child_team)
      .single();

    if (childError || !childTeam) {
      throw new Error(`Child team '${params.child_team}' not found`);
    }

    // Insert or update relationship
    const { error } = await this.supabase
      .from('team_relationships')
      .upsert({
        child_team_id: childTeam.id,
        parent_entity_type: params.entity_type,
        parent_entity_name: params.parent_entity,
        relationship_type: params.relationship_type,
      });

    if (error) {
      throw new Error(`Failed to update relationship: ${error.message}`);
    }

    // If reporting to executive, update executive_management table
    if (params.entity_type === 'executive' && params.relationship_type === 'reports_to') {
      await this.supabase
        .from('executive_management')
        .upsert({
          executive_role: params.parent_entity,
          managed_team_id: childTeam.id,
        });
    }

    return this.createSuccessResponse({
      message: `Updated relationship: ${params.child_team} ${params.relationship_type} ${params.parent_entity}`,
    });
  }

  private async getTeamMembers(args: any) {
    const { team_name } = this.validateInput(
      z.object({
        team_name: z.string(),
      }),
      args
    );

    // Get team ID
    const { data: team, error: teamError } = await this.supabase
      .from('teams')
      .select('id')
      .eq('name', team_name)
      .single();

    if (teamError || !team) {
      throw new Error(`Team '${team_name}' not found`);
    }

    // Get team members
    const { data, error } = await this.supabase
      .from('team_members')
      .select('*')
      .eq('team_id', team.id)
      .order('is_manager', { ascending: false })
      .order('role', { ascending: true });

    if (error) {
      throw new Error(`Failed to get team members: ${error.message}`);
    }

    return this.createSuccessResponse(data || []);
  }

  private async getTeamComposition() {
    const { data, error } = await this.supabase
      .from('team_composition')
      .select('*')
      .order('department', { ascending: true })
      .order('team_name', { ascending: true });

    if (error) {
      throw new Error(`Failed to get team composition: ${error.message}`);
    }

    return this.createSuccessResponse(data || []);
  }
}

// Start the server
const server = new TeamRegistryMCPServer();
server.start().catch(console.error);
