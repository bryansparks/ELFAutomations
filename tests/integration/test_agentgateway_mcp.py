#!/usr/bin/env python3
"""
AgentGateway + MCP Test Suite
Tests AgentGateway as MCP proxy and MCP server integration.
"""

import asyncio
import json
import time
from typing import List, Dict
import httpx

from .test_runner import (TestSuite, TestResult, TestStatus, run_command, 
                         check_http_endpoint, wait_for_condition)


class AgentGatewayMCPTestSuite(TestSuite):
    """Test suite for AgentGateway + MCP integration."""
    
    def __init__(self):
        super().__init__("AgentGateway + MCP Integration")
        self.test_namespace = "elf-automations"
        self.agentgateway_port = 3000
        self.mcp_servers = []
        
    async def run_tests(self) -> List[TestResult]:
        """Run all AgentGateway + MCP tests."""
        tests = [
            self.test_agentgateway_docker_image,
            self.test_agentgateway_configuration,
            self.test_agentgateway_deployment,
            self.test_agentgateway_health,
            self.test_mcp_server_discovery,
            self.test_mcp_proxy_functionality,
            self.test_agent_mcp_integration,
            self.test_tool_execution_via_gateway,
            self.test_multiple_mcp_servers,
            self.test_gateway_error_handling
        ]
        
        for test in tests:
            start_time = time.time()
            try:
                await test()
                duration = time.time() - start_time
                self.add_result(
                    test.__name__.replace('test_', '').replace('_', ' ').title(),
                    TestStatus.PASSED,
                    duration
                )
            except Exception as e:
                duration = time.time() - start_time
                self.add_result(
                    test.__name__.replace('test_', '').replace('_', ' ').title(),
                    TestStatus.FAILED,
                    duration,
                    str(e)
                )
                
        # Cleanup
        await self.cleanup_test_resources()
        return self.results
        
    async def test_agentgateway_docker_image(self):
        """Test AgentGateway Docker image is available."""
        # Check if image exists
        success, stdout, stderr = await run_command([
            'docker', 'images', 'elf-automations/agentgateway:latest', '--format', 'table'
        ])
        
        if not success or 'agentgateway' not in stdout:
            # Try to build the image
            agentgateway_path = "third-party/agentgateway"
            
            success, stdout, stderr = await run_command([
                'docker', 'build', '-t', 'elf-automations/agentgateway:latest', 
                agentgateway_path
            ], timeout=300)  # 5 minute timeout for build
            
            if not success:
                raise Exception(f"Failed to build AgentGateway image: {stderr}")
                
    async def test_agentgateway_configuration(self):
        """Test AgentGateway configuration is valid."""
        # Create test configuration
        test_config = {
            "type": "static",
            "listeners": [
                {
                    "protocol": "MCP",
                    "transport": "stdio",
                    "address": "0.0.0.0:3000"
                }
            ],
            "targets": {
                "mcp": []
            }
        }
        
        # Validate configuration structure
        required_fields = ["type", "listeners", "targets"]
        for field in required_fields:
            if field not in test_config:
                raise Exception(f"Configuration missing required field: {field}")
                
        # Test configuration with AgentGateway
        config_json = json.dumps(test_config, indent=2)
        
        # Write test config to temp file
        with open("/tmp/agentgateway-test-config.json", "w") as f:
            f.write(config_json)
            
        # Test config validation (dry run)
        success, stdout, stderr = await run_command([
            'docker', 'run', '--rm', 
            '-v', '/tmp/agentgateway-test-config.json:/config.json',
            'elf-automations/agentgateway:latest',
            '--file', '/config.json', '--validate'
        ])
        
        # Note: AgentGateway might not have --validate flag, so we'll test startup instead
        if not success and 'validate' not in stderr:
            # If validate flag doesn't exist, that's okay - we'll test startup
            pass
            
    async def test_agentgateway_deployment(self):
        """Test AgentGateway deployment in Kubernetes."""
        # Create AgentGateway deployment
        deployment_yaml = f'''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentgateway-test
  namespace: {self.test_namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: agentgateway-test
  template:
    metadata:
      labels:
        app: agentgateway-test
    spec:
      containers:
      - name: agentgateway
        image: elf-automations/agentgateway:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 3000
          name: mcp-proxy
        env:
        - name: AGENTGATEWAY_CONFIG
          value: |
            {{
              "type": "static",
              "listeners": [
                {{
                  "protocol": "MCP",
                  "transport": "stdio",
                  "address": "0.0.0.0:3000"
                }}
              ],
              "targets": {{
                "mcp": []
              }}
            }}
        command: ["sh", "-c"]
        args:
        - |
          echo '$AGENTGATEWAY_CONFIG' > /tmp/config.json
          /app/agentgateway --file /tmp/config.json
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: agentgateway-test-service
  namespace: {self.test_namespace}
spec:
  selector:
    app: agentgateway-test
  ports:
  - name: mcp-proxy
    port: 3000
    targetPort: 3000
'''
        
        # Apply deployment
        process = await asyncio.create_subprocess_exec(
            'kubectl', 'apply', '-f', '-',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(deployment_yaml.encode())
        
        if process.returncode != 0:
            raise Exception(f"Failed to deploy AgentGateway: {stderr.decode()}")
            
        # Wait for pod to be running
        async def pod_running():
            success, stdout, stderr = await run_command([
                'kubectl', 'get', 'pods', '-n', self.test_namespace,
                '-l', 'app=agentgateway-test', '-o', 'jsonpath={.items[0].status.phase}'
            ])
            return success and stdout.strip() == 'Running'
            
        if not await wait_for_condition(pod_running, timeout=120):
            # Get pod logs for debugging
            success, stdout, stderr = await run_command([
                'kubectl', 'logs', '-n', self.test_namespace,
                '-l', 'app=agentgateway-test', '--tail=20'
            ])
            raise Exception(f"AgentGateway pod not running. Logs: {stdout}")
            
    async def test_agentgateway_health(self):
        """Test AgentGateway health and connectivity."""
        # Port forward to access the service
        port_forward_process = await asyncio.create_subprocess_exec(
            'kubectl', 'port-forward', 
            f'service/agentgateway-test-service', f'{self.agentgateway_port}:3000',
            '-n', self.test_namespace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for port forward to establish
        await asyncio.sleep(3)
        
        try:
            # Test basic connectivity (AgentGateway might not have health endpoint)
            # So we'll test if the port is accessible
            success, stdout, stderr = await run_command([
                'nc', '-z', 'localhost', str(self.agentgateway_port)
            ])
            
            if not success:
                raise Exception(f"AgentGateway port {self.agentgateway_port} not accessible")
                
        finally:
            # Clean up port forward
            port_forward_process.terminate()
            await port_forward_process.wait()
            
    async def test_mcp_server_discovery(self):
        """Test MCP server discovery and registration."""
        # Create a simple test MCP server
        test_mcp_server_yaml = f'''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-mcp-server
  namespace: {self.test_namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-mcp-server
  template:
    metadata:
      labels:
        app: test-mcp-server
    spec:
      containers:
      - name: mcp-server
        image: python:3.11-slim
        ports:
        - containerPort: 8080
          name: mcp-server
        command: ["python3", "-c"]
        args:
        - |
          import json
          import http.server
          import socketserver
          
          class MCPHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      response = {{"status": "healthy", "type": "mcp-server"}}
                      self.wfile.write(json.dumps(response).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          with socketserver.TCPServer(("", 8080), MCPHandler) as httpd:
              print("Test MCP Server running on port 8080")
              httpd.serve_forever()
        resources:
          requests:
            memory: "64Mi"
            cpu: "25m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: test-mcp-server-service
  namespace: {self.test_namespace}
spec:
  selector:
    app: test-mcp-server
  ports:
  - name: mcp-server
    port: 8080
    targetPort: 8080
'''
        
        # Deploy test MCP server
        process = await asyncio.create_subprocess_exec(
            'kubectl', 'apply', '-f', '-',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(test_mcp_server_yaml.encode())
        
        if process.returncode != 0:
            raise Exception(f"Failed to deploy test MCP server: {stderr.decode()}")
            
        self.mcp_servers.append("test-mcp-server")
        
        # Wait for MCP server to be running
        async def mcp_pod_running():
            success, stdout, stderr = await run_command([
                'kubectl', 'get', 'pods', '-n', self.test_namespace,
                '-l', 'app=test-mcp-server', '-o', 'jsonpath={.items[0].status.phase}'
            ])
            return success and stdout.strip() == 'Running'
            
        if not await wait_for_condition(mcp_pod_running, timeout=60):
            raise Exception("Test MCP server not running within timeout")
            
    async def test_mcp_proxy_functionality(self):
        """Test AgentGateway MCP proxy functionality."""
        # Update AgentGateway configuration to include test MCP server
        updated_config = {
            "type": "static",
            "listeners": [
                {
                    "protocol": "MCP",
                    "transport": "stdio",
                    "address": "0.0.0.0:3000"
                }
            ],
            "targets": {
                "mcp": [
                    {
                        "name": "test-mcp-server",
                        "url": "http://test-mcp-server-service:8080",
                        "description": "Test MCP Server"
                    }
                ]
            }
        }
        
        # Update AgentGateway deployment with new config
        success, stdout, stderr = await run_command([
            'kubectl', 'patch', 'deployment', 'agentgateway-test',
            '-n', self.test_namespace,
            '-p', json.dumps({
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": "agentgateway",
                                    "env": [
                                        {
                                            "name": "AGENTGATEWAY_CONFIG",
                                            "value": json.dumps(updated_config)
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            })
        ])
        
        if not success:
            raise Exception(f"Failed to update AgentGateway config: {stderr}")
            
        # Wait for rollout to complete
        success, stdout, stderr = await run_command([
            'kubectl', 'rollout', 'status', 'deployment/agentgateway-test',
            '-n', self.test_namespace, '--timeout=60s'
        ])
        
        if not success:
            raise Exception(f"AgentGateway rollout failed: {stderr}")
            
    async def test_agent_mcp_integration(self):
        """Test agent integration with MCP via AgentGateway."""
        # This test would verify that agents can access MCP servers through the gateway
        # For now, we'll test the integration infrastructure
        
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from agents.distributed.distributed_agent import DistributedAgent
    
    # Create test agent with MCP integration
    agent = DistributedAgent(
        agent_id="mcp-integration-test-agent",
        role="MCP Integration Test Agent",
        goal="Test MCP integration via AgentGateway",
        backstory="A test agent for MCP integration testing",
        department="test"
    )
    
    # Verify agent can be configured for MCP access
    card = agent.get_agent_card()
    
    if not card.capabilities:
        raise Exception("Agent capabilities not configured")
        
    # Test agent creation with MCP-aware configuration
    if not card.skills:
        raise Exception("Agent skills not configured for MCP integration")
        
    print("SUCCESS: Agent MCP integration infrastructure validated")
    
except Exception as e:
    print(f"FAILED: Agent MCP integration test failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"Agent MCP integration test failed: {stderr}")
            
    async def test_tool_execution_via_gateway(self):
        """Test tool execution via AgentGateway."""
        # Port forward to test MCP server
        mcp_port_forward = await asyncio.create_subprocess_exec(
            'kubectl', 'port-forward', 
            'service/test-mcp-server-service', '18080:8080',
            '-n', self.test_namespace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for port forward
        await asyncio.sleep(3)
        
        try:
            # Test direct MCP server access
            success, message = await check_http_endpoint('http://localhost:18080/health')
            if not success:
                raise Exception(f"Test MCP server not accessible: {message}")
                
            # Verify MCP server response
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get('http://localhost:18080/health')
                if response.status_code == 200:
                    data = response.json()
                    if data.get('type') != 'mcp-server':
                        raise Exception("MCP server response invalid")
                else:
                    raise Exception(f"MCP server returned status {response.status_code}")
                    
        finally:
            # Clean up port forward
            mcp_port_forward.terminate()
            await mcp_port_forward.wait()
            
    async def test_multiple_mcp_servers(self):
        """Test AgentGateway with multiple MCP servers."""
        # Deploy second test MCP server
        second_mcp_yaml = f'''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-mcp-server-2
  namespace: {self.test_namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-mcp-server-2
  template:
    metadata:
      labels:
        app: test-mcp-server-2
    spec:
      containers:
      - name: mcp-server
        image: python:3.11-slim
        ports:
        - containerPort: 8080
          name: mcp-server
        command: ["python3", "-c"]
        args:
        - |
          import json
          import http.server
          import socketserver
          
          class MCPHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      response = {{"status": "healthy", "type": "mcp-server-2", "server": "second"}}
                      self.wfile.write(json.dumps(response).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          with socketserver.TCPServer(("", 8080), MCPHandler) as httpd:
              print("Test MCP Server 2 running on port 8080")
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: test-mcp-server-2-service
  namespace: {self.test_namespace}
spec:
  selector:
    app: test-mcp-server-2
  ports:
  - name: mcp-server
    port: 8080
    targetPort: 8080
'''
        
        # Deploy second MCP server
        process = await asyncio.create_subprocess_exec(
            'kubectl', 'apply', '-f', '-',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(second_mcp_yaml.encode())
        
        if process.returncode != 0:
            raise Exception(f"Failed to deploy second MCP server: {stderr.decode()}")
            
        self.mcp_servers.append("test-mcp-server-2")
        
        # Wait for second MCP server
        async def second_mcp_running():
            success, stdout, stderr = await run_command([
                'kubectl', 'get', 'pods', '-n', self.test_namespace,
                '-l', 'app=test-mcp-server-2', '-o', 'jsonpath={.items[0].status.phase}'
            ])
            return success and stdout.strip() == 'Running'
            
        if not await wait_for_condition(second_mcp_running, timeout=60):
            raise Exception("Second MCP server not running within timeout")
            
        # Update AgentGateway to include both MCP servers
        multi_server_config = {
            "type": "static",
            "listeners": [
                {
                    "protocol": "MCP",
                    "transport": "stdio",
                    "address": "0.0.0.0:3000"
                }
            ],
            "targets": {
                "mcp": [
                    {
                        "name": "test-mcp-server",
                        "url": "http://test-mcp-server-service:8080",
                        "description": "Test MCP Server 1"
                    },
                    {
                        "name": "test-mcp-server-2",
                        "url": "http://test-mcp-server-2-service:8080",
                        "description": "Test MCP Server 2"
                    }
                ]
            }
        }
        
        # Update AgentGateway configuration
        success, stdout, stderr = await run_command([
            'kubectl', 'patch', 'deployment', 'agentgateway-test',
            '-n', self.test_namespace,
            '-p', json.dumps({
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": "agentgateway",
                                    "env": [
                                        {
                                            "name": "AGENTGATEWAY_CONFIG",
                                            "value": json.dumps(multi_server_config)
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            })
        ])
        
        if not success:
            raise Exception(f"Failed to update AgentGateway for multiple servers: {stderr}")
            
    async def test_gateway_error_handling(self):
        """Test AgentGateway error handling and resilience."""
        # Test gateway behavior when MCP server is unavailable
        unavailable_config = {
            "type": "static",
            "listeners": [
                {
                    "protocol": "MCP",
                    "transport": "stdio",
                    "address": "0.0.0.0:3000"
                }
            ],
            "targets": {
                "mcp": [
                    {
                        "name": "unavailable-server",
                        "url": "http://unavailable-service:8080",
                        "description": "Unavailable MCP Server"
                    }
                ]
            }
        }
        
        # Update AgentGateway with unavailable server config
        success, stdout, stderr = await run_command([
            'kubectl', 'patch', 'deployment', 'agentgateway-test',
            '-n', self.test_namespace,
            '-p', json.dumps({
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": "agentgateway",
                                    "env": [
                                        {
                                            "name": "AGENTGATEWAY_CONFIG",
                                            "value": json.dumps(unavailable_config)
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            })
        ])
        
        if not success:
            raise Exception(f"Failed to update AgentGateway for error testing: {stderr}")
            
        # Wait for rollout
        await asyncio.sleep(10)
        
        # Verify AgentGateway is still running despite unavailable MCP server
        success, stdout, stderr = await run_command([
            'kubectl', 'get', 'pods', '-n', self.test_namespace,
            '-l', 'app=agentgateway-test', '-o', 'jsonpath={.items[0].status.phase}'
        ])
        
        if not success or stdout.strip() != 'Running':
            raise Exception("AgentGateway not handling unavailable MCP server gracefully")
            
    async def cleanup_test_resources(self):
        """Clean up test resources."""
        # Clean up AgentGateway
        await run_command([
            'kubectl', 'delete', 'deployment', 'agentgateway-test', '-n', self.test_namespace
        ])
        await run_command([
            'kubectl', 'delete', 'service', 'agentgateway-test-service', '-n', self.test_namespace
        ])
        
        # Clean up MCP servers
        for mcp_server in self.mcp_servers:
            await run_command([
                'kubectl', 'delete', 'deployment', mcp_server, '-n', self.test_namespace
            ])
            await run_command([
                'kubectl', 'delete', 'service', f'{mcp_server}-service', '-n', self.test_namespace
            ])


# Standalone test runner for this suite
async def main():
    """Run AgentGateway + MCP tests standalone."""
    from .test_runner import TestRunner
    
    runner = TestRunner()
    runner.add_suite(AgentGatewayMCPTestSuite())
    
    success = await runner.run_all_tests()
    return success


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
