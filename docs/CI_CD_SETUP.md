# CI/CD Pipeline Setup for Virtual AI Company Platform

## Overview

This document describes the comprehensive CI/CD pipeline setup for the Virtual AI Company Platform, implementing automated testing, security scanning, building, and deployment processes.

## Pipeline Architecture

### 1. Main CI/CD Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` and `develop` branches
- Pull requests to `main` and `develop`
- Manual workflow dispatch

**Jobs:**

#### Testing Job
- **Python Versions:** 3.11, 3.12
- **Code Quality:**
  - Black formatting check
  - isort import sorting
  - flake8 linting
  - mypy type checking
- **Security Scanning:**
  - bandit for Python security issues
  - safety for dependency vulnerabilities
- **Test Execution:**
  - pytest with coverage reporting
  - Upload to Codecov

#### Security Scanning Job
- **Container Scanning:** Trivy vulnerability scanner
- **Dependency Analysis:** SARIF format results
- **GitHub Security Integration:** Automatic security alerts

#### Build Job
- **Docker Images:**
  - Web dashboard (`ghcr.io/bryansparks/elfautomations-web`)
  - AI agents (`ghcr.io/bryansparks/elfautomations-agents`)
- **Registry:** GitHub Container Registry (GHCR)
- **Tagging Strategy:**
  - `develop-latest` for develop branch
  - `main-latest` for main branch
  - Git SHA tags for all builds

#### Deployment Jobs
- **Staging:** Auto-deploy from `develop` branch
- **Production:** Auto-deploy from `main` branch
- **Environment-specific configurations**
- **Smoke tests post-deployment**

### 2. Security Pipeline (`.github/workflows/security.yml`)

**Schedule:** Daily at 2 AM UTC

**Features:**
- **Dependency Scanning:** safety, pip-audit
- **Container Security:** Trivy scanning
- **Secret Scanning:** TruffleHog
- **Auto-merge:** Dependabot minor/patch updates

## Repository Secrets Configuration

### Required Secrets

```bash
# GitHub Container Registry
GITHUB_TOKEN  # Automatically provided

# Kubernetes Clusters
KUBE_CONFIG_STAGING     # Base64 encoded kubeconfig for staging
KUBE_CONFIG_PRODUCTION  # Base64 encoded kubeconfig for production

# Supabase Configuration
SUPABASE_URL                    # https://your-project.supabase.co
SUPABASE_ANON_KEY              # Public anon key
SUPABASE_PERSONAL_ACCESS_TOKEN # Personal access token
SUPABASE_PROJECT_ID            # Project ID

# AI API Keys
ANTHROPIC_API_KEY  # Claude API key
OPENAI_API_KEY     # OpenAI API key
```

### Setting Up Secrets

1. **Navigate to Repository Settings**
   ```
   GitHub Repository → Settings → Secrets and variables → Actions
   ```

2. **Add New Repository Secret**
   - Click "New repository secret"
   - Enter name and value
   - Click "Add secret"

3. **Kubernetes Secrets Setup**
   ```bash
   # Encode your kubeconfig
   cat ~/.kube/config | base64 | pbcopy

   # Add as KUBE_CONFIG_STAGING or KUBE_CONFIG_PRODUCTION
   ```

## Environment Setup

### Staging Environment
- **Namespace:** `virtual-ai-platform-staging`
- **Replicas:** 2 web, 1 agent
- **Domain:** `staging.virtual-ai.local`
- **Auto-deploy:** From `develop` branch

### Production Environment
- **Namespace:** `virtual-ai-platform`
- **Replicas:** 3 web, 2 agents (with HPA)
- **Domain:** `virtual-ai.company`
- **Auto-deploy:** From `main` branch
- **Features:** SSL/TLS, rate limiting, persistent storage

## Local Development Deployment

### Prerequisites
```bash
# Ensure minikube is running
minikube start

# Ensure kubectl context is set
kubectl config use-context minikube

# Set environment variables
export SUPABASE_ANON_KEY="your-anon-key"
export SUPABASE_PERSONAL_ACCESS_TOKEN="your-token"
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
```

### Deploy to Staging
```bash
# Run the deployment script
./scripts/deploy_to_staging.sh

# Access the application
kubectl port-forward -n virtual-ai-platform-staging service/virtual-ai-web-service 8080:80

# Open browser to http://localhost:8080
```

## Monitoring and Observability

### Deployment Health Checks
```bash
# Check deployment status
kubectl get deployments -n virtual-ai-platform-staging

# View pod logs
kubectl logs -n virtual-ai-platform-staging -l app=virtual-ai-web

# Monitor agent activities
kubectl logs -n virtual-ai-platform-staging -l app=virtual-ai-agents
```

### CI/CD Pipeline Monitoring
- **GitHub Actions:** Monitor workflow runs in Actions tab
- **Security Alerts:** Check Security tab for vulnerabilities
- **Dependabot:** Review dependency update PRs

## Security Features

### Code Security
- **Static Analysis:** bandit security linting
- **Dependency Scanning:** safety vulnerability checks
- **Container Scanning:** Trivy filesystem analysis
- **Secret Scanning:** TruffleHog for exposed secrets

### Runtime Security
- **Non-root Containers:** All containers run as non-root users
- **Read-only Filesystems:** Containers use read-only root filesystems
- **Security Contexts:** Proper security contexts configured
- **RBAC:** Role-based access control for Kubernetes

### Network Security
- **TLS/SSL:** Production environments use HTTPS
- **Rate Limiting:** API rate limiting configured
- **Network Policies:** Kubernetes network segmentation

## Troubleshooting

### Common Issues

#### 1. Docker Build Failures
```bash
# Check Dockerfile syntax
docker build -t test-image -f docker/web/Dockerfile .

# Review build logs in GitHub Actions
```

#### 2. Deployment Failures
```bash
# Check pod status
kubectl describe pod -n virtual-ai-platform-staging

# Review deployment events
kubectl get events -n virtual-ai-platform-staging --sort-by='.lastTimestamp'
```

#### 3. Secret Configuration Issues
```bash
# Verify secrets exist
kubectl get secrets -n virtual-ai-platform-staging

# Check secret contents (base64 encoded)
kubectl get secret supabase-secrets -n virtual-ai-platform-staging -o yaml
```

### Debug Commands
```bash
# Test CI pipeline locally
python -m pytest tests/test_ci_cd.py -v

# Validate Kubernetes manifests
kubectl apply --dry-run=client -f k8s/staging/

# Check image availability
docker images | grep virtual-ai
```

## Continuous Improvement

### Metrics and KPIs
- **Build Success Rate:** Target >95%
- **Deployment Time:** Target <10 minutes
- **Test Coverage:** Target >90%
- **Security Scan Pass Rate:** Target 100%

### Future Enhancements
- **Blue-Green Deployments:** Zero-downtime deployments
- **Canary Releases:** Gradual rollout strategy
- **Performance Testing:** Automated load testing
- **Multi-region Deployment:** Geographic distribution

## Support and Maintenance

### Regular Tasks
- **Weekly:** Review Dependabot PRs
- **Monthly:** Update base images
- **Quarterly:** Security audit and penetration testing

### Contacts
- **DevOps Lead:** Bryan Sparks
- **Security Team:** TBD
- **Platform Team:** TBD

---

For additional support or questions about the CI/CD pipeline, please create an issue in the repository or contact the development team.
