
# RAG Processor Team Deployment Instructions

## Local Testing
1. Build Docker image:
   ```bash
   docker build -t elf-automations/rag-processor-team:latest .
   ```

2. Run locally:
   ```bash
   docker run -p 8000:8000 \
     -e OPENAI_API_KEY=$OPENAI_API_KEY \
     -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
     -e SUPABASE_URL=$SUPABASE_URL \
     -e SUPABASE_KEY=$SUPABASE_KEY \
     -e NEO4J_URI=$NEO4J_URI \
     -e NEO4J_USER=$NEO4J_USER \
     -e NEO4J_PASSWORD=$NEO4J_PASSWORD \
     -e QDRANT_URL=$QDRANT_URL \
     elf-automations/rag-processor-team:latest
   ```

## Kubernetes Deployment
1. Create secrets (if not already created):
   ```bash
   kubectl create secret generic neo4j-credentials \
     --from-literal=uri=bolt://neo4j:7687 \
     --from-literal=username=neo4j \
     --from-literal=password=your-password \
     -n elf-teams

   kubectl create secret generic qdrant-credentials \
     --from-literal=url=http://qdrant:6333 \
     -n elf-teams
   ```

2. Apply the manifest:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

3. Check deployment status:
   ```bash
   kubectl get pods -n elf-teams -l app=rag-processor-team
   ```

4. View logs:
   ```bash
   kubectl logs -n elf-teams -l app=rag-processor-team
   ```

## Health Check Endpoints
- `/health` - Overall health status
- `/ready` - Readiness for processing
- `/capabilities` - Team capabilities
- `/status/{document_id}` - Document processing status

## GitOps Deployment
1. Commit changes to git
2. Push to repository
3. ArgoCD will automatically deploy

## Testing the Deployment
1. Process a document:
   ```bash
   curl -X POST http://rag-processor-team:8000/process \
     -H "Content-Type: application/json" \
     -d '{
       "document_id": "test-doc-1",
       "tenant_id": "tenant-1",
       "source_path": "/path/to/document.pdf"
     }'
   ```

2. Check processing status:
   ```bash
   curl http://rag-processor-team:8000/status/test-doc-1
   ```

3. Search documents:
   ```bash
   curl -X POST http://rag-processor-team:8000/search \
     -H "Content-Type: application/json" \
     -d '{
       "query": "contract terms",
       "tenant_id": "tenant-1",
       "limit": 10
     }'
   ```
