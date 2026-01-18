# SonarQube MCP Server

A Model Context Protocol (MCP) server that provides comprehensive tools to interact with your SonarQube instance running on localhost:9000.

## Features

This MCP server provides **25 tools** to interact with SonarQube:

### Code Analysis
- `analyze_code_snippet` - Analyze code snippets for quality and security issues
- `analyze_file_list` - Analyze multiple files using SonarQube for IDE
- `toggle_automatic_analysis` - Enable/disable automatic analysis

### Issue Management
- `search_sonar_issues_in_projects` - Search for issues across projects
- `change_sonar_issue_status` - Change issue status/transitions

### Project Management
- `search_my_sonarqube_projects` - Find and list projects
- `get_component_measures` - Get project metrics (complexity, violations, coverage, etc.)

### Quality Gates
- `list_quality_gates` - List all quality gates
- `get_project_quality_gate_status` - Get quality gate status for a project

### Rules & Languages
- `show_rule` - Get detailed information about a rule
- `list_rule_repositories` - List available rule repositories
- `list_languages` - List supported programming languages

### Metrics
- `search_metrics` - Search for available metrics

### Source Code
- `get_raw_source` - Get raw source code from SonarQube
- `get_scm_info` - Get SCM information for source files

### System Information
- `get_system_health` - Check server health status (GREEN/YELLOW/RED)
- `get_system_status` - Get server status, version, and ID
- `get_system_logs` - Retrieve system logs
- `ping_system` - Ping the server to check if it's alive
- `get_system_info` - Get detailed system configuration

### Webhooks
- `create_webhook` - Create a new webhook
- `list_webhooks` - List all webhooks

### Portfolio & Enterprise (SonarQube Cloud)
- `list_portfolios` - List available portfolios
- `list_enterprises` - List accessible enterprises

### Security
- `search_dependency_risks` - Search for software composition analysis issues

## Installation

1. Install dependencies using `uv`:
```bash
uv sync
```

2. **Generate a SonarQube authentication token:**
   - Log in to your SonarQube instance (http://localhost:9000)
   - Go to My Account → Security → Generate Tokens
   - Create a new token with appropriate permissions
   - Copy the generated token

3. Run the MCP server:
```bash
uv run sonarqube_server.py
```

## Authentication

The server supports authentication via environment variables:

- `SONAR_TOKEN` - Your SonarQube authentication token (required for authenticated endpoints)
- `SONAR_HOST_URL` - SonarQube server URL (defaults to http://localhost:9000)

## Configuration for Cline

To use this server with Cline (VS Code extension), add it to your MCP settings:

1. Open Cline settings in VS Code
2. Go to MCP Servers configuration
3. Add the following configuration:

```json
{
  "mcpServers": {
    "sonarqube": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/I527897/Desktop/SONAR_MCP_TRY",
        "run",
        "sonarqube_server.py"
      ],
      "env": {
        "SONAR_TOKEN": "your_sonarqube_token_here",
        "SONAR_HOST_URL": "http://localhost:9000"
      }
    }
  }
}
```

**Important:** Replace the following values:
- `/Users/I527897/Desktop/SONAR_MCP_TRY` with the actual path to this project directory
- `your_sonarqube_token_here` with your actual SonarQube authentication token
- `http://localhost:9000` with your SonarQube server URL (if different)

### How to Generate a SonarQube Token

1. Log in to your SonarQube instance
2. Click on your profile icon (top right) → **My Account**
3. Navigate to the **Security** tab
4. In the **Generate Tokens** section:
   - Enter a token name (e.g., "Cline MCP Server")
   - Select token type: **User Token** (recommended) or **Global Analysis Token**
   - Choose an expiration date or select "No expiration"
   - Click **Generate**
5. Copy the generated token immediately (you won't be able to see it again)
6. Paste it in your Cline MCP configuration under `SONAR_TOKEN`

## Usage Examples

Once configured, you can use the tools in Cline:

- **Check server status**: "Use the ping_system tool to check if SonarQube is running"
- **Get project metrics**: "Get the code coverage and complexity metrics for project 'my-app'"
- **Search for issues**: "Find all HIGH severity issues in my projects"
- **View quality gate**: "What's the quality gate status for project 'my-app'?"
- **List projects**: "Show me all my SonarQube projects"

## Requirements

- Python 3.13+
- SonarQube server running on http://localhost:9000
- Dependencies: fastmcp, httpx, mcp

## Notes

- The server connects to SonarQube at `http://localhost:9000` by default
- Some tools require specific SonarQube permissions (e.g., 'Administer' for system info)
- Code analysis tools (analyze_code_snippet, analyze_file_list) require SonarQube for IDE integration
- Authentication can be added by modifying the `make_sonar_request` function to include tokens

## License

MIT
