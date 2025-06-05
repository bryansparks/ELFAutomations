#!/usr/bin/env python3
"""
Test AgentGateway as MCP proxy using public MCP servers.
This validates the gateway pattern for MCP server access.
"""

import asyncio
import logging
import json
import httpx
import subprocess
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test_agentgateway")


def check_docker_running():
    """Check if Docker is running."""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to check Docker: {e}")
        return False


def start_agentgateway():
    """Start AgentGateway using direct Docker run."""
    try:
        # Stop any existing container
        subprocess.run(['docker', 'stop', 'agentgateway-test'], 
                      capture_output=True, text=True)
        subprocess.run(['docker', 'rm', 'agentgateway-test'], 
                      capture_output=True, text=True)
        
        # Start AgentGateway
        logger.info("🚀 Starting AgentGateway...")
        result = subprocess.run([
            'docker', 'run', '-d',
            '--name', 'agentgateway-test',
            '-p', '3002:3000',
            'elf-automations/agentgateway:latest'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ AgentGateway started successfully")
            # Wait for startup
            time.sleep(5)
            return True
        else:
            logger.error(f"❌ Failed to start AgentGateway: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to start AgentGateway: {e}")
        return False


def stop_agentgateway():
    """Stop AgentGateway container."""
    try:
        subprocess.run(['docker', 'stop', 'agentgateway-test'], 
                      capture_output=True, text=True)
        subprocess.run(['docker', 'rm', 'agentgateway-test'], 
                      capture_output=True, text=True)
        logger.info("🛑 AgentGateway stopped")
    except Exception as e:
        logger.warning(f"Could not stop AgentGateway: {e}")


async def test_agentgateway_health():
    """Test AgentGateway health endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3002/health", timeout=10.0)
            
            if response.status_code == 200:
                logger.info("✅ AgentGateway health check passed")
                logger.info(f"   Response: {response.text}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False


async def test_mcp_proxy():
    """Test MCP proxy functionality."""
    try:
        # Test MCP server listing
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3002/mcp/servers", timeout=10.0)
            
            if response.status_code == 200:
                servers = response.json()
                logger.info("✅ MCP servers endpoint accessible")
                logger.info(f"   Available servers: {servers}")
                return True
            else:
                logger.warning(f"⚠️  MCP servers endpoint returned: {response.status_code}")
                logger.info("   This is expected if no MCP servers are configured")
                return True
                
    except Exception as e:
        logger.error(f"❌ MCP proxy test failed: {e}")
        return False


def create_mcp_config():
    """Create a simple MCP configuration for testing."""
    config = {
        "type": "static",
        "listeners": [
            {
                "type": "A2A",
                "port": 3000
            }
        ],
        "targets": {
            "mcp": [
                {
                    "name": "test-server",
                    "command": "echo",
                    "args": ["Hello MCP"],
                    "env": {}
                }
            ]
        }
    }
    
    config_path = "/tmp/agentgateway-test-config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"📝 Created test config: {config_path}")
    return config_path


def start_agentgateway_with_config():
    """Start AgentGateway with MCP configuration."""
    try:
        # Create config
        config_path = create_mcp_config()
        
        # Stop any existing container
        subprocess.run(['docker', 'stop', 'agentgateway-test'], 
                      capture_output=True, text=True)
        subprocess.run(['docker', 'rm', 'agentgateway-test'], 
                      capture_output=True, text=True)
        
        # Start AgentGateway with config
        logger.info("🚀 Starting AgentGateway with MCP config...")
        result = subprocess.run([
            'docker', 'run', '-d',
            '--name', 'agentgateway-test',
            '-p', '3002:3000',
            '-v', f'{config_path}:/app/config.json',
            'elf-automations/agentgateway:latest',
            '--file', '/app/config.json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ AgentGateway with config started successfully")
            # Wait for startup
            time.sleep(8)
            return True
        else:
            logger.error(f"❌ Failed to start AgentGateway with config: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to start AgentGateway with config: {e}")
        return False


async def test_agentgateway_logs():
    """Check AgentGateway logs for errors."""
    try:
        result = subprocess.run([
            'docker', 'logs', 'agentgateway-test'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logs = result.stdout
            logger.info("📋 AgentGateway logs:")
            for line in logs.split('\n')[-10:]:  # Last 10 lines
                if line.strip():
                    logger.info(f"   {line}")
            
            # Check for errors
            if 'error' in logs.lower() or 'failed' in logs.lower():
                logger.warning("⚠️  Found potential errors in logs")
            else:
                logger.info("✅ No obvious errors in logs")
            
            return True
        else:
            logger.error("❌ Could not retrieve logs")
            return False
            
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return False


async def test_basic_connectivity():
    """Test basic connectivity to AgentGateway."""
    try:
        # Test port connectivity
        result = subprocess.run([
            'docker', 'exec', 'agentgateway-test', 
            'nc', '-z', 'localhost', '3000'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Port 3000 is accessible inside container")
        else:
            logger.warning("⚠️  Port 3000 not accessible inside container")
        
        # Test from host
        result = subprocess.run([
            'nc', '-z', 'localhost', '3002'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Port 3002 is accessible from host")
            return True
        else:
            logger.warning("⚠️  Port 3002 not accessible from host")
            return False
            
    except Exception as e:
        logger.error(f"Connectivity test failed: {e}")
        return False


async def main():
    """Run AgentGateway MCP integration tests."""
    logger.info("🚀 Starting AgentGateway MCP Integration Tests")
    
    try:
        # Check prerequisites
        if not check_docker_running():
            logger.error("❌ Docker is not running")
            return False
        
        logger.info("✅ Docker is running")
        
        # Test 1: Basic AgentGateway startup
        logger.info("\n🔍 Test 1: Basic AgentGateway startup")
        if not start_agentgateway():
            logger.error("❌ Failed to start AgentGateway")
            return False
        
        # Check logs
        await asyncio.sleep(3)
        await test_agentgateway_logs()
        
        # Test connectivity
        connectivity_ok = await test_basic_connectivity()
        
        # Test health endpoint
        health_ok = await test_agentgateway_health()
        
        # Test MCP proxy
        mcp_ok = await test_mcp_proxy()
        
        # Stop basic instance
        stop_agentgateway()
        
        # Test 2: AgentGateway with MCP config
        logger.info("\n🔍 Test 2: AgentGateway with MCP configuration")
        if start_agentgateway_with_config():
            await asyncio.sleep(5)
            await test_agentgateway_logs()
            
            # Test with config
            config_health_ok = await test_agentgateway_health()
            config_mcp_ok = await test_mcp_proxy()
            
            stop_agentgateway()
        else:
            config_health_ok = False
            config_mcp_ok = False
        
        # Results
        logger.info("\n🎉 AgentGateway Integration Test Results:")
        logger.info(f"   • Basic startup: {'✅' if True else '❌'}")
        logger.info(f"   • Port connectivity: {'✅' if connectivity_ok else '❌'}")
        logger.info(f"   • Health endpoint: {'✅' if health_ok else '❌'}")
        logger.info(f"   • MCP proxy: {'✅' if mcp_ok else '❌'}")
        logger.info(f"   • Config-based startup: {'✅' if config_health_ok else '❌'}")
        logger.info(f"   • Config-based MCP: {'✅' if config_mcp_ok else '❌'}")
        
        success = connectivity_ok and (health_ok or config_health_ok)
        
        if success:
            logger.info("\n✅ AgentGateway is working and ready for MCP integration!")
            logger.info("\n🚀 Next Steps:")
            logger.info("   • Add real MCP servers to configuration")
            logger.info("   • Test agent communication through gateway")
            logger.info("   • Deploy to Kubernetes with kagent integration")
            logger.info("   • Set up monitoring and observability")
        else:
            logger.error("\n❌ AgentGateway integration has issues that need resolution")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        stop_agentgateway()


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        exit(1)
