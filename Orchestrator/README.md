# MCP Orchestrator Server

A Model Context Protocol (MCP) server that acts as a central orchestrator to manage and control multiple MCP servers. This server allows you to start, stop, monitor, and manage other MCP servers through a unified interface.

## Features

The orchestrator provides comprehensive tools for managing MCP servers:

- **Configuration Management**: Load and manage server configurations
- **Server Lifecycle**: Start, stop, and restart individual servers
- **Status Monitoring**: Check the status of all managed servers
- **Bulk Operations**: Start all enabled servers or stop all running servers
- **Process Management**: Proper cleanup and signal handling

## Tools Available

### Configuration Tools
- **load_orchestrator_config**: Load the MCP server configuration from file
- **list_configured_servers**: List all configured servers with details
- **get_config_file_path**: Get the path to the configuration file

### Server Management Tools
- **start_mcp_server**: Start a specific configured server
- **stop_mcp_server**: Stop a running server
- **restart_mcp_server**: Restart a server (stop + start)
- **start_all_enabled_servers**: Start all enabled servers at once
- **stop_all_servers**: Stop all currently running servers

### Monitoring Tools
- **get_server_status**: Get detailed status of a specific server
- **get_all_servers_status**: Get status summary of all servers

### RBAC Management Tools
- **get_current_role**: Check your current role and RBAC status
- **set_role**: Change to a different role (user/admin)
- **check_tool_access**: Check if current role has access to a specific tool
- **list_available_tools_for_role**: List all tools accessible to a role
- **list_tool_permissions**: View complete tool permission configuration
- **reload_permissions**: Reload permissions from file after changes

### Server Capability Discovery Tools
- **discover_server_capabilities**: Discover all capabilities of a server
- **list_server_tools**: List all tools provided by a server
- **list_server_resources**: List all resources provided by a server
- **list_server_prompts**: List all prompts provided by a server
- **list_all_server_capabilities**: List all capabilities across all servers

### Server Interaction Tools
- **call_server_tool**: Call a specific tool on a server (enforces RBAC)
- **get_server_resource**: Get content from a server resource
- **get_server_prompt**: Get a prompt from a server

## Configuration File Format

The orchestrator uses the same configuration format as Claude Desktop's `claude_desktop_config.json`. The default configuration file is saved as `~/mcp_orchestrator_config.json`.

### Configuration Structure
```json
{
  "rbac": {
    "enabled": true,
    "current_role": "admin",
    "permissions_file": "tool_permissions.json"
  },
  "mcpServers": {
    "server-name": {
      "command": "/path/to/python",
      "args": ["/path/to/server.py"],
      "cwd": "/working/directory",
      "enabled": true,
      "description": "Description of the server",
      "env": {
        "CUSTOM_VAR": "value"
      }
    }
  }
}
```

### Configuration Fields

#### RBAC Configuration
- **rbac.enabled**: Enable/disable role-based access control (default: false)
- **rbac.current_role**: Current user role - "user" or "admin" (default: "user")
- **rbac.permissions_file**: Path to permissions configuration file (default: "tool_permissions.json")

#### Server Configuration
- **command**: The executable command to run the server
- **args**: Array of command-line arguments
- **cwd**: Working directory for the server process
- **enabled**: Whether the server should be started with bulk operations (optional, default: true)
- **description**: Human-readable description of the server (optional)
- **env**: Additional environment variables (optional)

## Role-Based Access Control (RBAC)

The orchestrator includes a comprehensive RBAC system to control access to MCP server tools based on user roles.

### Available Roles

- **user**: Standard user with read and safe operation access
- **admin**: Administrator with full access including dangerous operations (delete, remove, etc.)

### RBAC Configuration

RBAC is configured through two files:

1. **mcp_orchestrator_config.json**: Main config with RBAC settings
2. **tool_permissions.json**: Tool-level permission definitions

### Tool Permissions File Format

```json
{
  "description": "Role-based access control for MCP server tools",
  "roles": {
    "user": {
      "description": "Standard user with read and safe operation access"
    },
    "admin": {
      "description": "Administrator with full access including dangerous operations"
    }
  },
  "tool_permissions": {
    "notes-server": {
      "create_note": {
        "allowed_roles": ["user", "admin"],
        "description": "Create a new note"
      },
      "delete_note": {
        "allowed_roles": ["admin"],
        "description": "Delete a note - restricted to admins"
      }
    }
  },
  "default_policy": {
    "unknown_tools": "deny",
    "description": "By default, unknown tools are denied for all roles"
  }
}
```

### RBAC Management Tools

The orchestrator provides several tools for managing RBAC:

- **get_current_role**: Check your current role
- **set_role**: Change to a different role (user/admin)
- **check_tool_access**: Check if you have access to a specific tool
- **list_available_tools_for_role**: List all tools accessible to a role
- **list_tool_permissions**: View complete permission configuration
- **reload_permissions**: Reload permissions from file after changes

### RBAC Examples

#### Checking Current Role
```
get_current_role()
→ "Current role: admin\nRBAC enabled: true"
```

#### Switching Roles
```
set_role("user")
→ "Role changed to: user"
```

#### Checking Tool Access
```
check_tool_access("notes-server", "delete_note")
→ "✗ Access DENIED to notes-server/delete_note
   Reason: Role 'user' does not have permission. Required roles: admin
   Current role: user"
```

#### Listing Available Tools
```
list_available_tools_for_role("user")
→ Shows all tools accessible to users
```

### Access Denied Behavior

When RBAC is enabled and a user attempts to call a restricted tool, they receive an error response:

```json
{
  "error": "Access Denied",
  "reason": "Role 'user' does not have permission. Required roles: admin",
  "server": "notes-server",
  "tool": "delete_note",
  "current_role": "user"
}
```

### Configuring Tool Permissions

To add or modify tool permissions:

1. Edit `tool_permissions.json`
2. Add tool entries under the appropriate server
3. Specify allowed roles for each tool
4. Use `reload_permissions()` to apply changes without restarting

Example adding a new tool:
```json
"notes-server": {
  "archive_note": {
    "allowed_roles": ["user", "admin"],
    "description": "Archive a note for later reference"
  }
}
```

### Best Practices for RBAC

1. **Dangerous Operations**: Always restrict destructive operations (delete, remove, purge) to admin role
2. **Default Deny**: Keep `unknown_tools` set to "deny" for security
3. **Regular Audits**: Periodically review and update tool permissions
4. **Least Privilege**: Start users with minimal permissions, add as needed
5. **Document Changes**: Add clear descriptions to each permission entry

## Configuration File Format

## Installation and Setup

1. Make sure you have Python 3.14+ installed
2. FastMCP is already installed via: `uv add fastmcp`

## Usage Examples

### Starting the Orchestrator
The orchestrator runs as a standard MCP server and can be added to Claude Desktop.

### Basic Workflow
1. **Load Configuration**: Use `load_orchestrator_config` to load server definitions
2. **List Servers**: Use `list_configured_servers` to see available servers
3. **Start Servers**: Use `start_mcp_server` for individual servers or `start_all_enabled_servers` for bulk
4. **Monitor**: Use `get_all_servers_status` to check on running servers
5. **Stop Servers**: Use `stop_mcp_server` or `stop_all_servers` when done

### Example Configuration
The orchestrator comes with a sample configuration that includes:
- **notes-server**: Your notes taking MCP server
- **id-manager-server**: Your ID management MCP server

## Claude Desktop Integration

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-orchestrator": {
      "command": "/Users/I527897/Desktop/Final_test/Washim_test/Orchestrator/.venv/bin/python3",
      "args": ["/Users/I527897/Desktop/Final_test/Washim_test/Orchestrator/main.py"],
      "cwd": "/Users/I527897/Desktop/Final_test/Washim_test/Orchestrator"
    }
  }
}
```

## Use Cases

### Development Environment Management
- Start/stop development servers during coding sessions
- Manage different server configurations for different projects
- Quick status checks on all your MCP services

### Testing and Debugging
- Restart servers that might have crashed
- Test server configurations before deploying
- Monitor server health and process information

### Production-like Orchestration
- Manage multiple MCP servers as a unified system
- Bulk operations for environment setup/teardown
- Central logging and monitoring point

## Process Management

The orchestrator provides robust process management:
- **Graceful Shutdown**: Attempts to terminate processes cleanly
- **Force Kill**: Falls back to force kill if graceful shutdown fails
- **Signal Handling**: Properly handles SIGINT and SIGTERM for cleanup
- **Process Monitoring**: Tracks process IDs and status

## Error Handling

- **Configuration Errors**: Clear error messages for invalid configurations
- **Process Failures**: Detailed error reporting for failed server starts
- **File System Issues**: Handles missing configuration files gracefully
- **Resource Cleanup**: Ensures all spawned processes are cleaned up on exit

## Security Considerations

- The orchestrator runs with the same permissions as your user account
- Spawned servers inherit the orchestrator's environment
- Configuration file is stored in your home directory with standard file permissions
- No network exposure by default (uses stdio transport)
- **RBAC Protection**: Enable RBAC to restrict dangerous operations to admin role only
- **Tool Permissions**: Granular control over which roles can execute specific tools
- **Access Logging**: All access denied attempts are logged with details
- **Configurable Security**: Adjust tool permissions without code changes

## Limitations

- Currently supports stdio-based MCP servers only
- Process management is local to the machine
- Configuration changes require manual file editing for some settings
- RBAC roles are configured per orchestrator instance (no centralized user management)

## Future Enhancements

Potential future features:
- Web-based configuration interface
- HTTP-based MCP server support
- Server health checks and auto-restart
- Logging aggregation from managed servers
- Configuration validation and testing tools
