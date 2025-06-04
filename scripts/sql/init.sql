-- ELF Automations Development Database Initialization

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE elf_automations' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'elf_automations');

-- Connect to the database
\c elf_automations;

-- Create tables for business tools
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    score INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assignee VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS business_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    period_start DATE,
    period_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO customers (name, email, company, status) VALUES
    ('John Doe', 'john@example.com', 'Tech Corp', 'active'),
    ('Jane Smith', 'jane@startup.io', 'Startup Inc', 'active'),
    ('Bob Johnson', 'bob@enterprise.com', 'Enterprise Ltd', 'inactive')
ON CONFLICT (email) DO NOTHING;

INSERT INTO leads (name, email, company, source, status, score) VALUES
    ('Alice Brown', 'alice@prospect.com', 'Prospect Co', 'website', 'qualified', 85),
    ('Charlie Wilson', 'charlie@potential.org', 'Potential Org', 'referral', 'new', 65),
    ('Diana Davis', 'diana@opportunity.net', 'Opportunity Net', 'social', 'contacted', 75)
ON CONFLICT DO NOTHING;

INSERT INTO tasks (title, description, assignee, status, priority) VALUES
    ('Follow up with Alice Brown', 'Schedule demo call', 'sales-agent-001', 'pending', 'high'),
    ('Prepare Q4 report', 'Compile quarterly business metrics', 'analytics-agent-001', 'in_progress', 'medium'),
    ('Update website content', 'Refresh product descriptions', 'marketing-agent-001', 'pending', 'low')
ON CONFLICT DO NOTHING;

INSERT INTO business_metrics (metric_name, metric_value, metric_type, period_start, period_end) VALUES
    ('monthly_revenue', 125000.00, 'financial', '2024-11-01', '2024-11-30'),
    ('customer_acquisition_cost', 250.00, 'marketing', '2024-11-01', '2024-11-30'),
    ('customer_satisfaction', 4.2, 'service', '2024-11-01', '2024-11-30'),
    ('task_completion_rate', 0.92, 'operational', '2024-11-01', '2024-11-30')
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON business_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_period ON business_metrics(period_start, period_end);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO elf_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO elf_user;

SELECT 'Database initialization complete' as status;
