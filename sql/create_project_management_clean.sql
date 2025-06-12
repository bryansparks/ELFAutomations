CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_owner_team ON projects(owner_team);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_team ON tasks(assigned_team, status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE status NOT IN ('completed', 'cancelled');
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_task_updates_task ON task_updates(task_id);

CREATE OR REPLACE VIEW team_active_tasks AS
SELECT 
    t.assigned_team as team_id,
    tm.name as team_name,
    COUNT(*) as active_task_count,
    SUM(t.estimated_hours - COALESCE(t.actual_hours, 0)) as remaining_hours,
    MIN(t.due_date) as next_deadline
FROM tasks t
JOIN teams tm ON t.assigned_team = tm.id
WHERE t.status IN ('in_progress', 'ready', 'blocked')
GROUP BY t.assigned_team, tm.name;

CREATE OR REPLACE VIEW project_dashboard AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.status,
    p.priority,
    p.created_by_team,
    p.owner_team,
    p.start_date,
    p.target_end_date,
    p.actual_end_date,
    p.progress_percentage,
    p.health_status,
    p.estimated_hours,
    p.actual_hours,
    p.created_at,
    p.updated_at,
    p.metadata,
    COUNT(DISTINCT t.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'blocked' THEN t.id END) as blocked_tasks,
    COUNT(DISTINCT pt.team_id) as teams_involved,
    MAX(t.updated_at) as last_activity
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
LEFT JOIN project_teams pt ON p.id = pt.project_id
GROUP BY p.id, p.name, p.description, p.status, p.priority, p.created_by_team, 
         p.owner_team, p.start_date, p.target_end_date, p.actual_end_date,
         p.progress_percentage, p.health_status, p.estimated_hours, p.actual_hours,
         p.created_at, p.updated_at, p.metadata;

CREATE OR REPLACE VIEW available_tasks_for_assignment AS
SELECT 
    t.*,
    p.name as project_name,
    p.priority as project_priority,
    CASE 
        WHEN t.due_date < CURRENT_TIMESTAMP + INTERVAL '2 days' THEN 'urgent'
        WHEN t.due_date < CURRENT_TIMESTAMP + INTERVAL '7 days' THEN 'soon'
        ELSE 'normal'
    END as urgency
FROM tasks t
JOIN projects p ON t.project_id = p.id
WHERE t.status = 'ready'
AND t.assigned_team IS NULL
AND NOT EXISTS (
    SELECT 1 FROM task_dependencies td
    JOIN tasks dep_task ON td.depends_on_task_id = dep_task.id
    WHERE td.task_id = t.id
    AND dep_task.status != 'completed'
);

CREATE OR REPLACE FUNCTION are_task_dependencies_met(p_task_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1 
        FROM task_dependencies td
        JOIN tasks dep_task ON td.depends_on_task_id = dep_task.id
        WHERE td.task_id = p_task_id
        AND dep_task.status != 'completed'
        AND td.is_blocking = true
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION find_best_team_for_task(p_task_id UUID)
RETURNS UUID AS $$
DECLARE
    v_best_team_id UUID;
BEGIN
    SELECT team_id INTO v_best_team_id
    FROM task_skill_matches
    WHERE task_id = p_task_id
    AND match_score > 0.7
    ORDER BY match_score DESC
    LIMIT 1;
    
    RETURN v_best_team_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_task_ready()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE tasks
    SET status = 'ready',
        ready_date = CURRENT_TIMESTAMP
    WHERE status = 'pending'
    AND id IN (
        SELECT td.task_id
        FROM task_dependencies td
        WHERE td.depends_on_task_id = NEW.id
    )
    AND are_task_dependencies_met(id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_project_progress()
RETURNS TRIGGER AS $$
DECLARE
    v_total_tasks INTEGER;
    v_completed_tasks INTEGER;
    v_progress FLOAT;
    v_project_id UUID;
BEGIN
    v_project_id := NEW.project_id;
    
    IF v_project_id IS NULL THEN
        RETURN NEW;
    END IF;
    
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN status = 'completed' THEN 1 END)
    INTO v_total_tasks, v_completed_tasks
    FROM tasks
    WHERE project_id = v_project_id;
    
    IF v_total_tasks > 0 THEN
        v_progress := (v_completed_tasks::FLOAT / v_total_tasks) * 100;
    ELSE
        v_progress := 0;
    END IF;
    
    UPDATE projects
    SET progress_percentage = v_progress,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = v_project_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_task_ready_check') THEN
        CREATE TRIGGER trigger_task_ready_check
        AFTER UPDATE OF status ON tasks
        FOR EACH ROW
        WHEN (NEW.status = 'completed' AND OLD.status != 'completed')
        EXECUTE FUNCTION check_task_ready();
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_project_progress_update') THEN
        CREATE TRIGGER trigger_project_progress_update
        AFTER INSERT OR UPDATE OF status ON tasks
        FOR EACH ROW
        EXECUTE FUNCTION update_project_progress();
    END IF;
END$$;

GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;