
# Deployment Instructions

## Local Testing
1. Build Docker image:
   ```bash
   docker build -t general-team .
   ```

2. Run locally:
   ```bash
   docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY general-team
   ```

## Kubernetes Deployment
1. Apply the manifest:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

2. Check deployment status:
   ```bash
   kubectl get pods -n elf-teams -l app=general-team
   ```

3. View logs:
   ```bash
   kubectl logs -n elf-teams -l app=general-team
   ```

## GitOps Deployment
1. Commit changes to git
2. Push to repository
3. ArgoCD will automatically deploy
