#!/usr/bin/env node

/**
 * Project Management MCP Server V2
 *
 * Updated to use pm_ prefixed tables to avoid conflicts
 */

import { createClient } from '@supabase/supabase-js';
import { BaseServer } from '../shared/base-server';

interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
  priority: 'critical' | 'high' | 'medium' | 'low';
  created_by_team?: string;
  owner_team?: string;
  start_date?: string;
  target_end_date?: string;
  progress_percentage: number;
}

interface Task {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'ready' | 'in_progress' | 'blocked' | 'review' | 'completed' | 'cancelled';
  assigned_team?: string;
  priority: number;
  estimated_hours?: number;
  required_skills?: string[];
  due_date?: string;
  progress_percentage: number;
}

class ProjectManagementServer extends BaseServer {
  private supabase: any;

  constructor() {
    super('project-management', '2.0.0');

    // Initialize Supabase client
    const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
      throw new Error('Supabase credentials not found in environment variables');
    }

    this.supabase = createClient(supabaseUrl, supabaseKey);
    this.setupTools();
  }

  private setupTools() {
    // Project Management Tools
    this.addTool({
      name: 'create_project',
      description: 'Create a new project with automatic task breakdown',
      inputSchema: {
        type: 'object',
        properties: {
          name: { type: 'string', description: 'Project name' },
          description: { type: 'string', description: 'Project description' },
          priority: {
            type: 'string',
            enum: ['critical', 'high', 'medium', 'low'],
            description: 'Project priority'
          },
          owner_team: { type: 'string', description: 'Team ID that owns the project' },
          target_end_date: { type: 'string', description: 'Target completion date (YYYY-MM-DD)' }
        },
        required: ['name', 'priority']
      },
      handler: async (args) => this.createProject(args)
    });

    this.addTool({
      name: 'get_project_status',
      description: 'Get detailed status of a project including tasks and progress',
      inputSchema: {
        type: 'object',
        properties: {
          project_id: { type: 'string', description: 'Project ID' }
        },
        required: ['project_id']
      },
      handler: async (args) => this.getProjectStatus(args.project_id)
    });

    this.addTool({
      name: 'list_projects',
      description: 'List projects with optional filters',
      inputSchema: {
        type: 'object',
        properties: {
          status: { type: 'string', description: 'Filter by status' },
          owner_team: { type: 'string', description: 'Filter by owner team' },
          priority: { type: 'string', description: 'Filter by priority' }
        }
      },
      handler: async (args) => this.listProjects(args)
    });

    // Task Management Tools
    this.addTool({
      name: 'create_task',
      description: 'Create a new task within a project',
      inputSchema: {
        type: 'object',
        properties: {
          project_id: { type: 'string', description: 'Project ID' },
          title: { type: 'string', description: 'Task title' },
          description: { type: 'string', description: 'Task description' },
          task_type: {
            type: 'string',
            enum: ['development', 'design', 'analysis', 'testing', 'deployment', 'documentation', 'review']
          },
          assigned_team: { type: 'string', description: 'Team ID to assign to' },
          required_skills: {
            type: 'array',
            items: { type: 'string' },
            description: 'Skills required for this task'
          },
          estimated_hours: { type: 'number', description: 'Estimated hours to complete' },
          due_date: { type: 'string', description: 'Due date (YYYY-MM-DD)' }
        },
        required: ['project_id', 'title']
      },
      handler: async (args) => this.createTask(args)
    });

    this.addTool({
      name: 'update_task_status',
      description: 'Update the status of a task',
      inputSchema: {
        type: 'object',
        properties: {
          task_id: { type: 'string', description: 'Task ID' },
          status: {
            type: 'string',
            enum: ['pending', 'ready', 'in_progress', 'blocked', 'review', 'completed', 'cancelled']
          },
          notes: { type: 'string', description: 'Update notes' },
          progress_percentage: { type: 'number', description: 'Progress percentage (0-100)' },
          hours_worked: { type: 'number', description: 'Hours worked in this update' }
        },
        required: ['task_id', 'status']
      },
      handler: async (args) => this.updateTaskStatus(args)
    });

    this.addTool({
      name: 'assign_task',
      description: 'Assign or reassign a task to a team',
      inputSchema: {
        type: 'object',
        properties: {
          task_id: { type: 'string', description: 'Task ID' },
          team_id: { type: 'string', description: 'Team ID to assign to' },
          agent_role: { type: 'string', description: 'Specific agent role within team' }
        },
        required: ['task_id', 'team_id']
      },
      handler: async (args) => this.assignTask(args)
    });

    this.addTool({
      name: 'add_task_dependency',
      description: 'Add a dependency between tasks',
      inputSchema: {
        type: 'object',
        properties: {
          task_id: { type: 'string', description: 'Task that has the dependency' },
          depends_on_task_id: { type: 'string', description: 'Task that must complete first' },
          dependency_type: {
            type: 'string',
            enum: ['finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish'],
            default: 'finish_to_start'
          }
        },
        required: ['task_id', 'depends_on_task_id']
      },
      handler: async (args) => this.addTaskDependency(args)
    });

    this.addTool({
      name: 'list_team_tasks',
      description: 'List all tasks assigned to a team',
      inputSchema: {
        type: 'object',
        properties: {
          team_id: { type: 'string', description: 'Team ID' },
          status: { type: 'string', description: 'Filter by status' },
          include_completed: { type: 'boolean', default: false }
        },
        required: ['team_id']
      },
      handler: async (args) => this.listTeamTasks(args)
    });

    // Coordination Tools
    this.addTool({
      name: 'find_available_work',
      description: 'Find available tasks matching team skills',
      inputSchema: {
        type: 'object',
        properties: {
          team_id: { type: 'string', description: 'Team ID looking for work' },
          skills: {
            type: 'array',
            items: { type: 'string' },
            description: 'Team skills'
          },
          capacity_hours: { type: 'number', description: 'Available capacity in hours' }
        },
        required: ['team_id', 'skills']
      },
      handler: async (args) => this.findAvailableWork(args)
    });

    this.addTool({
      name: 'report_blocker',
      description: 'Report a blocker on a task',
      inputSchema: {
        type: 'object',
        properties: {
          task_id: { type: 'string', description: 'Task ID' },
          blocker_description: { type: 'string', description: 'Description of the blocker' },
          needs_help_from: { type: 'string', description: 'Team that might help resolve' }
        },
        required: ['task_id', 'blocker_description']
      },
      handler: async (args) => this.reportBlocker(args)
    });

    this.addTool({
      name: 'get_project_analytics',
      description: 'Get analytics and insights for a project',
      inputSchema: {
        type: 'object',
        properties: {
          project_id: { type: 'string', description: 'Project ID' }
        },
        required: ['project_id']
      },
      handler: async (args) => this.getProjectAnalytics(args.project_id)
    });
  }

  // Implementation methods - Updated to use pm_ prefixed tables

  private async createProject(args: any) {
    try {
      const project = {
        name: args.name,
        description: args.description,
        priority: args.priority || 'medium',
        status: 'planning',
        owner_team: args.owner_team,
        created_by_team: args.owner_team,
        target_end_date: args.target_end_date,
        progress_percentage: 0
      };

      const { data, error } = await this.supabase
        .from('pm_projects')  // Updated table name
        .insert(project)
        .select()
        .single();

      if (error) throw error;

      return {
        success: true,
        project: data,
        message: `Project '${args.name}' created successfully`
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async getProjectStatus(projectId: string) {
    try {
      // Get project details
      const { data: project, error: projectError } = await this.supabase
        .from('pm_project_dashboard')  // Updated view name
        .select('*')
        .eq('id', projectId)
        .single();

      if (projectError) throw projectError;

      // Get tasks
      const { data: tasks, error: tasksError } = await this.supabase
        .from('pm_tasks')  // Updated table name
        .select('*, assigned_team:teams(name)')
        .eq('project_id', projectId)
        .order('priority', { ascending: true });

      if (tasksError) throw tasksError;

      // Get team involvement
      const { data: teams, error: teamsError } = await this.supabase
        .from('pm_project_teams')  // Updated table name
        .select('*, team:teams(name)')
        .eq('project_id', projectId);

      if (teamsError) throw teamsError;

      return {
        success: true,
        project: project,
        tasks: tasks,
        teams: teams,
        summary: {
          total_tasks: project.total_tasks,
          completed_tasks: project.completed_tasks,
          blocked_tasks: project.blocked_tasks,
          progress_percentage: project.progress_percentage,
          health_status: project.health_status
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async createTask(args: any) {
    try {
      const task = {
        project_id: args.project_id,
        title: args.title,
        description: args.description,
        task_type: args.task_type || 'development',
        assigned_team: args.assigned_team,
        required_skills: args.required_skills,
        estimated_hours: args.estimated_hours,
        due_date: args.due_date,
        status: args.assigned_team ? 'ready' : 'pending',
        priority: args.priority || 3,
        progress_percentage: 0
      };

      const { data, error } = await this.supabase
        .from('pm_tasks')  // Updated table name
        .insert(task)
        .select()
        .single();

      if (error) throw error;

      return {
        success: true,
        task: data,
        message: `Task '${args.title}' created successfully`
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async updateTaskStatus(args: any) {
    try {
      // Update task
      const updates: any = {
        status: args.status,
        updated_at: new Date().toISOString()
      };

      if (args.progress_percentage !== undefined) {
        updates.progress_percentage = args.progress_percentage;
      }

      if (args.status === 'completed') {
        updates.completed_date = new Date().toISOString();
      } else if (args.status === 'in_progress' && !updates.start_date) {
        updates.start_date = new Date().toISOString();
      }

      const { data: task, error: taskError } = await this.supabase
        .from('pm_tasks')  // Updated table name
        .update(updates)
        .eq('id', args.task_id)
        .select()
        .single();

      if (taskError) throw taskError;

      // Create update record
      const updateRecord = {
        task_id: args.task_id,
        team_id: task.assigned_team,
        update_type: 'status_change',
        old_value: task.status,
        new_value: args.status,
        notes: args.notes,
        hours_worked: args.hours_worked || 0
      };

      await this.supabase
        .from('pm_task_updates')  // Updated table name
        .insert(updateRecord);

      return {
        success: true,
        task: task,
        message: `Task status updated to ${args.status}`
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async findAvailableWork(args: any) {
    try {
      // Get available tasks
      const { data: availableTasks, error } = await this.supabase
        .from('pm_available_tasks_for_assignment')  // Updated view name
        .select('*')
        .order('urgency', { ascending: true })
        .order('project_priority', { ascending: true });

      if (error) throw error;

      // Filter by skill match
      const matchingTasks = availableTasks.filter((task: any) => {
        if (!task.required_skills || task.required_skills.length === 0) {
          return true; // No specific skills required
        }

        // Check if team has required skills
        const teamSkills = new Set(args.skills);
        return task.required_skills.some((skill: string) => teamSkills.has(skill));
      });

      // Filter by capacity if provided
      const tasksWithinCapacity = args.capacity_hours
        ? matchingTasks.filter((task: any) =>
            !task.estimated_hours || task.estimated_hours <= args.capacity_hours)
        : matchingTasks;

      return {
        success: true,
        available_tasks: tasksWithinCapacity,
        total_found: tasksWithinCapacity.length,
        message: `Found ${tasksWithinCapacity.length} available tasks matching your skills`
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async listProjects(filters: any) {
    try {
      let query = this.supabase
        .from('pm_project_dashboard')  // Updated view name
        .select('*');

      if (filters.status) {
        query = query.eq('status', filters.status);
      }
      if (filters.owner_team) {
        query = query.eq('owner_team', filters.owner_team);
      }
      if (filters.priority) {
        query = query.eq('priority', filters.priority);
      }

      const { data, error } = await query
        .order('priority', { ascending: true })
        .order('created_at', { ascending: false });

      if (error) throw error;

      return {
        success: true,
        projects: data,
        count: data.length
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async assignTask(args: any) {
    try {
      const updates: any = {
        assigned_team: args.team_id,
        status: 'ready',
        updated_at: new Date().toISOString()
      };

      if (args.agent_role) {
        updates.assigned_agent = args.agent_role;
      }

      const { data, error } = await this.supabase
        .from('pm_tasks')  // Updated table name
        .update(updates)
        .eq('id', args.task_id)
        .select()
        .single();

      if (error) throw error;

      // Record assignment
      await this.supabase
        .from('pm_task_updates')  // Updated table name
        .insert({
          task_id: args.task_id,
          team_id: args.team_id,
          update_type: 'assignment_change',
          new_value: args.team_id,
          notes: `Task assigned to team ${args.team_id}`
        });

      return {
        success: true,
        task: data,
        message: `Task assigned to team ${args.team_id}`
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async addTaskDependency(args: any) {
    try {
      const dependency = {
        task_id: args.task_id,
        depends_on_task_id: args.depends_on_task_id,
        dependency_type: args.dependency_type || 'finish_to_start'
      };

      const { data, error } = await this.supabase
        .from('pm_task_dependencies')  // Updated table name
        .insert(dependency)
        .select()
        .single();

      if (error) throw error;

      return {
        success: true,
        dependency: data,
        message: 'Task dependency added successfully'
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async listTeamTasks(args: any) {
    try {
      let query = this.supabase
        .from('pm_tasks')  // Updated table name
        .select(`
          *,
          project:pm_projects(name, priority)
        `)
        .eq('assigned_team', args.team_id);

      if (args.status) {
        query = query.eq('status', args.status);
      }

      if (!args.include_completed) {
        query = query.not('status', 'in', '(completed,cancelled)');
      }

      const { data, error } = await query
        .order('priority', { ascending: true })
        .order('due_date', { ascending: true });

      if (error) throw error;

      return {
        success: true,
        tasks: data,
        count: data.length
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async reportBlocker(args: any) {
    try {
      // Update task status
      const { error: taskError } = await this.supabase
        .from('pm_tasks')  // Updated table name
        .update({
          status: 'blocked',
          blocker_description: args.blocker_description,
          updated_at: new Date().toISOString()
        })
        .eq('id', args.task_id);

      if (taskError) throw taskError;

      // Record the blocker
      const { error: updateError } = await this.supabase
        .from('pm_task_updates')  // Updated table name
        .insert({
          task_id: args.task_id,
          team_id: args.team_id,
          update_type: 'blocker_reported',
          new_value: args.blocker_description,
          notes: args.needs_help_from ? `Needs help from: ${args.needs_help_from}` : null
        });

      if (updateError) throw updateError;

      return {
        success: true,
        message: 'Blocker reported successfully',
        needs_help_from: args.needs_help_from
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private async getProjectAnalytics(projectId: string) {
    try {
      // Get project with all details
      const { data: project, error: projectError } = await this.supabase
        .from('pm_projects')  // Updated table name
        .select(`
          *,
          pm_tasks(*),
          pm_project_teams(*, team:teams(name))
        `)
        .eq('id', projectId)
        .single();

      if (projectError) throw projectError;

      // Calculate analytics
      const tasks = project.pm_tasks || [];
      const totalTasks = tasks.length;
      const completedTasks = tasks.filter((t: any) => t.status === 'completed').length;
      const blockedTasks = tasks.filter((t: any) => t.status === 'blocked').length;
      const inProgressTasks = tasks.filter((t: any) => t.status === 'in_progress').length;

      // Calculate velocity
      const completedWithHours = tasks.filter((t: any) =>
        t.status === 'completed' && t.estimated_hours && t.actual_hours
      );

      const velocityRatio = completedWithHours.length > 0
        ? completedWithHours.reduce((sum: number, t: any) =>
            sum + (t.estimated_hours / t.actual_hours), 0) / completedWithHours.length
        : 1;

      // Estimate completion
      const remainingHours = tasks
        .filter((t: any) => t.status !== 'completed')
        .reduce((sum: number, t: any) => sum + (t.estimated_hours || 0), 0);

      const estimatedRemainingHours = remainingHours / velocityRatio;

      return {
        success: true,
        analytics: {
          progress: {
            total_tasks: totalTasks,
            completed_tasks: completedTasks,
            in_progress_tasks: inProgressTasks,
            blocked_tasks: blockedTasks,
            completion_percentage: totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0
          },
          velocity: {
            velocity_ratio: velocityRatio,
            average_task_duration: completedWithHours.length > 0
              ? completedWithHours.reduce((sum: number, t: any) => sum + t.actual_hours, 0) / completedWithHours.length
              : 0,
            estimated_remaining_hours: estimatedRemainingHours
          },
          teams: {
            involved_teams: project.pm_project_teams?.length || 0,
            team_list: project.pm_project_teams?.map((pt: any) => ({
              name: pt.team.name,
              role: pt.role,
              allocation: pt.allocation_percentage
            }))
          },
          health: {
            has_blockers: blockedTasks > 0,
            on_track: project.health_status === 'on_track',
            days_until_deadline: project.target_end_date
              ? Math.ceil((new Date(project.target_end_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
              : null
          }
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Start the server
const server = new ProjectManagementServer();
server.start().catch(console.error);
