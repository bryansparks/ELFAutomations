#!/usr/bin/env python3
"""
Kubernetes Foundation Test Suite
Tests the base K8s infrastructure required for distributed agents.
"""

import asyncio
import time
from typing import List

from .test_runner import TestSuite, TestResult, TestStatus, run_command, wait_for_condition


class K8sFoundationTestSuite(TestSuite):
    """Test suite for Kubernetes foundation infrastructure."""
    
    def __init__(self):
        super().__init__("Kubernetes Foundation Infrastructure")
        
    async def run_tests(self) -> List[TestResult]:
        """Run all K8s foundation tests."""
        tests = [
            self.test_cluster_connectivity,
            self.test_minikube_status,
            self.test_docker_availability,
            self.test_kubectl_access,
            self.test_namespace_creation,
            self.test_rbac_permissions,
            self.test_crd_installation,
            self.test_kagent_controller,
            self.test_resource_quotas
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
                
        return self.results
        
    async def test_cluster_connectivity(self):
        """Test basic cluster connectivity."""
        success, stdout, stderr = await run_command(['kubectl', 'cluster-info'])
        if not success:
            raise Exception(f"Cluster not accessible: {stderr}")
            
        if 'running at' not in stdout.lower():
            raise Exception("Cluster info doesn't show running status")
            
    async def test_minikube_status(self):
        """Test minikube is running."""
        success, stdout, stderr = await run_command(['minikube', 'status'])
        if not success:
            raise Exception(f"Minikube not available: {stderr}")
            
        required_components = ['kubelet', 'apiserver', 'kubeconfig']
        for component in required_components:
            if component not in stdout.lower() or 'running' not in stdout.lower():
                raise Exception(f"Minikube component {component} not running")
                
    async def test_docker_availability(self):
        """Test Docker is available."""
        success, stdout, stderr = await run_command(['docker', 'ps'])
        if not success:
            raise Exception(f"Docker not available: {stderr}")
            
        # Test Docker can build images
        success, stdout, stderr = await run_command(['docker', 'version'])
        if not success:
            raise Exception(f"Docker version check failed: {stderr}")
            
    async def test_kubectl_access(self):
        """Test kubectl has proper access."""
        # Test basic kubectl commands
        commands = [
            ['kubectl', 'get', 'nodes'],
            ['kubectl', 'get', 'namespaces'],
            ['kubectl', 'auth', 'can-i', 'create', 'pods']
        ]
        
        for cmd in commands:
            success, stdout, stderr = await run_command(cmd)
            if not success:
                raise Exception(f"kubectl command failed: {' '.join(cmd)} - {stderr}")
                
    async def test_namespace_creation(self):
        """Test namespace creation and management."""
        test_namespace = "elf-test-namespace"
        
        # Create test namespace
        success, stdout, stderr = await run_command([
            'kubectl', 'create', 'namespace', test_namespace
        ])
        
        # If namespace already exists, that's fine
        if not success and 'already exists' not in stderr:
            raise Exception(f"Failed to create namespace: {stderr}")
            
        # Verify namespace exists
        success, stdout, stderr = await run_command([
            'kubectl', 'get', 'namespace', test_namespace
        ])
        if not success:
            raise Exception(f"Test namespace not found: {stderr}")
            
        # Clean up
        await run_command(['kubectl', 'delete', 'namespace', test_namespace])
        
    async def test_rbac_permissions(self):
        """Test RBAC permissions for agent operations."""
        permissions_to_test = [
            ('create', 'pods'),
            ('get', 'pods'),
            ('list', 'pods'),
            ('create', 'services'),
            ('get', 'services'),
            ('create', 'deployments'),
            ('get', 'deployments'),
            ('create', 'configmaps'),
            ('get', 'secrets')
        ]
        
        for action, resource in permissions_to_test:
            success, stdout, stderr = await run_command([
                'kubectl', 'auth', 'can-i', action, resource
            ])
            if not success or 'yes' not in stdout.lower():
                raise Exception(f"Missing permission: {action} {resource}")
                
    async def test_crd_installation(self):
        """Test Custom Resource Definitions are available."""
        # Check if kagent CRDs are installed
        success, stdout, stderr = await run_command([
            'kubectl', 'get', 'crd'
        ])
        if not success:
            raise Exception(f"Failed to get CRDs: {stderr}")
            
        # Look for kagent-related CRDs
        expected_crds = ['agents.kagent.dev', 'teams.kagent.dev']
        for crd in expected_crds:
            if crd not in stdout:
                # Try to find any kagent CRDs
                success, stdout, stderr = await run_command([
                    'kubectl', 'get', 'crd', '-o', 'name'
                ])
                if 'kagent' not in stdout:
                    raise Exception(f"kagent CRDs not installed. Expected: {expected_crds}")
                    
    async def test_kagent_controller(self):
        """Test kagent controller is running."""
        # Check if kagent controller is deployed
        success, stdout, stderr = await run_command([
            'kubectl', 'get', 'pods', '-A', '-l', 'app=kagent-controller'
        ])
        
        if not success:
            # Try alternative label
            success, stdout, stderr = await run_command([
                'kubectl', 'get', 'pods', '-A'
            ])
            if 'kagent' not in stdout:
                raise Exception("kagent controller not found in any namespace")
                
        # Check controller is running
        if 'Running' not in stdout:
            raise Exception("kagent controller not in Running state")
            
    async def test_resource_quotas(self):
        """Test resource availability for agent deployment."""
        # Check node resources
        success, stdout, stderr = await run_command([
            'kubectl', 'top', 'nodes'
        ])
        
        # If metrics server not available, skip this test
        if not success and 'metrics' in stderr.lower():
            return  # Skip resource quota test if metrics not available
            
        if not success:
            raise Exception(f"Failed to get node resources: {stderr}")
            
        # Check we have reasonable resources available
        success, stdout, stderr = await run_command([
            'kubectl', 'describe', 'nodes'
        ])
        if not success:
            raise Exception(f"Failed to describe nodes: {stderr}")
            
        # Basic check that we have some CPU and memory
        if 'cpu:' not in stdout.lower() or 'memory:' not in stdout.lower():
            raise Exception("Node resource information not available")


# Standalone test runner for this suite
async def main():
    """Run K8s foundation tests standalone."""
    from .test_runner import TestRunner
    
    runner = TestRunner()
    runner.add_suite(K8sFoundationTestSuite())
    
    success = await runner.run_all_tests()
    return success


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
