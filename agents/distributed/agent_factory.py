#!/usr/bin/env python3
"""
Agent Factory Pattern - Complete Infrastructure Generator

Generates ALL required components for deploying a distributed CrewAI agent:
- kagent CRD
- Docker configuration  
- A2A infrastructure
- Kubernetes services
- Monitoring setup
- CI/CD configuration
"""

import os
import yaml
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AgentSpec:
    """Complete specification for a distributed agent"""
    agent_id: str
    role: str
    goal: str
    backstory: str
    department: str
    capabilities: List[str]
    tools: List[Dict[str, Any]]
    a2a_port: int
    health_port: int
    resources: Dict[str, Any]
    scaling: Dict[str, Any]
    llm_config: Dict[str, Any] = None
    api_keys: Dict[str, Any] = None
    cost_optimization: Dict[str, Any] = None
    agent_llm_config: Dict[str, Any] = None

class AgentFactory:
    """Factory for generating complete agent infrastructure"""
    
    def __init__(self, base_path: str = "/Users/bryansparks/projects/ELFAutomations"):
        self.base_path = Path(base_path)
        self.k8s_path = self.base_path / "agents" / "distributed" / "k8s"
        self.docker_path = self.base_path / "agents" / "distributed"
        
    def create_complete_agent(self, spec: AgentSpec) -> Dict[str, str]:
        """Create ALL infrastructure components for an agent"""
        components = {}
        
        # 1. kagent CRD
        components['kagent_crd'] = self._generate_kagent_crd(spec)
        
        # 2. Kubernetes Service
        components['k8s_service'] = self._generate_k8s_service(spec)
        
        # 3. ConfigMap
        components['configmap'] = self._generate_configmap(spec)
        
        # 4. ServiceMonitor
        components['service_monitor'] = self._generate_service_monitor(spec)
        
        # 5. NetworkPolicy
        components['network_policy'] = self._generate_network_policy(spec)
        
        # 6. API Keys Secret (if needed)
        if spec.api_keys:
            components['api_keys_secret'] = self._generate_api_keys_secret(spec)
        
        # 7. Team CRD
        components['team_crd'] = self._generate_team_crd(spec)
        
        return components
    
    def _generate_kagent_crd(self, spec: AgentSpec) -> str:
        """Generate kagent CRD YAML matching the actual CRD schema"""
        crd = {
            'apiVersion': 'kagent.dev/v1alpha1',
            'kind': 'Agent',
            'metadata': {
                'name': spec.agent_id,
                'namespace': 'elf-automations',
                'labels': {
                    'department': spec.department,
                    'role': spec.role.lower().replace(' ', '-'),
                    'agent-type': 'distributed-crewai',
                    'version': 'v1.0.0'
                }
            },
            'spec': {
                'description': f'{spec.role} - {spec.goal}',
                'systemMessage': f'You are a {spec.role}. {spec.backstory}',
                'modelConfig': 'default-model-config'
            }
        }
        return yaml.dump(crd, default_flow_style=False)
    
    def _generate_k8s_service(self, spec: AgentSpec) -> str:
        """Generate Kubernetes Service YAML"""
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{spec.agent_id}-service",
                'namespace': 'elf-automations',
                'labels': {
                    'app': spec.agent_id,
                    'department': spec.department
                }
            },
            'spec': {
                'selector': {
                    'app': spec.agent_id
                },
                'ports': [
                    {
                        'name': 'a2a',
                        'port': spec.a2a_port,
                        'targetPort': spec.a2a_port,
                        'protocol': 'TCP'
                    },
                    {
                        'name': 'health',
                        'port': spec.health_port,
                        'targetPort': spec.health_port,
                        'protocol': 'TCP'
                    }
                ],
                'type': 'ClusterIP'
            }
        }
        return yaml.dump(service, default_flow_style=False)
    
    def _generate_configmap(self, spec: AgentSpec) -> str:
        """Generate ConfigMap YAML"""
        config = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f"{spec.agent_id}-config",
                'namespace': 'elf-automations'
            },
            'data': {
                'agent.yaml': yaml.dump({
                    'agent_id': spec.agent_id,
                    'role': spec.role,
                    'department': spec.department,
                    'capabilities': spec.capabilities,
                    'a2a': {
                        'port': spec.a2a_port,
                        'discovery_endpoint': 'http://a2a-discovery-service:8080'
                    }
                })
            }
        }
        return yaml.dump(config, default_flow_style=False)
    
    def _generate_service_monitor(self, spec: AgentSpec) -> str:
        """Generate ServiceMonitor for Prometheus"""
        monitor = {
            'apiVersion': 'monitoring.coreos.com/v1',
            'kind': 'ServiceMonitor',
            'metadata': {
                'name': f"{spec.agent_id}-monitor",
                'namespace': 'elf-automations'
            },
            'spec': {
                'selector': {
                    'matchLabels': {
                        'app': spec.agent_id
                    }
                },
                'endpoints': [
                    {
                        'port': 'health',
                        'path': '/metrics',
                        'interval': '30s'
                    }
                ]
            }
        }
        return yaml.dump(monitor, default_flow_style=False)
    
    def _generate_network_policy(self, spec: AgentSpec) -> str:
        """Generate NetworkPolicy for security"""
        policy = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'NetworkPolicy',
            'metadata': {
                'name': f"{spec.agent_id}-netpol",
                'namespace': 'elf-automations'
            },
            'spec': {
                'podSelector': {
                    'matchLabels': {
                        'app': spec.agent_id
                    }
                },
                'policyTypes': ['Ingress', 'Egress'],
                'ingress': [
                    {
                        'from': [
                            {
                                'namespaceSelector': {
                                    'matchLabels': {
                                        'name': 'elf-automations'
                                    }
                                }
                            }
                        ],
                        'ports': [
                            {
                                'protocol': 'TCP',
                                'port': spec.a2a_port
                            },
                            {
                                'protocol': 'TCP',
                                'port': spec.health_port
                            }
                        ]
                    }
                ]
            }
        }
        return yaml.dump(policy, default_flow_style=False)
    
    def _generate_api_keys_secret(self, spec: AgentSpec) -> str:
        """Generate Secret for API keys"""
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': f"{spec.agent_id}-api-keys",
                'namespace': 'elf-automations'
            },
            'type': 'Opaque',
            'data': {
                'api_key': spec.api_keys.get('api_key', ''),
                'api_secret': spec.api_keys.get('api_secret', '')
            }
        }
        return yaml.dump(secret, default_flow_style=False)
    
    def _generate_team_crd(self, spec: AgentSpec) -> str:
        """Generate Team CRD YAML for the agent"""
        team = {
            'apiVersion': 'kagent.dev/v1alpha1',
            'kind': 'Team',
            'metadata': {
                'name': spec.agent_id,
                'namespace': 'elf-automations',
                'labels': {
                    'app': 'elf-automations',
                    'component': 'team',
                    'department': spec.department,
                    'role': spec.role.lower().replace(' ', '-'),
                    'agent-type': 'distributed-crewai',
                    'version': 'v1.0.0'
                }
            },
            'spec': {
                'description': f'Team for {spec.role} - {spec.goal}',
                'maxTurns': 10,
                'modelConfig': 'default-model-config',
                'participants': [spec.agent_id],
                'roundRobinTeamConfig': {},
                'terminationCondition': {
                    'maxMessageTermination': {
                        'maxMessages': 20
                    }
                }
            }
        }
        return yaml.dump(team, default_flow_style=False)
    
    def _generate_llm_env_vars(self, spec: AgentSpec) -> List[Dict[str, str]]:
        """Generate LLM-specific environment variables"""
        env_vars = []
        
        # Get agent-specific LLM config or use defaults
        agent_llm = getattr(spec, 'agent_llm_config', None)
        if agent_llm:
            env_vars.extend([
                {'name': 'LLM_PROVIDER', 'value': agent_llm.get('provider', 'openai')},
                {'name': 'LLM_MODEL', 'value': agent_llm.get('model', 'gpt-4o-mini')},
                {'name': 'LLM_TEMPERATURE', 'value': str(agent_llm.get('temperature', 0.3))},
                {'name': 'LLM_MAX_TOKENS', 'value': str(agent_llm.get('max_tokens', 1500))}
            ])
        elif spec.llm_config:
            # Use crew-level defaults
            default_provider = spec.llm_config.get('default_provider', 'openai')
            env_vars.extend([
                {'name': 'LLM_PROVIDER', 'value': default_provider},
                {'name': 'LLM_MODEL', 'value': 'gpt-4o-mini'},
                {'name': 'LLM_TEMPERATURE', 'value': '0.3'},
                {'name': 'LLM_MAX_TOKENS', 'value': '1500'}
            ])
        
        return env_vars
    
    def _generate_env_from(self, spec: AgentSpec) -> List[Dict[str, Any]]:
        """Generate envFrom for API key secrets"""
        env_from = []
        
        if spec.api_keys:
            secret_name = spec.api_keys.get('secret_name', 'llm-api-keys')
            env_from.append({
                'secretRef': {
                    'name': secret_name,
                    'optional': False
                }
            })
        
        return env_from
    
    def _generate_llm_config(self, spec: AgentSpec) -> Dict[str, Any]:
        """Generate LLM configuration section for kagent CRD"""
        llm_config = {}
        
        # Get agent-specific LLM config
        agent_llm = getattr(spec, 'agent_llm_config', None)
        if agent_llm:
            llm_config = {
                'provider': agent_llm.get('provider', 'openai'),
                'model': agent_llm.get('model', 'gpt-4o-mini'),
                'temperature': agent_llm.get('temperature', 0.3),
                'max_tokens': agent_llm.get('max_tokens', 1500),
                'reasoning': agent_llm.get('reasoning', 'Default LLM configuration')
            }
        elif spec.llm_config:
            # Use crew-level defaults
            llm_config = {
                'provider': spec.llm_config.get('default_provider', 'openai'),
                'model': 'gpt-4o-mini',
                'temperature': 0.3,
                'max_tokens': 1500,
                'reasoning': 'Crew-level default configuration'
            }
        
        return llm_config
    
    def save_agent_infrastructure(self, spec: AgentSpec):
        """Save all generated components to files"""
        components = self.create_complete_agent(spec)
        
        # Save kagent CRD
        kagent_file = self.k8s_path / f"{spec.agent_id}-kagent.yaml"
        with open(kagent_file, 'w') as f:
            f.write(components['kagent_crd'])
        
        # Save service
        service_file = self.k8s_path / f"{spec.agent_id}-service.yaml"
        with open(service_file, 'w') as f:
            f.write(components['k8s_service'])
        
        # Save configmap
        config_file = self.k8s_path / f"{spec.agent_id}-configmap.yaml"
        with open(config_file, 'w') as f:
            f.write(components['configmap'])
        
        # Save ServiceMonitor (Prometheus monitoring)
        monitor_file = self.k8s_path / f"{spec.agent_id}-monitor.yaml"
        with open(monitor_file, 'w') as f:
            f.write(components['service_monitor'])
        
        # Save network policy
        netpol_file = self.k8s_path / f"{spec.agent_id}-netpol.yaml"
        with open(netpol_file, 'w') as f:
            f.write(components['network_policy'])
        
        # Save API keys secret
        if 'api_keys_secret' in components:
            secret_file = self.k8s_path / f"{spec.agent_id}-api-keys.yaml"
            with open(secret_file, 'w') as f:
                f.write(components['api_keys_secret'])
        
        # Save Team CRD
        team_file = self.k8s_path / f"{spec.agent_id}-team.yaml"
        with open(team_file, 'w') as f:
            f.write(components['team_crd'])
        
        print(f"✅ Saved infrastructure for {spec.agent_id}")
    
    def save_infrastructure(self, agent_specs: List[AgentSpec], crew_name: str):
        """Save infrastructure for all agents in a crew"""
        print(f"💾 Saving infrastructure for crew: {crew_name}")
        
        # Ensure k8s directory exists
        self.k8s_path.mkdir(exist_ok=True)
        
        # Save infrastructure for each agent
        for spec in agent_specs:
            self.save_agent_infrastructure(spec)
        
        print(f"✅ Saved infrastructure for {len(agent_specs)} agents in crew '{crew_name}'")

# Port allocation system
class PortManager:
    """Manages unique port allocation for agents"""
    
    def __init__(self, base_port: int = 8090):
        self.base_port = base_port
        self.allocated_ports = set()
    
    def allocate_ports(self, agent_id: str) -> tuple[int, int]:
        """Allocate A2A and health ports for an agent"""
        # Simple allocation: increment by 10 for each agent
        agent_number = len(self.allocated_ports)
        a2a_port = self.base_port + (agent_number * 10)
        health_port = a2a_port + 1
        
        self.allocated_ports.add((a2a_port, health_port))
        return a2a_port, health_port

if __name__ == "__main__":
    # Example usage
    factory = AgentFactory()
    port_manager = PortManager()
    
    # Create Sales Manager agent
    a2a_port, health_port = port_manager.allocate_ports("sales-manager")
    
    sales_manager_spec = AgentSpec(
        agent_id="sales-manager",
        role="Sales Manager",
        goal="Lead and coordinate sales team activities, optimize sales processes, and achieve revenue targets",
        backstory="You are an experienced Sales Manager with expertise in team leadership, process optimization, and revenue growth",
        department="sales",
        capabilities=["team_leadership", "sales_optimization", "revenue_forecasting"],
        tools=[
            {
                "type": "McpServer",
                "mcpServer": {
                    "toolServer": "crm-connector",
                    "toolNames": ["update_opportunity", "get_pipeline"]
                }
            }
        ],
        a2a_port=a2a_port,
        health_port=health_port,
        resources={
            "requests": {"memory": "512Mi", "cpu": "250m"},
            "limits": {"memory": "1Gi", "cpu": "500m"}
        },
        scaling={
            "replicas": 1,
            "minReplicas": 1,
            "maxReplicas": 2,
            "targetCPU": 70
        },
        llm_config={
            "model": "gpt-3.5-turbo",
            "api_key": "YOUR_API_KEY",
            "api_secret": "YOUR_API_SECRET"
        },
        api_keys={
            "api_key": "YOUR_API_KEY",
            "api_secret": "YOUR_API_SECRET"
        }
    )
    
    factory.save_agent_infrastructure(sales_manager_spec)
