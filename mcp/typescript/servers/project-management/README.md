# Project Management MCP Server

This MCP server provides project and task management capabilities that enable AI teams to autonomously coordinate complex work without human intervention.

**Note**: This server uses `pm_` prefixed tables (pm_projects, pm_tasks, etc.) to avoid conflicts with existing tables in Supabase.

## Features

### Project Management
- Create and manage projects with priorities and deadlines
- Track project progress automatically
- Monitor project health and identify risks
- View comprehensive project analytics

### Task Management
- Create tasks with skill requirements
- Automatic task assignment based on team capabilities
- Dependency tracking and management
- Progress tracking and status updates
- Blocker reporting and resolution

### Autonomous Coordination
- Teams can find available work matching their skills
- Automatic notification when dependencies are met
- Self-organizing task allocation
- Cross-team coordination without human intervention

## Available Tools

### Project Tools

#### create_project
Create a new project with automatic setup.
```typescript
{
  name: string,              // Project name
  description?: string,      // Project description
  priority: 'critical' | 'high' | 'medium' | 'low',
  owner_team?: string,       // Team ID that owns the project
  target_end_date?: string   // Target completion date (YYYY-MM-DD)
}
```

#### get_project_status
Get comprehensive project status including all tasks and team involvement.
```typescript
{
  project_id: string  // Project ID to query
}
```

#### list_projects
List projects with optional filters.
```typescript
{
  status?: string,      // Filter by status
  owner_team?: string,  // Filter by owner team
  priority?: string     // Filter by priority
}
```

### Task Tools

#### create_task
Create a new task within a project.
```typescript
{
  project_id: string,        // Parent project
  title: string,             // Task title
  description?: string,      // Task description
  task_type?: string,        // Type of task
  assigned_team?: string,    // Team to assign to
  required_skills?: string[], // Required skills
  estimated_hours?: number,  // Estimated hours
  due_date?: string         // Due date (YYYY-MM-DD)
}
```

#### update_task_status
Update task status and progress.
```typescript
{
  task_id: string,           // Task to update
  status: string,            // New status
  notes?: string,            // Update notes
  progress_percentage?: number, // Progress (0-100)
  hours_worked?: number      // Hours worked
}
```

#### assign_task
Assign or reassign a task to a team.
```typescript
{
  task_id: string,      // Task to assign
  team_id: string,      // Team to assign to
  agent_role?: string   // Specific agent role
}
```

#### add_task_dependency
Create a dependency between tasks.
```typescript
{
  task_id: string,           // Task with dependency
  depends_on_task_id: string, // Task that must complete first
  dependency_type?: string   // Type of dependency
}
```

#### list_team_tasks
Get all tasks assigned to a team.
```typescript
{
  team_id: string,           // Team ID
  status?: string,           // Filter by status
  include_completed?: boolean // Include completed tasks
}
```

### Coordination Tools

#### find_available_work
Find tasks matching team capabilities.
```typescript
{
  team_id: string,         // Team looking for work
  skills: string[],        // Team's skills
  capacity_hours?: number  // Available capacity
}
```

#### report_blocker
Report a blocker on a task.
```typescript
{
  task_id: string,              // Blocked task
  blocker_description: string,  // Description
  needs_help_from?: string      // Team that can help
}
```

#### get_project_analytics
Get detailed analytics for a project.
```typescript
{
  project_id: string  // Project to analyze
}
```

## Usage Example

### Team Finding Work
```javascript
// Engineering team looking for work
const result = await mcp.find_available_work({
  team_id: "engineering-team-id",
  skills: ["python", "api", "database"],
  capacity_hours: 40
});

// Claim the highest priority task
if (result.available_tasks.length > 0) {
  await mcp.assign_task({
    task_id: result.available_tasks[0].id,
    team_id: "engineering-team-id"
  });
}
```

### Project Creation with Tasks
```javascript
// Create a new project
const project = await mcp.create_project({
  name: "Customer Analytics Dashboard",
  description: "Build analytics dashboard for customer insights",
  priority: "high",
  owner_team: "product-team-id",
  target_end_date: "2025-03-01"
});

// Add tasks
await mcp.create_task({
  project_id: project.project.id,
  title: "Design database schema",
  required_skills: ["database", "sql"],
  estimated_hours: 16
});

await mcp.create_task({
  project_id: project.project.id,
  title: "Build API endpoints",
  required_skills: ["python", "fastapi"],
  estimated_hours: 24
});
```

### Progress Tracking
```javascript
// Update task progress
await mcp.update_task_status({
  task_id: "task-id",
  status: "in_progress",
  progress_percentage: 50,
  hours_worked: 4,
  notes: "Completed database design, starting implementation"
});
```

## Configuration

Set these environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key

## Integration with Teams

Teams should be updated to:
1. Periodically check for available work using `find_available_work`
2. Update task status as work progresses
3. Report blockers when encountered
4. Mark tasks complete when finished

This enables fully autonomous project execution!
