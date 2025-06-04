kagent Architecture Overview
Single kagent Controller (Not One Per Agent)
There is ONE kagent controller per Kubernetes cluster, not one controller per agent. Here's how it works:
yamlKubernetes_Cluster:
  kagent-controller: 1 instance (runs as deployment in kagent-system namespace)
    manages: ALL Agent CRDs across ALL namespaces
    
  Agent_CRDs: Many instances (one per agent type you deploy)
    examples:
      - sdr-agent (in sales-department namespace)
      - content-creator-agent (in marketing-department namespace)
      - sales-manager-agent (in sales-department namespace)
      - etc.
How kagent Controller Works
mermaidgraph TB
    subgraph "Kubernetes Control Plane"
        API[Kubernetes API Server]
        Scheduler[K8s Scheduler]
    end
    
    subgraph "kagent-system namespace"
        KC[kagent-controller]
        KC --> API
    end
    
    subgraph "sales-department namespace"
        SDR_CRD[SDR Agent CRD]
        SDR_Pods[SDR Agent Pods]
        Sales_CRD[Sales Manager CRD]
        Sales_Pods[Sales Manager Pods]
    end
    
    subgraph "marketing-department namespace"
        Content_CRD[Content Creator CRD]
        Content_Pods[Content Creator Pods]
    end
    
    KC -.-> SDR_CRD
    KC -.-> Sales_CRD
    KC -.-> Content_CRD
    
    SDR_CRD --> SDR_Pods
    Sales_CRD --> Sales_Pods
    Content_CRD --> Content_Pods
    
    Scheduler --> SDR_Pods
    Scheduler --> Sales_Pods
    Scheduler --> Content_Pods
Detailed kagent Flow
1. Single Controller, Multiple CRDs
yaml# The kagent controller deployment (ONE instance)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kagent-controller
  namespace: kagent-system
spec:
  replicas: 1  # Single controller instance
  selector:
    matchLabels:
      app: kagent-controller
  template:
    spec:
      containers:
      - name: controller
        image: kagent/controller:latest
        # This controller watches ALL Agent CRDs cluster-wide
2. Individual Agent CRDs
Each agent type gets its own CRD, but they're all managed by the same controller:
yaml# SDR Agent CRD (managed by the single kagent-controller)
apiVersion: kagent.dev/v1
kind: Agent
metadata:
  name: sdr-agent
  namespace: sales-department
spec:
  systemPrompt: "You are an SDR..."
  image: "elfautomations/sdr-agent:v1.0.0"
  replicas: 5
  # ... other config

---
# Content Creator Agent CRD (also managed by same kagent-controller)  
apiVersion: kagent.dev/v1
kind: Agent
metadata:
  name: content-creator-agent
  namespace: marketing-department
spec:
  systemPrompt: "You are a content creator..."
  image: "elfautomations/content-creator:v1.0.0"
  replicas: 2
  # ... other config
3. How Kubernetes Controls Agents
The flow is:
You create Agent CRD → kagent-controller watches → Creates K8s resources → K8s manages pods
Detailed process:

You deploy an Agent CRD:
bashkubectl apply -f sdr-agent.yaml

kagent-controller detects the new Agent CRD:

Watches for Agent resources across all namespaces
Receives event: "new Agent CRD created"


kagent-controller creates standard Kubernetes resources:
yaml# kagent-controller automatically creates these:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdr-agent
  namespace: sales-department
spec:
  replicas: 5  # From Agent CRD spec
  template:
    spec:
      containers:
      - name: sdr-agent
        image: "elfautomations/sdr-agent:v1.0.0"  # From Agent CRD
        # Additional config from Agent CRD

---
apiVersion: v1
kind: Service
metadata:
  name: sdr-agent
  namespace: sales-department

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sdr-agent-hpa
# ... etc

Standard Kubernetes takes over:

Kubernetes Deployment controller manages the pods
HPA controller handles scaling
Service controller manages networking
Scheduler places pods on nodes



Kubernetes Management Layers
yamlManagement_Layers:
  Layer_1_User_Interface:
    - "You define Agent CRDs (high-level agent specifications)"
    - "kubectl apply -f sdr-agent.yaml"
    
  Layer_2_kagent_Controller:
    - "Translates Agent CRDs into standard Kubernetes resources"
    - "Watches for Agent CRD changes and updates K8s resources accordingly"
    
  Layer_3_Kubernetes_Native:
    - "Standard K8s controllers manage the actual pods, services, scaling"
    - "Deployment controller, HPA controller, Service controller, etc."
    
  Layer_4_Container_Runtime:
    - "containerd/Docker runs your actual agent containers"
    - "Your CrewAI + A2A agent code runs here"
Benefits of This Architecture
1. Kubernetes-Native Management
yamlWhat_You_Get:
  - kubectl_works: "kubectl get agents, kubectl describe agent sdr-agent"
  - standard_monitoring: "Prometheus scrapes agent pods automatically"
  - standard_networking: "Kubernetes Services, Ingress, NetworkPolicies work"
  - standard_scaling: "HPA, VPA work with agent pods"
  - standard_troubleshooting: "kubectl logs, kubectl exec work on agent pods"
2. Abstraction Benefits
yamlAgent_CRD_Abstracts:
  - deployment_complexity: "Don't write Deployment YAML manually"
  - scaling_configuration: "Simple replicas vs complex HPA setup"
  - service_discovery: "Agent networking handled automatically"
  - monitoring_setup: "Automatic metrics and health check configuration"
3. Operational Simplicity
yamlOperations:
  scale_agent: "kubectl patch agent sdr-agent --patch '{\"spec\":{\"replicas\":10}}'"
  update_agent: "Edit Agent CRD, kagent-controller handles rolling update"
  monitor_agent: "Standard Kubernetes monitoring tools work"
  debug_agent: "kubectl logs deployment/sdr-agent"
Example: Scaling an Agent
Traditional Kubernetes Way:
bash# You'd need to update multiple resources
kubectl scale deployment sdr-agent --replicas=10
kubectl patch hpa sdr-agent --patch '...'
kubectl update service sdr-agent ...
# Update multiple related resources manually
kagent Way:
bash# Single command updates everything
kubectl patch agent sdr-agent --patch '{"spec":{"replicas":10}}'

# Or edit the Agent CRD
kubectl edit agent sdr-agent
# Change replicas: 5 to replicas: 10
# kagent-controller automatically updates Deployment, HPA, etc.
Agent CRD → Kubernetes Resources Mapping
When you create an Agent CRD, kagent-controller creates:
yamlAgent_CRD_Creates:
  Deployment:
    purpose: "Runs your agent pods"
    replicas: "From Agent CRD spec.replicas"
    image: "From Agent CRD spec.image"
    
  Service:
    purpose: "Network access to agent pods"
    ports: "Based on Agent CRD configuration"
    
  HorizontalPodAutoscaler:
    purpose: "Auto-scaling based on metrics"
    minReplicas: "From Agent CRD autoscaling config"
    maxReplicas: "From Agent CRD autoscaling config"
    
  ServiceMonitor:
    purpose: "Prometheus monitoring setup"
    metrics: "Automatic scraping of agent metrics"
    
  ConfigMap:
    purpose: "Agent configuration and prompts"
    data: "From Agent CRD systemPrompt and other config"
    
  Secret_References:
    purpose: "API keys and sensitive configuration"
    refs: "From Agent CRD tool and model configuration"
Summary
Key Points:

One kagent-controller manages all Agent CRDs across the cluster
Agent CRDs are specifications - you define what you want
kagent-controller translates Agent CRDs into standard Kubernetes resources
Standard Kubernetes controllers manage the actual pods, scaling, networking
You interact with high-level Agent CRDs, Kubernetes handles the low-level details

The beauty: You get all the benefits of Kubernetes (scaling, monitoring, networking, failure recovery) but with a simple, agent-focused interface. You don't need to understand Deployments, Services, HPAs - you just define agents and kagent handles the Kubernetes complexity.
This is why kagent provides "true Kubernetes-native" agent management while keeping the complexity hidden behind a clean agent-focused API.
