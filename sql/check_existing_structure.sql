-- Check columns in existing projects table
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'projects'
ORDER BY ordinal_position;

-- Check columns in existing tasks table
SELECT
    '---TASKS TABLE---' as separator;

SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'tasks'
ORDER BY ordinal_position;

-- Check the trigger definition
SELECT
    '---TRIGGER DEFINITION---' as separator;

SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
AND trigger_name = 'update_tasks_updated_at';
