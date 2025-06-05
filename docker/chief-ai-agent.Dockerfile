FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
COPY README.md ./
RUN pip install -e .

# Copy source code
COPY agents/ ./agents/
COPY config/ ./config/
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash agent
RUN chown -R agent:agent /app
USER agent

# Expose health check port
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the kagent-wrapped agent
CMD ["python", "-m", "agents.executive.chief_ai_kagent"]
