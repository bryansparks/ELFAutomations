"""
Kubernetes manifest generator for team deployment.
"""

from pathlib import Path
from typing import Any, Dict

from ...models import TeamSpecification
from ..base import BaseGenerator


class KubernetesGenerator(BaseGenerator):
    """Generates Kubernetes deployment manifests."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate Kubernetes deployment manifest.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        team_dir = Path(team_spec.name)
        k8s_dir = team_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        deployment_path = k8s_dir / "deployment.yaml"
        
        # Generate deployment manifest
        deployment_content = self._generate_deployment_manifest(team_spec)
        
        # Write file
        with open(deployment_path, "w") as f:
            f.write(deployment_content)
        
        return {
            "generated_files": [str(deployment_path)],
            "errors": []
        }
    
    def _generate_deployment_manifest(self, team_spec: TeamSpecification) -> str:
        """Generate Kubernetes deployment manifest."""
        # Resource calculations based on team size
        cpu_request = "100m" if len(team_spec.members) <= 3 else "200m"
        cpu_limit = "500m" if len(team_spec.members) <= 3 else "1000m"
        memory_request = "256Mi" if len(team_spec.members) <= 3 else "512Mi"
        memory_limit = "512Mi" if len(team_spec.members) <= 3 else "1Gi"
        
        return f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {team_spec.name}
  namespace: elf-teams
  labels:
    app: {team_spec.name}
    department: {team_spec.department}
    framework: {team_spec.framework.lower()}
    team-type: ai-agent-team
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {team_spec.name}
  template:
    metadata:
      labels:
        app: {team_spec.name}
        department: {team_spec.department}
        framework: {team_spec.framework.lower()}
    spec:
      containers:
      - name: {team_spec.name}
        image: elf-automations/{team_spec.name}:latest
        imagePullPolicy: Never  # For local development
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: TEAM_NAME
          value: "{team_spec.name}"
        - name: FRAMEWORK
          value: "{team_spec.framework}"
        - name: DEPARTMENT
          value: "{team_spec.department}"
        - name: LLM_PROVIDER
          value: "{team_spec.llm_provider}"
        - name: LLM_MODEL
          value: "{team_spec.llm_model}"
        - name: LOG_LEVEL
          value: "INFO"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-credentials
              key: openai-api-key
              optional: true
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-credentials
              key: anthropic-api-key
              optional: true
        - name: AGENTGATEWAY_URL
          value: "http://agentgateway-service:3003"
        - name: QDRANT_URL
          value: "http://qdrant-service:6333"
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: supabase-credentials
              key: url
        - name: SUPABASE_KEY
          valueFrom:
            secretKeyRef:
              name: supabase-credentials
              key: service-key
        resources:
          requests:
            cpu: {cpu_request}
            memory: {memory_request}
          limits:
            cpu: {cpu_limit}
            memory: {memory_limit}
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
      restartPolicy: Always
      serviceAccountName: {team_spec.name}-sa
---
apiVersion: v1
kind: Service
metadata:
  name: {team_spec.name}-service
  namespace: elf-teams
  labels:
    app: {team_spec.name}
spec:
  selector:
    app: {team_spec.name}
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  type: ClusterIP
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {team_spec.name}-sa
  namespace: elf-teams
  labels:
    app: {team_spec.name}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {team_spec.name}-role
  namespace: elf-teams
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {team_spec.name}-rolebinding
  namespace: elf-teams
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {team_spec.name}-role
subjects:
- kind: ServiceAccount
  name: {team_spec.name}-sa
  namespace: elf-teams
'''