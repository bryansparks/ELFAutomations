#!/usr/bin/env python3
"""
Development Database Setup

Sets up lightweight development databases using Docker or in-memory alternatives.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_docker_compose():
    """Check if Docker Compose is available."""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True
        # Try docker compose (newer syntax)
        result = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def create_docker_compose():
    """Create a docker-compose.yml for development databases."""
    project_root = Path(__file__).parent.parent
    compose_file = project_root / "docker-compose.dev.yml"

    compose_content = """version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: elf_postgres_dev
    environment:
      POSTGRES_DB: elf_automations
      POSTGRES_USER: elf_user
      POSTGRES_PASSWORD: elf_password
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U elf_user -d elf_automations"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: elf_redis_dev
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
"""

    with open(compose_file, "w") as f:
        f.write(compose_content)

    logger.info("Created docker-compose.dev.yml", path=str(compose_file))
    return compose_file


def create_init_sql():
    """Create initialization SQL for PostgreSQL."""
    project_root = Path(__file__).parent.parent
    sql_dir = project_root / "scripts" / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)

    init_sql = sql_dir / "init.sql"

    sql_content = """-- ELF Automations Development Database Initialization

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE elf_automations' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'elf_automations');

-- Connect to the database
\\c elf_automations;

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
"""

    with open(init_sql, "w") as f:
        f.write(sql_content)

    logger.info("Created database initialization SQL", path=str(init_sql))
    return init_sql


def update_env_file():
    """Update .env file with development database URLs."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if not env_file.exists():
        logger.error(".env file not found - run setup_env.py first")
        return False

    # Read existing .env
    with open(env_file, "r") as f:
        lines = f.readlines()

    # Update database URLs
    updated_lines = []
    db_url_set = False
    redis_url_set = False

    for line in lines:
        if line.startswith("DATABASE_URL="):
            updated_lines.append(
                "DATABASE_URL=postgresql://elf_user:elf_password@localhost:5432/elf_automations\n"
            )
            db_url_set = True
        elif line.startswith("REDIS_URL="):
            updated_lines.append("REDIS_URL=redis://localhost:6379/0\n")
            redis_url_set = True
        else:
            updated_lines.append(line)

    # Add URLs if they weren't found
    if not db_url_set:
        updated_lines.append(
            "DATABASE_URL=postgresql://elf_user:elf_password@localhost:5432/elf_automations\n"
        )
    if not redis_url_set:
        updated_lines.append("REDIS_URL=redis://localhost:6379/0\n")

    # Write updated .env
    with open(env_file, "w") as f:
        f.writelines(updated_lines)

    logger.info("Updated .env file with development database URLs")
    return True


async def start_databases():
    """Start development databases using Docker Compose."""
    try:
        # Check if containers are already running
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name=elf_postgres_dev",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
        )

        if "elf_postgres_dev" in result.stdout:
            logger.info("Development databases are already running")
            return True

        # Start databases
        logger.info("Starting development databases...")
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.dev.yml", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            # Try with docker compose (newer syntax)
            result = subprocess.run(
                ["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d"],
                capture_output=True,
                text=True,
                timeout=60,
            )

        if result.returncode == 0:
            logger.info("Development databases started successfully")

            # Wait for health checks
            logger.info("Waiting for databases to be ready...")
            await asyncio.sleep(10)

            return True
        else:
            logger.error("Failed to start databases", error=result.stderr)
            return False

    except Exception as e:
        logger.error("Error starting databases", error=str(e))
        return False


def main():
    """Main setup function."""
    logger.info("🗄️ ELF Automations Development Database Setup")
    logger.info("=" * 50)

    # Check Docker availability
    if not check_docker():
        logger.error("Docker is not available. Please install Docker first.")
        logger.info("Visit: https://docs.docker.com/get-docker/")
        return 1

    if not check_docker_compose():
        logger.error("Docker Compose is not available. Please install Docker Compose.")
        return 1

    logger.info("✅ Docker and Docker Compose are available")

    try:
        # Create Docker Compose file
        create_docker_compose()

        # Create initialization SQL
        create_init_sql()

        # Update .env file
        if not update_env_file():
            return 1

        # Start databases
        success = asyncio.run(start_databases())

        if success:
            logger.info("🚀 Development databases are ready!")
            logger.info(
                "PostgreSQL: postgresql://elf_user:elf_password@localhost:5432/elf_automations"
            )
            logger.info("Redis: redis://localhost:6379/0")
            logger.info(
                "\nTo stop databases: docker-compose -f docker-compose.dev.yml down"
            )
            logger.info(
                "To view logs: docker-compose -f docker-compose.dev.yml logs -f"
            )
            return 0
        else:
            logger.error("Failed to start development databases")
            return 1

    except Exception as e:
        logger.error("Setup failed", error=str(e))
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
