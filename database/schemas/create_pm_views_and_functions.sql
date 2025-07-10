-- Views and functions for the pm_ prefixed project management tables

-- Active tasks per team
CREATE OR REPLACE VIEW pm_team_active_tasks AS
SELECT
    t.assigned_team as team_id,
    tm.name as team_name,
    COUNT(*) as active_task_count,
    SUM(t.estimated_hours - COALESCE(t.actual_hours, 0)) as remaining_hours,
    MIN(t.due_date) as next_deadline
FROM pm_tasks t
JOIN teams tm ON t.assigned_team = tm.id
WHERE t.status IN ('in_progress', 'ready', 'blocked')
GROUP BY t.assigned_team, tm.name;

-- Project dashboard view
CREATE OR REPLACE VIEW pm_project_dashboard AS
SELECT
    p.*,
    COUNT(DISTINCT t.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'blocked' THEN t.id END) as blocked_tasks,
    COUNT(DISTINCT pt.team_id) as teams_involved,
    MAX(t.updated_at) as last_activity
FROM pm_projects p
LEFT JOIN pm_tasks t ON p.id = t.project_id
LEFT JOIN pm_project_teams pt ON p.id = pt.project_id
GROUP BY p.id;

-- Available tasks for autonomous assignment
CREATE OR REPLACE VIEW pm_available_tasks_for_assignment AS
SELECT
    t.*,
    p.name as project_name,
    p.priority as project_priority,
    CASE
        WHEN t.due_date < CURRENT_TIMESTAMP + INTERVAL '2 days' THEN 'urgent'
        WHEN t.due_date < CURRENT_TIMESTAMP + INTERVAL '7 days' THEN 'soon'
        ELSE 'normal'
    END as urgency
FROM pm_tasks t
JOIN pm_projects p ON t.project_id = p.id
WHERE t.status = 'ready'
AND t.assigned_team IS NULL
AND NOT EXISTS (
    SELECT 1 FROM pm_task_dependencies td
    JOIN pm_tasks dep_task ON td.depends_on_task_id = dep_task.id
    WHERE td.task_id = t.id
    AND dep_task.status != 'completed'
);

-- Function to check if task dependencies are met
CREATE OR REPLACE FUNCTION pm_are_task_dependencies_met(p_task_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1
        FROM pm_task_dependencies td
        JOIN pm_tasks dep_task ON td.depends_on_task_id = dep_task.id
        WHERE td.task_id = p_task_id
        AND dep_task.status != 'completed'
        AND td.is_blocking = true
    );
END;
$$ LANGUAGE plpgsql;

-- Function to auto-assign tasks based on skills
CREATE OR REPLACE FUNCTION pm_find_best_team_for_task(p_task_id UUID)
RETURNS UUID AS $$
DECLARE
    v_best_team_id UUID;
BEGIN
    SELECT team_id INTO v_best_team_id
    FROM pm_task_skill_matches
    WHERE task_id = p_task_id
    AND match_score > 0.7
    ORDER BY match_score DESC
    LIMIT 1;

    RETURN v_best_team_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update task status when dependencies are met
CREATE OR REPLACE FUNCTION pm_check_task_ready()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE pm_tasks
    SET status = 'ready',
        ready_date = CURRENT_TIMESTAMP
    WHERE status = 'pending'
    AND id IN (
        SELECT td.task_id
        FROM pm_task_dependencies td
        WHERE td.depends_on_task_id = NEW.id
    )
    AND pm_are_task_dependencies_met(id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update project progress
CREATE OR REPLACE FUNCTION pm_update_project_progress()
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
    FROM pm_tasks
    WHERE project_id = v_project_id;

    IF v_total_tasks > 0 THEN
        v_progress := (v_completed_tasks::FLOAT / v_total_tasks) * 100;
    ELSE
        v_progress := 0;
    END IF;

    UPDATE pm_projects
    SET progress_percentage = v_progress,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = v_project_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER pm_trigger_task_ready_check
AFTER UPDATE OF status ON pm_tasks
FOR EACH ROW
WHEN (NEW.status = 'completed' AND OLD.status != 'completed')
EXECUTE FUNCTION pm_check_task_ready();

CREATE TRIGGER pm_trigger_project_progress_update
AFTER INSERT OR UPDATE OF status ON pm_tasks
FOR EACH ROW
EXECUTE FUNCTION pm_update_project_progress();

-- Grant permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
