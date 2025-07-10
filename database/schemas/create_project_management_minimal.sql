-- Project & Task Management System - Minimal Version
-- This version creates tables first, then adds views and functions one by one

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create Projects table first
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'planning'
        CHECK (status IN ('planning', 'active', 'on_hold', 'completed', 'cancelled')),
    priority VARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    created_by_team UUID REFERENCES teams(id),
    owner_team UUID REFERENCES teams(id),
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,
    progress_percentage FLOAT DEFAULT 0.0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    health_status VARCHAR(20) DEFAULT 'on_track'
        CHECK (health_status IN ('on_track', 'at_risk', 'delayed', 'blocked')),
    estimated_hours FLOAT,
    actual_hours FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 2. Create Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) DEFAULT 'development'
        CHECK (task_type IN ('development', 'design', 'analysis', 'testing', 'deployment', 'documentation', 'review')),
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'ready', 'in_progress', 'blocked', 'review', 'completed', 'cancelled')),
    blocker_description TEXT,
    created_by_team UUID REFERENCES teams(id),
    assigned_team UUID REFERENCES teams(id),
    assigned_agent VARCHAR(255),
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    estimated_hours FLOAT,
    actual_hours FLOAT DEFAULT 0.0,
    complexity VARCHAR(20) DEFAULT 'medium'
        CHECK (complexity IN ('trivial', 'easy', 'medium', 'hard', 'expert')),
    ready_date TIMESTAMP,
    start_date TIMESTAMP,
    due_date TIMESTAMP,
    completed_date TIMESTAMP,
    required_skills TEXT[],
    progress_percentage FLOAT DEFAULT 0.0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 3. Create Task Dependencies table
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'finish_to_start'
        CHECK (dependency_type IN ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish')),
    is_blocking BOOLEAN DEFAULT TRUE,
    lag_hours FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, depends_on_task_id)
);

-- 4. Create Task Updates table
CREATE TABLE IF NOT EXISTS task_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id),
    agent_role VARCHAR(255),
    update_type VARCHAR(50) NOT NULL
        CHECK (update_type IN ('status_change', 'progress_update', 'blocker_reported',
                              'blocker_resolved', 'assignment_change', 'comment')),
    old_value TEXT,
    new_value TEXT,
    notes TEXT,
    hours_worked FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create Project Teams table
CREATE TABLE IF NOT EXISTS project_teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id),
    role VARCHAR(100) DEFAULT 'contributor',
    allocation_percentage FLOAT DEFAULT 100.0 CHECK (allocation_percentage > 0 AND allocation_percentage <= 100),
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    UNIQUE(project_id, team_id)
);

-- 6. Create Task Skills Match table
CREATE TABLE IF NOT EXISTS task_skill_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id),
    match_score FLOAT NOT NULL CHECK (match_score >= 0 AND match_score <= 1),
    matching_skills TEXT[],
    missing_skills TEXT[],
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, team_id)
);

-- 7. Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_owner_team ON projects(owner_team);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_team ON tasks(assigned_team, status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE status NOT IN ('completed', 'cancelled');
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_task_updates_task ON task_updates(task_id);

-- 8. Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- End of minimal setup
-- Views and functions can be added separately after confirming tables are created
