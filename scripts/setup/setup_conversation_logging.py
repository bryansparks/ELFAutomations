#!/usr/bin/env python3
"""
Setup script for conversation logging in Supabase
Creates the necessary tables and views for team conversation analysis
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.supabase_client import get_supabase_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print(
        "Error: Supabase client not available. Please ensure utils/supabase_client.py exists."
    )
    sys.exit(1)


CONVERSATION_LOGGING_SCHEMA = """
-- Team conversation logs table
CREATE TABLE IF NOT EXISTS team_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_name TEXT NOT NULL,
    task_id TEXT,
    agent_name TEXT NOT NULL,
    message TEXT NOT NULL,
    message_type TEXT NOT NULL,
    to_agent TEXT,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_team_conversations_team ON team_conversations(team_name);
CREATE INDEX IF NOT EXISTS idx_team_conversations_task ON team_conversations(task_id);
CREATE INDEX IF NOT EXISTS idx_team_conversations_timestamp ON team_conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_team_conversations_type ON team_conversations(message_type);
CREATE INDEX IF NOT EXISTS idx_team_conversations_agent ON team_conversations(agent_name);

-- Team performance metrics table
CREATE TABLE IF NOT EXISTS team_performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_name TEXT NOT NULL,
    evaluation_date DATE NOT NULL,
    task_success_rate FLOAT,
    communication_efficiency FLOAT,
    decision_quality FLOAT,
    avg_time_to_completion FLOAT,
    challenge_resolution_rate FLOAT,
    collaboration_score FLOAT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_name, evaluation_date)
);

-- View for conversation analytics
CREATE OR REPLACE VIEW conversation_analytics AS
SELECT
    team_name,
    DATE(timestamp) as conversation_date,
    COUNT(*) as total_messages,
    COUNT(DISTINCT agent_name) as active_agents,
    COUNT(DISTINCT task_id) as tasks_handled,
    COUNT(CASE WHEN message_type = 'decision' THEN 1 END) as decisions_made,
    COUNT(CASE WHEN message_type = 'challenge' THEN 1 END) as challenges_raised,
    COUNT(CASE WHEN message_type = 'proposal' THEN 1 END) as proposals_made,
    COUNT(CASE WHEN to_agent IS NOT NULL THEN 1 END) as directed_messages,
    AVG(CASE
        WHEN metadata->>'sentiment' = 'positive' THEN 1
        WHEN metadata->>'sentiment' = 'negative' THEN -1
        ELSE 0
    END) as avg_sentiment,
    COUNT(CASE WHEN metadata->>'sentiment' = 'positive' THEN 1 END) as positive_messages,
    COUNT(CASE WHEN metadata->>'sentiment' = 'negative' THEN 1 END) as negative_messages
FROM team_conversations
GROUP BY team_name, DATE(timestamp);

-- View for agent interaction patterns
CREATE OR REPLACE VIEW agent_interactions AS
SELECT
    tc1.team_name,
    tc1.agent_name as from_agent,
    tc1.to_agent,
    COUNT(*) as interaction_count,
    COUNT(CASE WHEN tc1.message_type = 'challenge' THEN 1 END) as challenges,
    COUNT(CASE WHEN tc1.message_type = 'proposal' THEN 1 END) as proposals,
    COUNT(CASE WHEN tc1.message_type = 'agreement' THEN 1 END) as agreements,
    COUNT(CASE WHEN tc1.message_type = 'disagreement' THEN 1 END) as disagreements
FROM team_conversations tc1
WHERE tc1.to_agent IS NOT NULL
GROUP BY tc1.team_name, tc1.agent_name, tc1.to_agent;

-- View for task performance
CREATE OR REPLACE VIEW task_performance AS
SELECT
    team_name,
    task_id,
    MIN(timestamp) as task_start,
    MAX(timestamp) as task_end,
    EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))/60 as duration_minutes,
    COUNT(*) as total_messages,
    COUNT(DISTINCT agent_name) as agents_involved,
    COUNT(CASE WHEN message_type = 'challenge' THEN 1 END) as challenges_during_task,
    COUNT(CASE WHEN message_type = 'decision' THEN 1 END) as decisions_made
FROM team_conversations
WHERE task_id IS NOT NULL
GROUP BY team_name, task_id;

-- View for identifying effective communication patterns
CREATE OR REPLACE VIEW effective_patterns AS
SELECT
    t1.team_name,
    t1.agent_name,
    t1.message_type,
    t2.message_type as response_type,
    COUNT(*) as pattern_count,
    AVG(EXTRACT(EPOCH FROM (t2.timestamp - t1.timestamp))) as avg_response_time_seconds
FROM team_conversations t1
JOIN team_conversations t2
    ON t1.team_name = t2.team_name
    AND t1.task_id = t2.task_id
    AND t2.timestamp > t1.timestamp
    AND t2.timestamp < t1.timestamp + INTERVAL '5 minutes'
WHERE t1.to_agent = t2.agent_name
GROUP BY t1.team_name, t1.agent_name, t1.message_type, t2.message_type
HAVING COUNT(*) > 3
ORDER BY pattern_count DESC;
"""


def setup_conversation_logging():
    """Create tables and views for conversation logging"""

    print("🚀 Setting up conversation logging in Supabase...")

    if not SUPABASE_AVAILABLE:
        print("❌ Supabase client not available")
        return False

    try:
        # Note: The Supabase Python client doesn't support direct SQL execution
        # You need to run this SQL in the Supabase dashboard

        print("\n📋 Please run the following SQL in your Supabase SQL editor:")
        print("   (Dashboard → SQL Editor → New Query)")
        print("\n" + "=" * 60 + "\n")
        print(CONVERSATION_LOGGING_SCHEMA)
        print("\n" + "=" * 60 + "\n")

        print("✅ Setup instructions displayed!")
        print("\n📝 After creating the tables:")
        print("   1. Your teams will automatically log conversations")
        print("   2. Logs will be stored both locally and in Supabase")
        print("   3. The Quality Auditor team can analyze patterns")
        print("   4. Use the views to generate performance reports")

        print("\n🔍 Useful queries after setup:")
        print(
            "   - SELECT * FROM conversation_analytics WHERE team_name = 'marketing-team';"
        )
        print("   - SELECT * FROM agent_interactions ORDER BY interaction_count DESC;")
        print("   - SELECT * FROM task_performance WHERE duration_minutes > 30;")
        print(
            "   - SELECT * FROM effective_patterns WHERE team_name = 'executive-team';"
        )

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def verify_setup():
    """Verify that the tables were created successfully"""

    try:
        client = get_supabase_client()

        # Try to query the table
        result = client.table("team_conversations").select("count").execute()

        print("\n✅ Verification successful! Tables are ready.")
        print(
            f"   Current conversation count: {result.data[0]['count'] if result.data else 0}"
        )

        return True

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        print("   Please ensure you've run the SQL in Supabase dashboard")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CONVERSATION LOGGING SETUP")
    print("=" * 60)

    if setup_conversation_logging():
        print("\n🔄 Checking if tables exist...")

        # Give user time to run the SQL
        input("\nPress Enter after you've run the SQL in Supabase...")

        if verify_setup():
            print("\n🎉 Conversation logging is ready to use!")
        else:
            print("\n⚠️  Please complete the setup in Supabase dashboard")
