-- Virtual AI Company Platform - Business Tables
-- Run this SQL in your Supabase dashboard SQL editor

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    score INTEGER DEFAULT 0 CHECK (score >= 0 AND score <= 100),
    assigned_agent_id VARCHAR(255),
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    assignee VARCHAR(255),
    assigned_agent_id VARCHAR(255),
    created_by_agent_id VARCHAR(255),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Business metrics table
CREATE TABLE IF NOT EXISTS business_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    period_start DATE,
    period_end DATE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent activities table (for tracking agent actions)
CREATE TABLE IF NOT EXISTS agent_activities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    description TEXT,
    target_table VARCHAR(100),
    target_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score);
CREATE INDEX IF NOT EXISTS idx_leads_assigned_agent ON leads(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_business_metrics_name ON business_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_business_metrics_type ON business_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_agent_activities_agent ON agent_activities(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_activities_type ON agent_activities(activity_type);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO customers (name, email, phone, company, status) VALUES
('John Doe', 'john@techcorp.com', '+1-555-0101', 'Tech Corp', 'active'),
('Jane Smith', 'jane@startup.io', '+1-555-0102', 'Startup Inc', 'active'),
('Bob Johnson', 'bob@enterprise.com', '+1-555-0103', 'Enterprise Ltd', 'inactive'),
('Alice Brown', 'alice@prospect.com', '+1-555-0104', 'Prospect Co', 'active'),
('Charlie Wilson', 'charlie@potential.org', '+1-555-0105', 'Potential Org', 'active')
ON CONFLICT (email) DO NOTHING;

INSERT INTO leads (name, email, company, source, status, score) VALUES
('Diana Davis', 'diana@opportunity.net', 'Opportunity Net', 'website', 'qualified', 85),
('Eve Martinez', 'eve@growth.biz', 'Growth Biz', 'referral', 'new', 65),
('Frank Taylor', 'frank@scale.co', 'Scale Co', 'social', 'contacted', 75),
('Grace Lee', 'grace@expand.org', 'Expand Org', 'email', 'qualified', 90),
('Henry Chen', 'henry@develop.io', 'Develop IO', 'website', 'new', 55)
ON CONFLICT DO NOTHING;

INSERT INTO tasks (title, description, status, priority, assigned_agent_id, created_by_agent_id) VALUES
('Follow up with Diana Davis', 'Schedule demo call for high-value prospect', 'pending', 1, 'sales-agent-001', 'chief-ai-agent'),
('Prepare Q4 report', 'Compile quarterly business metrics and analysis', 'in_progress', 2, 'analytics-agent-001', 'chief-ai-agent'),
('Update website content', 'Refresh product descriptions and pricing', 'pending', 3, 'marketing-agent-001', 'marketing-manager'),
('Customer onboarding', 'Set up new customer account and training', 'pending', 2, 'customer-success-001', 'cs-manager'),
('Security audit', 'Review system security and compliance', 'pending', 1, 'security-agent-001', 'cto-agent')
ON CONFLICT DO NOTHING;

INSERT INTO business_metrics (metric_name, metric_value, metric_type, period_start, period_end) VALUES
('monthly_revenue', 125000.00, 'financial', '2024-11-01', '2024-11-30'),
('customer_acquisition_cost', 250.00, 'marketing', '2024-11-01', '2024-11-30'),
('customer_satisfaction', 4.2, 'service', '2024-11-01', '2024-11-30'),
('task_completion_rate', 0.92, 'operational', '2024-11-01', '2024-11-30'),
('lead_conversion_rate', 0.15, 'sales', '2024-11-01', '2024-11-30'),
('agent_efficiency', 0.87, 'operational', '2024-11-01', '2024-11-30')
ON CONFLICT DO NOTHING;

-- Verify tables were created
SELECT 'customers' as table_name, count(*) as row_count FROM customers
UNION ALL
SELECT 'leads' as table_name, count(*) as row_count FROM leads
UNION ALL
SELECT 'tasks' as table_name, count(*) as row_count FROM tasks
UNION ALL
SELECT 'business_metrics' as table_name, count(*) as row_count FROM business_metrics
UNION ALL
SELECT 'agent_activities' as table_name, count(*) as row_count FROM agent_activities
ORDER BY table_name;
