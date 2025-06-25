#!/bin/bash
# Build script for RAG Processor Team
# This script should be run from the team directory

set -e

TEAM_NAME="rag-processor-team"
IMAGE_NAME="elf-automations/$TEAM_NAME:latest"

echo "🚀 Building RAG Processor Team Docker image..."
echo "============================================"

# Get the project root (two levels up from this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "📁 Project root: $PROJECT_ROOT"
echo "📦 Building image: $IMAGE_NAME"

# Create a temporary Dockerfile that includes the shared modules
cat > Dockerfile.build << 'EOF'
# RAG Processor Team Docker Image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy shared modules first
COPY elf_automations /app/elf_automations

# Copy team-specific requirements
COPY teams/rag-processor-team/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy team code
COPY teams/rag-processor-team/ .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server
CMD ["python", "server.py"]
EOF

# Build from project root
cd "$PROJECT_ROOT"
docker build -f "$SCRIPT_DIR/Dockerfile.build" -t "$IMAGE_NAME" .

# Clean up
rm "$SCRIPT_DIR/Dockerfile.build"

echo ""
echo "✅ Build complete!"
echo ""
echo "To run locally:"
echo "docker run -p 8000:8000 -e OPENAI_API_KEY=\$OPENAI_API_KEY $IMAGE_NAME"
echo ""
echo "To transfer to ArgoCD machine:"
echo "cd $PROJECT_ROOT && ./scripts/transfer-docker-images-ssh.sh"
