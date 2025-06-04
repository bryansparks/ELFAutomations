-- ELF Automations Database Initialization
-- This script sets up the basic database schema for the Virtual AI Company Platform

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS workflows;
CREATE SCHEMA IF NOT EXISTS business;
CREATE SCHEMA IF NOT EXISTS audit;

-- Agents schema tables
CREATE TABLE IF NOT EXISTS agents.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'executive', 'department_head', 'individual'
    department VARCHAR(100),
    status VARCHAR(50) DEFAULT 'inactive',
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agents.agent_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents.agents(id) ON DELETE CASCADE,
    state_data JSONB NOT NULL,
    checkpoint_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflows schema tables
CREATE TABLE IF NOT EXISTS workflows.workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'cross_department', 'department', 'individual'
    definition JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflows.workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows.workflows(id),
    initiator_agent_id UUID REFERENCES agents.agents(id),
    status VARCHAR(50) DEFAULT 'running',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Business schema tables
CREATE TABLE IF NOT EXISTS business.customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    company VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS business.leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES business.customers(id),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    score INTEGER DEFAULT 0,
    assigned_agent_id UUID REFERENCES agents.agents(id),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS business.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100),
    priority INTEGER DEFAULT 3,
    status VARCHAR(50) DEFAULT 'pending',
    assigned_agent_id UUID REFERENCES agents.agents(id),
    created_by_agent_id UUID REFERENCES agents.agents(id),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit schema tables
CREATE TABLE IF NOT EXISTS audit.agent_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents.agents(id),
    action_type VARCHAR(100) NOT NULL,
    action_data JSONB NOT NULL,
    result JSONB,
    success BOOLEAN DEFAULT true,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit.inter_agent_communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_agent_id UUID NOT NULL REFERENCES agents.agents(id),
    to_agent_id UUID NOT NULL REFERENCES agents.agents(id),
    message_type VARCHAR(100) NOT NULL,
    message_data JSONB NOT NULL,
    response_data JSONB,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents.agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_department ON agents.agents(department);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents.agents(status);
CREATE INDEX IF NOT EXISTS idx_agent_state_agent_id ON agents.agent_state(agent_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflows.workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_leads_status ON business.leads(status);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON business.tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON business.tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_actions_agent_id ON audit.agent_actions(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_actions_created_at ON audit.agent_actions(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents.agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows.workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON business.customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON business.leads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON business.tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some initial data
INSERT INTO agents.agents (name, type, department, status, config) VALUES
('Chief AI Agent', 'executive', 'executive', 'active', '{"model": "claude-3-5-sonnet-20241022", "max_tokens": 4000}'),
('Sales Manager', 'department_head', 'sales', 'inactive', '{"model": "claude-3-5-sonnet-20241022", "max_tokens": 2000}'),
('Marketing Manager', 'department_head', 'marketing', 'inactive', '{"model": "claude-3-5-sonnet-20241022", "max_tokens": 2000}')
ON CONFLICT DO NOTHING;
