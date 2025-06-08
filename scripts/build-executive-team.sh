#!/bin/bash

echo "=== Building Executive Team Docker Image ==="
echo

# For now, let's create a simple working image that just runs and logs
echo "1. Creating temporary build directory..."
mkdir -p /tmp/executive-team-build
cd /tmp/executive-team-build

echo "2. Creating a simple Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install basic dependencies
RUN pip install fastapi uvicorn pyyaml

# Create a simple app that responds to health checks
RUN cat > main.py << 'PYTHON'
from fastapi import FastAPI
import os
import yaml

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy", "team": "executive"}

@app.get("/ready")
def ready():
    return {"status": "ready", "team": "executive"}

@app.get("/")
def root():
    return {
        "team": "Executive Leadership Team",
        "status": "running",
        "message": "Team infrastructure is working! Next step: implement actual CrewAI logic.",
        "environment": {
            "TEAM_NAME": os.getenv("TEAM_NAME", "unknown"),
            "AGENTGATEWAY_URL": os.getenv("AGENTGATEWAY_URL", "not set")
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TEAM_PORT", "8090"))
    uvicorn.run(app, host="0.0.0.0", port=port)
PYTHON

EXPOSE 8090

CMD ["python", "main.py"]
EOF

echo "3. Building Docker image..."
docker build -t ghcr.io/bryansparks/elfautomations-executive-team:latest .

echo "4. To push to GitHub Container Registry:"
echo "   a) Create a GitHub Personal Access Token with 'write:packages' scope"
echo "   b) Login to ghcr.io:"
echo "      echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u bryansparks --password-stdin"
echo "   c) Push the image:"
echo "      docker push ghcr.io/bryansparks/elfautomations-executive-team:latest"
echo
echo "5. OR use a local registry (easier for testing):"
echo "   docker tag ghcr.io/bryansparks/elfautomations-executive-team:latest localhost:5000/executive-team:latest"
echo "   docker run -d -p 5000:5000 --name registry registry:2  # if not already running"
echo "   docker push localhost:5000/executive-team:latest"
echo
echo "   Then update the deployment:"
echo "   kubectl set image deployment/executive-team executive-team=localhost:5000/executive-team:latest -n elf-teams"
echo
echo "6. OR load directly into OrbStack (simplest):"
echo "   docker save ghcr.io/bryansparks/elfautomations-executive-team:latest | kubectl exec -i -n kube-system deploy/orbstack -c k3s -- ctr -n k8s.io image import -"
echo "   Then restart the pod:"
echo "   kubectl rollout restart deployment/executive-team -n elf-teams"
