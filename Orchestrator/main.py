#!/usr/bin/env python3
"""
MCP Orchestrator Server using FastMCP2
Acts as a central hub to manage and communicate with multiple MCP servers.
"""

import json
import os
import subprocess
import asyncio
import signal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from fastmcp import FastMCP
import sys
import time
import threading
import queue
import httpx

# Initialize the MCP server
mcp = FastMCP("MCP Orchestrator")

# Configuration file path
CONFIG_FILE = "mcp_orchestrator_config.json"

@dataclass
class MCPServerProcess:
    """Represents a managed MCP server process."""
    name: str
    process: Optional[subprocess.Popen] = None
    config: Dict[str, Any] = None
    status: str = "running"
    tools: Dict[str, Any] = None
    resources: List[str] = None
    prompts: List[str] = None
    server_type: str = "stdio"  # "stdio" or "http"
    url: Optional[str] = None  # For HTTP servers
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = {}
        if self.resources is None:
            self.resources = []
        if self.prompts is None:
            self.prompts = []
        if self.config is None:
            self.config = {}

class MCPOrchestrator:
    """Manages multiple MCP servers with role-based access control."""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerProcess] = {}
        self.config = {}
        self.server_capabilities: Dict[str, Dict] = {}
        self.permissions: Dict[str, Any] = {}
        self.current_role: str = "user"
        self.rbac_enabled: bool = False
        self.http_client: httpx.Client = httpx.Client(timeout=30.0)  # Sync client
    
    def send_mcp_request_http(self, server_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send an MCP request to an HTTP server (synchronous)."""
        server = self.servers[server_name]
        try:
            response = self.http_client.post(
                server.url,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"HTTP communication error with {server_name}: {str(e)}"}
    
    def send_mcp_request(self, server_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send an MCP request to a specific server and get the response."""
        if server_name not in self.servers:
            return {"error": f"Server {server_name} not found or not running"}
        
        server = self.servers[server_name]
        
        # Handle HTTP servers
        if server.server_type == "http":
            if server.status != "running":
                return {"error": f"Server {server_name} is not running"}
            return self.send_mcp_request_http(server_name, request)
        
        # Handle stdio servers
        if server.status != "running" or server.process.poll() is not None:
            return {"error": f"Server {server_name} is not running"}
        
        try:
            # Send request to server's stdin
            request_json = json.dumps(request) + "\n"
            server.process.stdin.write(request_json)
            server.process.stdin.flush()
            
            # Read response from server's stdout
            response_line = server.process.stdout.readline()
            if not response_line:
                return {"error": "No response from server"}
            
            return json.loads(response_line.strip())
            
        except Exception as e:
            return {"error": f"Communication error with {server_name}: {str(e)}"}
    
    def discover_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """Discover what tools, resources, and prompts a server provides."""
        if server_name not in self.servers:
            return {"error": f"Server {server_name} not found"}
        
        # Initialize the server
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-orchestrator",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = self.send_mcp_request(server_name, init_request)
        if "error" in init_response:
            return init_response
        
        capabilities = {
            "tools": [],
            "resources": [],
            "prompts": []
        }
        
        # Get available tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        tools_response = self.send_mcp_request(server_name, tools_request)
        if "result" in tools_response and "tools" in tools_response["result"]:
            capabilities["tools"] = tools_response["result"]["tools"]
        
        # Get available resources
        resources_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list"
        }
        
        resources_response = self.send_mcp_request(server_name, resources_request)
        if "result" in resources_response and "resources" in resources_response["result"]:
            capabilities["resources"] = resources_response["result"]["resources"]
        
        # Get available prompts
        prompts_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "prompts/list"
        }
        
        prompts_response = self.send_mcp_request(server_name, prompts_request)
        if "result" in prompts_response and "prompts" in prompts_response["result"]:
            capabilities["prompts"] = prompts_response["result"]["prompts"]
        
        self.server_capabilities[server_name] = capabilities
        
        # Update the server object
        if server_name in self.servers:
            server = self.servers[server_name]
            server.tools = {tool["name"]: tool for tool in capabilities["tools"]}
            server.resources = [res["uri"] for res in capabilities["resources"]]
            server.prompts = [prompt["name"] for prompt in capabilities["prompts"]]
        
        return capabilities
    
    def load_permissions(self) -> Dict[str, Any]:
        """Load the tool permissions configuration."""
        permissions_file = self.config.get("rbac", {}).get("permissions_file", "tool_permissions.json")
        
        # Try to load from the same directory as the config
        config_dir = os.path.dirname(os.path.expanduser(f"~/{CONFIG_FILE}"))
        permissions_path = os.path.join(config_dir, permissions_file)
        
        # If not found, try relative to current directory
        if not os.path.exists(permissions_path):
            permissions_path = permissions_file
        
        try:
            with open(permissions_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load permissions file: {e}", file=sys.stderr)
            return {"tool_permissions": {}, "default_policy": {"unknown_tools": "deny"}}
    
    def check_tool_permission(self, server_name: str, tool_name: str) -> tuple[bool, str]:
        """Check if current role has permission to execute a tool.
        
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if not self.rbac_enabled:
            return True, "RBAC disabled"
        
        # Get tool permissions
        tool_perms = self.permissions.get("tool_permissions", {}).get(server_name, {})
        
        if tool_name not in tool_perms:
            # Check default policy for unknown tools
            default_policy = self.permissions.get("default_policy", {}).get("unknown_tools", "deny")
            if default_policy == "deny":
                return False, f"Tool '{tool_name}' not found in permissions configuration"
            return True, "Default policy allows unknown tools"
        
        # Check if current role is allowed
        allowed_roles = tool_perms[tool_name].get("allowed_roles", [])
        
        if self.current_role in allowed_roles:
            return True, f"Role '{self.current_role}' has access"
        
        return False, f"Role '{self.current_role}' does not have permission. Required roles: {', '.join(allowed_roles)}"
    
    def call_server_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on a specific server with RBAC enforcement."""
        if server_name not in self.servers:
            return {"error": f"Server {server_name} not found"}
        
        # Check permissions
        allowed, reason = self.check_tool_permission(server_name, tool_name)
        if not allowed:
            return {
                "error": "Access Denied",
                "reason": reason,
                "server": server_name,
                "tool": tool_name,
                "current_role": self.current_role
            }
        
        # Ensure we have the server's capabilities
        if server_name not in self.server_capabilities:
            self.discover_server_capabilities(server_name)
        
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        return self.send_mcp_request(server_name, request)
    
    def get_server_resource(self, server_name: str, resource_uri: str) -> Dict[str, Any]:
        """Get a resource from a specific server."""
        if server_name not in self.servers:
            return {"error": f"Server {server_name} not found"}
        
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "resources/read",
            "params": {
                "uri": resource_uri
            }
        }
        
        return self.send_mcp_request(server_name, request)
    
    def get_server_prompt(self, server_name: str, prompt_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a prompt from a specific server."""
        if server_name not in self.servers:
            return {"error": f"Server {server_name} not found"}
        
        params = {"name": prompt_name}
        if arguments:
            params["arguments"] = arguments
        
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "prompts/get",
            "params": params
        }
        
        return self.send_mcp_request(server_name, request)
    
    def load_config(self) -> Dict[str, Any]:
        """Load the MCP orchestrator configuration."""
        config_path = os.path.expanduser(f"~/{CONFIG_FILE}")
        
        if not os.path.exists(config_path):
            # Create a default config file with your actual servers
            default_config = {
                "mcpServers": {
                    "notes-server": {
                        "command": "/Users/I527897/Desktop/Final_test/Washim_test/MCPS/.venv/bin/python3",
                        "args": ["/Users/I527897/Desktop/Final_test/Washim_test/MCPS/main.py"],
                        "cwd": "/Users/I527897/Desktop/Final_test/Washim_test/MCPS",
                        "enabled": True,
                        "description": "Simple notes taking MCP server"
                    },
                    "id-manager-server": {
                        "command": "/Users/I527897/Desktop/Final_test/Washim_test/Random_text_generator/.venv/bin/python3",
                        "args": ["/Users/I527897/Desktop/Final_test/Washim_test/Random_text_generator/main.py"],
                        "cwd": "/Users/I527897/Desktop/Final_test/Washim_test/Random_text_generator",
                        "enabled": True,
                        "description": "ID management server for adding/removing unique IDs from text"
                    }
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"mcpServers": {}}
    
    def save_config(self) -> None:
        """Save the current configuration."""
        config_path = os.path.expanduser(f"~/{CONFIG_FILE}")
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def start_server(self, name: str, config: Dict[str, Any]) -> bool:
        """Start an MCP server process or register an HTTP server."""
        try:
            if name in self.servers and self.servers[name].status == "running":
                return False  # Already running
            
            # Check if it's an HTTP server
            if config.get("type") == "http":
                url = config.get("url")
                if not url:
                    print(f"HTTP server {name} missing URL", file=sys.stderr)
                    return False
                
                self.servers[name] = MCPServerProcess(
                    name=name,
                    config=config,
                    status="running",
                    server_type="http",
                    url=url
                )
                
                # Give the HTTP server a moment, then discover capabilities
                time.sleep(1)
                try:
                    self.discover_server_capabilities(name)
                except Exception as e:
                    print(f"Warning: Could not discover capabilities for {name}: {e}", file=sys.stderr)
                
                return True
            
            # Handle stdio servers
            command = [config["command"]] + config.get("args", [])
            cwd = config.get("cwd", os.getcwd())
            env = os.environ.copy()
            
            # Add any custom environment variables
            if "env" in config:
                env.update(config["env"])
            
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self.servers[name] = MCPServerProcess(
                name=name,
                process=process,
                config=config,
                status="running",
                server_type="stdio"
            )
            
            # Give the server a moment to start, then discover capabilities
            time.sleep(1)
            try:
                self.discover_server_capabilities(name)
            except Exception as e:
                print(f"Warning: Could not discover capabilities for {name}: {e}", file=sys.stderr)
            
            return True
            
        except Exception as e:
            print(f"Failed to start server {name}: {e}", file=sys.stderr)
            return False
    
    def stop_server(self, name: str) -> bool:
        """Stop an MCP server process or unregister HTTP server."""
        if name not in self.servers:
            return False
        
        server = self.servers[name]
        
        # HTTP servers are managed externally, just mark as stopped
        if server.server_type == "http":
            server.status = "stopped"
            return True
        
        # Handle stdio servers
        try:
            # Gracefully terminate
            server.process.terminate()
            
            # Wait for termination with timeout
            try:
                server.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not terminated gracefully
                server.process.kill()
                server.process.wait()
            
            server.status = "stopped"
            return True
            
        except Exception as e:
            print(f"Failed to stop server {name}: {e}", file=sys.stderr)
            return False
    
    def get_server_status(self, name: str) -> Dict[str, Any]:
        """Get the status of a specific server."""
        if name not in self.servers:
            return {"status": "not_configured"}
        
        server = self.servers[name]
        
        # Handle HTTP servers
        if server.server_type == "http":
            return {
                "name": name,
                "status": server.status,
                "type": "http",
                "url": server.url,
                "config": server.config,
                "description": server.config.get("description", "")
            }
        
        # Handle stdio servers
        # Check if process is still alive
        if server.process.poll() is None:
            status = "running"
        else:
            status = "stopped"
            server.status = "stopped"
        
        return {
            "name": name,
            "status": status,
            "type": "stdio",
            "pid": server.process.pid if status == "running" else None,
            "config": server.config,
            "description": server.config.get("description", "")
        }
    
    def stop_all_servers(self) -> None:
        """Stop all running servers."""
        for name in list(self.servers.keys()):
            try:
                self.stop_server(name)
            except Exception as e:
                print(f"Error stopping server {name}: {e}", file=sys.stderr)

# Global orchestrator instance
orchestrator = MCPOrchestrator()

@mcp.tool()
def load_orchestrator_config() -> str:
    """
    Load the MCP orchestrator configuration from file.
    
    Returns:
        Status message about configuration loading
    """
    try:
        orchestrator.config = orchestrator.load_config()
        
        # Load RBAC settings
        rbac_config = orchestrator.config.get("rbac", {})
        orchestrator.rbac_enabled = rbac_config.get("enabled", False)
        orchestrator.current_role = rbac_config.get("current_role", "user")
        
        # Load permissions if RBAC is enabled
        if orchestrator.rbac_enabled:
            orchestrator.permissions = orchestrator.load_permissions()
            rbac_status = f" RBAC enabled. Current role: {orchestrator.current_role}"
        else:
            rbac_status = " RBAC disabled"
        
        return f"Configuration loaded successfully. Found {len(orchestrator.config.get('mcpServers', {}))} servers configured.{rbac_status}"
    except Exception as e:
        return f"Failed to load configuration: {str(e)}"

@mcp.tool()
def list_configured_servers() -> str:
    """
    List all configured MCP servers.
    
    Returns:
        List of configured servers with their details
    """
    if not orchestrator.config.get("mcpServers"):
        return "No servers configured. Load configuration first."
    
    servers = orchestrator.config["mcpServers"]
    result = []
    
    for name, config in servers.items():
        enabled = config.get("enabled", True)
        description = config.get("description", "No description")
        command = f"{config.get('command', 'N/A')} {' '.join(config.get('args', []))}"
        
        result.append(f"""
Server: {name}
  Status: {'Enabled' if enabled else 'Disabled'}
  Description: {description}
  Command: {command}
  Working Dir: {config.get('cwd', 'N/A')}
""".strip())
    
    return "\n\n".join(result)

@mcp.tool()
def start_mcp_server(server_name: str) -> str:
    """
    Start a configured MCP server.
    
    Args:
        server_name: Name of the server to start
    
    Returns:
        Status message about the operation
    """
    if not orchestrator.config.get("mcpServers"):
        return "No configuration loaded. Run load_orchestrator_config first."
    
    if server_name not in orchestrator.config["mcpServers"]:
        return f"Server '{server_name}' not found in configuration."
    
    config = orchestrator.config["mcpServers"][server_name]
    
    if not config.get("enabled", True):
        return f"Server '{server_name}' is disabled in configuration."
    
    if orchestrator.start_server(server_name, config):
        return f"Server '{server_name}' started successfully."
    else:
        return f"Failed to start server '{server_name}'. Check logs for details."

@mcp.tool()
def stop_mcp_server(server_name: str) -> str:
    """
    Stop a running MCP server.
    
    Args:
        server_name: Name of the server to stop
    
    Returns:
        Status message about the operation
    """
    if orchestrator.stop_server(server_name):
        return f"Server '{server_name}' stopped successfully."
    else:
        return f"Failed to stop server '{server_name}' or server not running."

@mcp.tool()
def restart_mcp_server(server_name: str) -> str:
    """
    Restart an MCP server.
    
    Args:
        server_name: Name of the server to restart
    
    Returns:
        Status message about the operation
    """
    # Stop first
    stop_result = stop_mcp_server(server_name)
    
    # Wait a moment
    time.sleep(1)
    
    # Start again
    start_result = start_mcp_server(server_name)
    
    return f"Restart operation: {stop_result} -> {start_result}"

@mcp.tool()
def get_server_status(server_name: str) -> str:
    """
    Get detailed status of an MCP server.
    
    Args:
        server_name: Name of the server to check
    
    Returns:
        Detailed status information
    """
    status = orchestrator.get_server_status(server_name)
    
    if status["status"] == "not_configured":
        return f"Server '{server_name}' is not configured."
    
    # Build status output based on server type
    result = f"""Server: {status['name']}
Status: {status['status'].upper()}
Type: {status.get('type', 'stdio').upper()}"""
    
    if status.get('type') == 'http':
        result += f"\nURL: {status.get('url', 'N/A')}"
    else:
        result += f"\nPID: {status.get('pid', 'N/A')}"
        result += f"\nCommand: {status['config'].get('command', 'N/A')}"
        result += f"\nWorking Directory: {status['config'].get('cwd', 'N/A')}"
    
    result += f"\nDescription: {status.get('description', 'N/A')}"
    
    return result

@mcp.tool()
def get_all_servers_status() -> str:
    """
    Get status of all configured servers.
    
    Returns:
        Status of all servers
    """
    if not orchestrator.config.get("mcpServers"):
        return "No servers configured."
    
    result = []
    for server_name in orchestrator.config["mcpServers"].keys():
        status = orchestrator.get_server_status(server_name)
        result.append(f"{server_name}: {status['status'].upper()}")
    
    return "\n".join(result)

@mcp.tool()
def start_all_enabled_servers() -> str:
    """
    Start all enabled servers from the configuration.
    
    Returns:
        Summary of start operations
    """
    if not orchestrator.config.get("mcpServers"):
        return "No servers configured."
    
    results = []
    for name, config in orchestrator.config["mcpServers"].items():
        if config.get("enabled", True):
            if orchestrator.start_server(name, config):
                results.append(f"✓ {name}: Started successfully")
            else:
                results.append(f"✗ {name}: Failed to start")
        else:
            results.append(f"- {name}: Skipped (disabled)")
    
    return "\n".join(results)

@mcp.tool()
def stop_all_servers() -> str:
    """
    Stop all running servers.
    
    Returns:
        Summary of stop operations
    """
    if not orchestrator.servers:
        return "No servers currently running."
    
    results = []
    for name in list(orchestrator.servers.keys()):
        if orchestrator.stop_server(name):
            results.append(f"✓ {name}: Stopped successfully")
        else:
            results.append(f"✗ {name}: Failed to stop")
    
    return "\n".join(results)

@mcp.tool()
def get_config_file_path() -> str:
    """
    Get the path to the orchestrator configuration file.
    
    Returns:
        Full path to the configuration file
    """
    config_path = os.path.expanduser(f"~/{CONFIG_FILE}")
    exists = "exists" if os.path.exists(config_path) else "does not exist"
    return f"Configuration file: {config_path} ({exists})"

@mcp.tool()
def discover_server_tools(server_name: str) -> str:
    """
    Discover and list all available tools from a specific MCP server.
    
    Args:
        server_name: Name of the server to discover tools from
    
    Returns:
        List of available tools with their descriptions
    """
    capabilities = orchestrator.discover_server_capabilities(server_name)
    
    if "error" in capabilities:
        return f"Error discovering tools for {server_name}: {capabilities['error']}"
    
    tools = capabilities.get("tools", [])
    if not tools:
        return f"No tools found for server {server_name}"
    
    result = [f"Available tools for {server_name}:"]
    for tool in tools:
        name = tool.get("name", "Unknown")
        description = tool.get("description", "No description")
        
        # Format input schema if available
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        
        params = []
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "unknown")
            param_desc = param_info.get("description", "")
            is_required = param_name in input_schema.get("required", [])
            req_marker = "*" if is_required else ""
            params.append(f"  - {param_name}{req_marker} ({param_type}): {param_desc}")
        
        params_str = "\n" + "\n".join(params) if params else ""
        
        result.append(f"\n• {name}: {description}{params_str}")
    
    return "\n".join(result)

@mcp.tool()
def list_server_resources(server_name: str) -> str:
    """
    List all available resources from a specific MCP server.
    
    Args:
        server_name: Name of the server to list resources from
    
    Returns:
        List of available resources
    """
    if server_name not in orchestrator.server_capabilities:
        capabilities = orchestrator.discover_server_capabilities(server_name)
        if "error" in capabilities:
            return f"Error discovering resources for {server_name}: {capabilities['error']}"
    
    resources = orchestrator.server_capabilities.get(server_name, {}).get("resources", [])
    
    if not resources:
        return f"No resources found for server {server_name}"
    
    result = [f"Available resources for {server_name}:"]
    for resource in resources:
        uri = resource.get("uri", "Unknown URI")
        name = resource.get("name", uri)
        description = resource.get("description", "No description")
        mime_type = resource.get("mimeType", "unknown")
        
        result.append(f"• {name} ({uri})")
        result.append(f"  Type: {mime_type}")
        result.append(f"  Description: {description}")
    
    return "\n".join(result)

@mcp.tool()
def list_server_prompts(server_name: str) -> str:
    """
    List all available prompts from a specific MCP server.
    
    Args:
        server_name: Name of the server to list prompts from
    
    Returns:
        List of available prompts
    """
    if server_name not in orchestrator.server_capabilities:
        capabilities = orchestrator.discover_server_capabilities(server_name)
        if "error" in capabilities:
            return f"Error discovering prompts for {server_name}: {capabilities['error']}"
    
    prompts = orchestrator.server_capabilities.get(server_name, {}).get("prompts", [])
    
    if not prompts:
        return f"No prompts found for server {server_name}"
    
    result = [f"Available prompts for {server_name}:"]
    for prompt in prompts:
        name = prompt.get("name", "Unknown")
        description = prompt.get("description", "No description")
        
        result.append(f"• {name}: {description}")
    
    return "\n".join(result)

@mcp.tool()
def call_server_tool(server_name: str, tool_name: str, arguments: str = "{}") -> str:
    """
    Call a specific tool on a specific MCP server.
    
    Args:
        server_name: Name of the server hosting the tool
        tool_name: Name of the tool to call
        arguments: JSON string containing the tool arguments
    
    Returns:
        Result from the tool execution
    """
    try:
        # Parse arguments
        if arguments:
            args = json.loads(arguments)
        else:
            args = {}
        
        # Call the tool
        response = orchestrator.call_server_tool(server_name, tool_name, args)
        
        if "error" in response:
            return f"Error calling {tool_name} on {server_name}: {response['error']}"
        
        if "result" in response:
            result = response["result"]
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            else:
                return str(result)
        
        return f"Tool {tool_name} executed successfully but returned no result"
        
    except json.JSONDecodeError:
        return f"Error: Invalid JSON arguments: {arguments}"
    except Exception as e:
        return f"Error calling tool: {str(e)}"

@mcp.tool()
def get_server_resource(server_name: str, resource_uri: str) -> str:
    """
    Get content from a specific resource on an MCP server.
    
    Args:
        server_name: Name of the server hosting the resource
        resource_uri: URI of the resource to retrieve
    
    Returns:
        Content of the resource
    """
    response = orchestrator.get_server_resource(server_name, resource_uri)
    
    if "error" in response:
        return f"Error getting resource {resource_uri} from {server_name}: {response['error']}"
    
    if "result" in response:
        result = response["result"]
        if isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return str(result)
    
    return f"Resource {resource_uri} retrieved but returned no content"

@mcp.tool()
def get_server_prompt(server_name: str, prompt_name: str, arguments: str = "{}") -> str:
    """
    Get a prompt from a specific MCP server.
    
    Args:
        server_name: Name of the server hosting the prompt
        prompt_name: Name of the prompt to retrieve
        arguments: JSON string containing the prompt arguments
    
    Returns:
        The prompt content
    """
    try:
        # Parse arguments
        if arguments:
            args = json.loads(arguments)
        else:
            args = None
        
        # Get the prompt
        response = orchestrator.get_server_prompt(server_name, prompt_name, args)
        
        if "error" in response:
            return f"Error getting prompt {prompt_name} from {server_name}: {response['error']}"
        
        if "result" in response:
            result = response["result"]
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            else:
                return str(result)
        
        return f"Prompt {prompt_name} retrieved but returned no content"
        
    except json.JSONDecodeError:
        return f"Error: Invalid JSON arguments: {arguments}"
    except Exception as e:
        return f"Error getting prompt: {str(e)}"

@mcp.tool()
def list_all_server_capabilities() -> str:
    """
    List all tools, resources, and prompts from all running servers.
    
    Returns:
        Comprehensive list of all capabilities across all servers
    """
    if not orchestrator.servers:
        return "No servers currently running."
    
    result = ["All Server Capabilities:"]
    
    for server_name in orchestrator.servers.keys():
        if orchestrator.servers[server_name].status == "running":
            # Ensure we have capabilities
            if server_name not in orchestrator.server_capabilities:
                orchestrator.discover_server_capabilities(server_name)
            
            capabilities = orchestrator.server_capabilities.get(server_name, {})
            
            result.append(f"\n=== {server_name.upper()} ===")
            
            # Tools
            tools = capabilities.get("tools", [])
            if tools:
                result.append("Tools:")
                for tool in tools:
                    result.append(f"  • {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            else:
                result.append("Tools: None")
            
            # Resources
            resources = capabilities.get("resources", [])
            if resources:
                result.append("Resources:")
                for resource in resources:
                    result.append(f"  • {resource.get('name', resource.get('uri', 'Unknown'))}")
            else:
                result.append("Resources: None")
            
            # Prompts
            prompts = capabilities.get("prompts", [])
            if prompts:
                result.append("Prompts:")
                for prompt in prompts:
                    result.append(f"  • {prompt.get('name', 'Unknown')}: {prompt.get('description', 'No description')}")
            else:
                result.append("Prompts: None")
    
    return "\n".join(result)

@mcp.tool()
def get_current_role() -> str:
    """
    Get the current RBAC role.
    
    Returns:
        Current role and RBAC status
    """
    if not orchestrator.rbac_enabled:
        return "RBAC is disabled. All tools are accessible."
    
    return f"Current role: {orchestrator.current_role}\nRBAC enabled: {orchestrator.rbac_enabled}"

@mcp.tool()
def set_role(role: str) -> str:
    """
    Set the current RBAC role.
    
    Args:
        role: Role to set (user or admin)
    
    Returns:
        Status message
    """
    if role not in ["user", "admin"]:
        return f"Error: Invalid role '{role}'. Valid roles are: user, admin"
    
    orchestrator.current_role = role
    
    # Update config file
    orchestrator.config["rbac"]["current_role"] = role
    orchestrator.save_config()
    
    return f"Role changed to: {role}"

@mcp.tool()
def check_tool_access(server_name: str, tool_name: str) -> str:
    """
    Check if current role has access to a specific tool.
    
    Args:
        server_name: Name of the server
        tool_name: Name of the tool to check
    
    Returns:
        Access status and details
    """
    if not orchestrator.rbac_enabled:
        return f"RBAC is disabled. Access to {server_name}/{tool_name} is allowed."
    
    allowed, reason = orchestrator.check_tool_permission(server_name, tool_name)
    
    if allowed:
        return f"✓ Access ALLOWED to {server_name}/{tool_name}\nReason: {reason}\nCurrent role: {orchestrator.current_role}"
    else:
        return f"✗ Access DENIED to {server_name}/{tool_name}\nReason: {reason}\nCurrent role: {orchestrator.current_role}"

@mcp.tool()
def list_available_tools_for_role(role: str = None) -> str:
    """
    List all tools available for a specific role.
    
    Args:
        role: Role to check (defaults to current role)
    
    Returns:
        List of accessible tools
    """
    check_role = role if role else orchestrator.current_role
    
    if not orchestrator.rbac_enabled:
        return "RBAC is disabled. All tools are accessible."
    
    if check_role not in ["user", "admin"]:
        return f"Error: Invalid role '{check_role}'. Valid roles are: user, admin"
    
    result = [f"Tools accessible to role '{check_role}':\n"]
    
    tool_permissions = orchestrator.permissions.get("tool_permissions", {})
    
    for server_name, tools in tool_permissions.items():
        server_tools = []
        for tool_name, perms in tools.items():
            allowed_roles = perms.get("allowed_roles", [])
            if check_role in allowed_roles:
                description = perms.get("description", "No description")
                server_tools.append(f"  • {tool_name}: {description}")
        
        if server_tools:
            result.append(f"\n{server_name}:")
            result.extend(server_tools)
    
    if len(result) == 1:
        return f"No tools configured for role '{check_role}'"
    
    return "\n".join(result)

@mcp.tool()
def list_tool_permissions() -> str:
    """
    List all tool permissions and their role requirements.
    
    Returns:
        Complete tool permissions configuration
    """
    if not orchestrator.rbac_enabled:
        return "RBAC is disabled."
    
    if not orchestrator.permissions.get("tool_permissions"):
        return "No tool permissions configured."
    
    result = ["Tool Permissions:\n"]
    
    tool_permissions = orchestrator.permissions.get("tool_permissions", {})
    
    for server_name, tools in tool_permissions.items():
        result.append(f"\n{server_name}:")
        for tool_name, perms in tools.items():
            allowed_roles = perms.get("allowed_roles", [])
            description = perms.get("description", "No description")
            result.append(f"  • {tool_name}")
            result.append(f"    Roles: {', '.join(allowed_roles)}")
            result.append(f"    Description: {description}")
    
    return "\n".join(result)

@mcp.tool()
def reload_permissions() -> str:
    """
    Reload the tool permissions from the permissions file.
    
    Returns:
        Status message
    """
    try:
        orchestrator.permissions = orchestrator.load_permissions()
        tool_count = sum(len(tools) for tools in orchestrator.permissions.get("tool_permissions", {}).values())
        return f"Permissions reloaded successfully. {tool_count} tools configured across {len(orchestrator.permissions.get('tool_permissions', {}))} servers."
    except Exception as e:
        return f"Error reloading permissions: {str(e)}"

def cleanup_on_exit():
    """Cleanup function to stop all servers on exit."""
    print("Shutting down orchestrator...", file=sys.stderr)
    orchestrator.stop_all_servers()

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    cleanup_on_exit()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load initial configuration
        orchestrator.config = orchestrator.load_config()
        
        # Initialize RBAC
        rbac_config = orchestrator.config.get("rbac", {})
        orchestrator.rbac_enabled = rbac_config.get("enabled", False)
        orchestrator.current_role = rbac_config.get("current_role", "user")
        
        if orchestrator.rbac_enabled:
            orchestrator.permissions = orchestrator.load_permissions()
            print(f"MCP Orchestrator started with {len(orchestrator.config.get('mcpServers', {}))} servers configured", file=sys.stderr)
            print(f"RBAC enabled. Current role: {orchestrator.current_role}", file=sys.stderr)
        else:
            print(f"MCP Orchestrator started with {len(orchestrator.config.get('mcpServers', {}))} servers configured", file=sys.stderr)
            print("RBAC disabled", file=sys.stderr)
        
        # Run the server using stdio transport (default MCP protocol)
        # For HTTP/SSE access, clients can wrap stdio with their own server
        mcp.run()
    except KeyboardInterrupt:
        cleanup_on_exit()
    except Exception as e:
        print(f"Orchestrator error: {e}", file=sys.stderr)
        cleanup_on_exit()
        sys.exit(1)
