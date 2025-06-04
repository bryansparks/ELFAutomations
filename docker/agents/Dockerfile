# Multi-stage build for AI agents
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r agentuser && useradd -r -g agentuser agentuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create app directory
WORKDIR /app

# Copy application code
COPY agents/ ./agents/
COPY utils/ ./utils/
COPY mcp_servers/ ./mcp_servers/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY *.py ./

# Change ownership to agentuser
RUN chown -R agentuser:agentuser /app

# Switch to non-root user
USER agentuser

# Health check for agent processes
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import agents.registry; print('Agents healthy')" || exit 1

# Default command - can be overridden for specific agents
CMD ["python", "-m", "agents.executive.chief_ai_agent"]
