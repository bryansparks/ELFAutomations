-- Enable chat interface for the executive team
UPDATE teams
SET
    is_top_level = true,
    enable_chat_interface = true,
    chat_config = jsonb_build_object(
        'allowed_roles', ARRAY['admin', 'user'],
        'max_session_duration_minutes', 60,
        'max_messages_per_session', 100,
        'enable_delegation_preview', true,
        'context_window_messages', 20,
        'require_user_confirmation', true
    )
WHERE name = 'executive-team';

-- Also enable for any other top-level department heads
UPDATE teams
SET
    is_top_level = true,
    enable_chat_interface = true,
    chat_config = jsonb_build_object(
        'allowed_roles', ARRAY['admin', 'user'],
        'max_session_duration_minutes', 45,
        'max_messages_per_session', 50,
        'enable_delegation_preview', true,
        'context_window_messages', 20,
        'require_user_confirmation', true
    )
WHERE name IN ('engineering-team', 'marketing-team', 'operations-team', 'finance-team')
AND NOT enable_chat_interface;

-- Check which teams now have chat enabled
SELECT
    name,
    department,
    is_top_level,
    enable_chat_interface,
    chat_config
FROM teams
WHERE is_top_level = true OR enable_chat_interface = true
ORDER BY name;
