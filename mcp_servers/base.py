"""
Base MCP Server for ELF Automations

This module provides the base class for all MCP servers in the
Virtual AI Company Platform.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class MCPTool(BaseModel):
    """Definition of an MCP tool."""
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    parameters: Dict[str, Any] = Field(description="Tool parameters schema")
    
    
class MCPResource(BaseModel):
    """Definition of an MCP resource."""
    
    uri: str = Field(description="Resource URI")
    name: str = Field(description="Resource name")
    description: str = Field(description="Resource description")
    mime_type: str = Field(description="Resource MIME type")


class BaseMCPServer(ABC):
    """
    Base class for all MCP servers.
    
    This class provides the foundational functionality for MCP servers,
    including tool registration, resource management, and communication protocols.
    """
    
    def __init__(self, server_name: str, version: str = "1.0.0"):
        """Initialize the MCP server."""
        self.server_name = server_name
        self.version = version
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        
        self.logger = logger.bind(
            server_name=server_name,
            version=version
        )
        
        self.logger.info("MCP server initialized")
    
    def register_tool(self, tool: MCPTool) -> None:
        """Register a tool with the MCP server."""
        self.tools[tool.name] = tool
        self.logger.info("Tool registered", tool_name=tool.name)
    
    def register_resource(self, resource: MCPResource) -> None:
        """Register a resource with the MCP server."""
        self.resources[resource.uri] = resource
        self.logger.info("Resource registered", resource_uri=resource.uri)
    
    def get_tools(self) -> List[MCPTool]:
        """Get all registered tools."""
        return list(self.tools.values())
    
    def get_resources(self) -> List[MCPResource]:
        """Get all registered resources."""
        return list(self.resources.values())
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a resource by URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        pass
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP request.
        
        Args:
            request: MCP request
            
        Returns:
            MCP response
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "tools/list":
                return await self._handle_list_tools()
            elif method == "tools/call":
                return await self._handle_call_tool(params)
            elif method == "resources/list":
                return await self._handle_list_resources()
            elif method == "resources/read":
                return await self._handle_read_resource(params)
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            self.logger.error("Error handling MCP request", error=str(e))
            return {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_list_tools(self) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters
            })
        
        return {
            "tools": tools_list
        }
    
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Tool not found: {tool_name}"
                }
            }
        
        try:
            result = await self.call_tool(tool_name, arguments)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }
    
    async def _handle_list_resources(self) -> Dict[str, Any]:
        """Handle resources/list request."""
        resources_list = []
        for resource in self.resources.values():
            resources_list.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mime_type
            })
        
        return {
            "resources": resources_list
        }
    
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")
        
        if uri not in self.resources:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Resource not found: {uri}"
                }
            }
        
        try:
            content = await self.read_resource(uri)
            return {
                "contents": [content]
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Resource read failed: {str(e)}"
                }
            }
    
    async def start(self, host: str = "localhost", port: int = 8080) -> None:
        """Start the MCP server."""
        self.logger.info("Starting MCP server", host=host, port=port)
        
        # In a real implementation, this would start an HTTP server
        # For now, we'll just log that the server is ready
        self.logger.info("MCP server ready")
    
    async def stop(self) -> None:
        """Stop the MCP server."""
        self.logger.info("Stopping MCP server")
        
        # Cleanup resources
        self.tools.clear()
        self.resources.clear()
        
        self.logger.info("MCP server stopped")
