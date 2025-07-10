"""
MCP Server Discovery Service

Handles discovery of MCP servers from multiple sources:
1. AgentGateway configuration
2. Local MCP configuration files
3. K8s ConfigMaps
4. Environment variables
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


class MCPServerInfo:
    """Information about an MCP server"""

    def __init__(
        self,
        name: str,
        protocol: str = "stdio",
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        endpoint: Optional[str] = None,
        tools: Optional[List[str]] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.protocol = protocol  # stdio, http, sse
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.endpoint = endpoint  # For HTTP/SSE servers
        self.tools = tools or []
        self.description = description

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "protocol": self.protocol,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "endpoint": self.endpoint,
            "tools": self.tools,
            "description": self.description,
        }


class MCPDiscovery:
    """Discovers available MCP servers from various sources"""

    def __init__(
        self,
        config_paths: Optional[List[str]] = None,
        k8s_namespace: str = "elf-automations",
        use_agentgateway: bool = True,
    ):
        """
        Initialize MCP Discovery

        Args:
            config_paths: Additional paths to search for MCP configs
            k8s_namespace: Kubernetes namespace to search
            use_agentgateway: Whether to query AgentGateway for servers
        """
        self.config_paths = config_paths or []
        self.k8s_namespace = k8s_namespace
        self.use_agentgateway = use_agentgateway

        # Add default config paths
        self.config_paths.extend(
            [
                "/config/mcp_config.json",
                "/config/agentgateway/config.json",
                str(Path.home() / ".config" / "elf" / "mcp_config.json"),
                "config/mcp_config.json",
                "config/agentgateway/config.json",
            ]
        )

        self._servers: Dict[str, MCPServerInfo] = {}

    def discover_all(self) -> Dict[str, MCPServerInfo]:
        """Discover all available MCP servers"""
        logger.info("Starting MCP server discovery...")

        # Clear previous discoveries
        self._servers.clear()

        # Discover from various sources
        self._discover_from_files()
        self._discover_from_env()
        self._discover_from_k8s()
        self._discover_from_agentgateway()

        logger.info(
            f"Discovered {len(self._servers)} MCP servers: {list(self._servers.keys())}"
        )
        return self._servers

    def _discover_from_files(self):
        """Discover MCP servers from configuration files"""
        for config_path in self.config_paths:
            path = Path(config_path)
            if not path.exists():
                continue

            try:
                logger.debug(f"Checking config file: {path}")

                if path.suffix == ".json":
                    with open(path, "r") as f:
                        config = json.load(f)
                elif path.suffix in [".yaml", ".yml"]:
                    with open(path, "r") as f:
                        config = yaml.safe_load(f)
                else:
                    continue

                # Parse different config formats
                if "mcpServers" in config:
                    # Claude Desktop style config
                    self._parse_claude_config(config["mcpServers"])
                elif "targets" in config and "mcp" in config["targets"]:
                    # AgentGateway style config
                    self._parse_agentgateway_config(config["targets"]["mcp"])
                elif "mcp" in config:
                    # Custom MCP config format
                    self._parse_custom_config(config["mcp"])

            except Exception as e:
                logger.warning(f"Failed to parse config {path}: {e}")

    def _parse_claude_config(self, servers_config: Dict):
        """Parse Claude Desktop style MCP configuration"""
        for name, server_config in servers_config.items():
            try:
                server = MCPServerInfo(
                    name=name,
                    protocol="stdio",
                    command=server_config.get("command"),
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                )
                self._servers[name] = server
                logger.debug(f"Added server from Claude config: {name}")
            except Exception as e:
                logger.warning(f"Failed to parse Claude server config {name}: {e}")

    def _parse_agentgateway_config(self, mcp_targets: List[Dict]):
        """Parse AgentGateway style MCP configuration"""
        for target in mcp_targets:
            try:
                name = target["name"]

                if "stdio" in target:
                    server = MCPServerInfo(
                        name=name,
                        protocol="stdio",
                        command=target["stdio"].get("cmd"),
                        args=target["stdio"].get("args", []),
                        env=target["stdio"].get("env", {}),
                    )
                elif "http" in target:
                    server = MCPServerInfo(
                        name=name, protocol="http", endpoint=target["http"].get("url")
                    )
                elif "sse" in target:
                    server = MCPServerInfo(
                        name=name, protocol="sse", endpoint=target["sse"].get("url")
                    )
                else:
                    continue

                self._servers[name] = server
                logger.debug(f"Added server from AgentGateway config: {name}")
            except Exception as e:
                logger.warning(f"Failed to parse AgentGateway target: {e}")

    def _parse_custom_config(self, mcp_config: Dict):
        """Parse custom MCP configuration format"""
        if isinstance(mcp_config, list):
            servers = mcp_config
        elif "servers" in mcp_config:
            servers = mcp_config["servers"]
        else:
            servers = [mcp_config]

        for server_config in servers:
            try:
                name = server_config.get("name", server_config.get("id", "unknown"))
                server = MCPServerInfo(
                    name=name,
                    protocol=server_config.get("protocol", "stdio"),
                    command=server_config.get("command"),
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                    endpoint=server_config.get("endpoint"),
                    tools=server_config.get("tools", []),
                    description=server_config.get("description"),
                )
                self._servers[name] = server
                logger.debug(f"Added server from custom config: {name}")
            except Exception as e:
                logger.warning(f"Failed to parse custom server config: {e}")

    def _discover_from_env(self):
        """Discover MCP servers from environment variables"""
        # Check for MCP_SERVERS env var (comma-separated list)
        mcp_servers = os.environ.get("MCP_SERVERS", "")
        if mcp_servers:
            for server_name in mcp_servers.split(","):
                server_name = server_name.strip()
                if not server_name:
                    continue

                # Look for server-specific env vars
                cmd_var = f"MCP_{server_name.upper()}_COMMAND"
                endpoint_var = f"MCP_{server_name.upper()}_ENDPOINT"

                if cmd_var in os.environ:
                    server = MCPServerInfo(
                        name=server_name, protocol="stdio", command=os.environ[cmd_var]
                    )
                    self._servers[server_name] = server
                    logger.debug(f"Added server from env: {server_name}")
                elif endpoint_var in os.environ:
                    server = MCPServerInfo(
                        name=server_name,
                        protocol="http",
                        endpoint=os.environ[endpoint_var],
                    )
                    self._servers[server_name] = server
                    logger.debug(f"Added server from env: {server_name}")

    def _discover_from_k8s(self):
        """Discover MCP servers from Kubernetes ConfigMaps"""
        if not self._is_k8s_available():
            return

        try:
            # Get AgentGateway ConfigMap
            result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "configmap",
                    "agentgateway-config",
                    "-n",
                    self.k8s_namespace,
                    "-o",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                configmap = json.loads(result.stdout)
                config_data = configmap.get("data", {}).get("config.json", "{}")
                config = json.loads(config_data)

                if "targets" in config and "mcp" in config["targets"]:
                    self._parse_agentgateway_config(config["targets"]["mcp"])

        except Exception as e:
            logger.debug(f"Failed to discover from K8s: {e}")

    def _discover_from_agentgateway(self):
        """Discover MCP servers from AgentGateway API"""
        if not self.use_agentgateway:
            return

        try:
            import httpx

            # Try common AgentGateway URLs
            gateway_urls = [
                os.environ.get("AGENTGATEWAY_URL", ""),
                "http://agentgateway:3000",
                "http://agentgateway.elf-automations:3000",
                "http://localhost:3000",
            ]

            for url in gateway_urls:
                if not url:
                    continue

                try:
                    response = httpx.get(f"{url}/mcp/servers", timeout=2.0)
                    if response.status_code == 200:
                        servers = response.json()
                        for server_info in servers:
                            if isinstance(server_info, str):
                                # Simple server name
                                self._servers[server_info] = MCPServerInfo(
                                    name=server_info
                                )
                            elif isinstance(server_info, dict):
                                # Detailed server info
                                name = server_info.get("name", "unknown")
                                self._servers[name] = MCPServerInfo(
                                    name=name,
                                    protocol=server_info.get("protocol", "stdio"),
                                    endpoint=server_info.get("endpoint"),
                                    tools=server_info.get("tools", []),
                                    description=server_info.get("description"),
                                )
                        logger.debug(f"Discovered servers from AgentGateway at {url}")
                        break
                except Exception:
                    continue

        except ImportError:
            logger.debug("httpx not available for AgentGateway discovery")
        except Exception as e:
            logger.debug(f"Failed to discover from AgentGateway: {e}")

    def _is_k8s_available(self) -> bool:
        """Check if kubectl is available and configured"""
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client", "--short"],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_server(self, name: str) -> Optional[MCPServerInfo]:
        """Get a specific server by name"""
        return self._servers.get(name)

    def list_servers(self) -> List[str]:
        """List all discovered server names"""
        return list(self._servers.keys())

    def get_servers_by_protocol(self, protocol: str) -> List[MCPServerInfo]:
        """Get all servers using a specific protocol"""
        return [
            server for server in self._servers.values() if server.protocol == protocol
        ]

    def get_servers_with_tool(self, tool_name: str) -> List[MCPServerInfo]:
        """Get all servers that provide a specific tool"""
        return [
            server for server in self._servers.values() if tool_name in server.tools
        ]


# Convenience function
def discover_mcp_servers(**kwargs) -> Dict[str, MCPServerInfo]:
    """Convenience function to discover all MCP servers"""
    discovery = MCPDiscovery(**kwargs)
    return discovery.discover_all()
