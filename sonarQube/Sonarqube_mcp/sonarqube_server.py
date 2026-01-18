#!/usr/bin/env python3
"""
SonarQube MCP Server
Provides tools to interact with SonarQube instance running on localhost:9000
"""

import httpx
import os
from typing import Optional, Any
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("SonarQube MCP Server")

# SonarQube base URL and authentication
SONAR_BASE_URL = os.getenv("SONAR_HOST_URL", "http://localhost:9000")
SONAR_TOKEN = os.getenv("SONAR_TOKEN", "")


def make_sonar_request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> Any:
    """Make HTTP request to SonarQube API"""
    url = f"{SONAR_BASE_URL}/api{endpoint}"
    
    # Prepare headers with authentication if token is available
    headers = {}
    if SONAR_TOKEN:
        # SonarQube uses token as username with empty password (Basic Auth)
        headers["Authorization"] = f"Bearer {SONAR_TOKEN}"
    
    try:
        with httpx.Client() as client:
            response = client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Handle plain text responses
            content_type = response.headers.get("content-type", "")
            if "text/plain" in content_type:
                return {"result": response.text}
            
            # Handle JSON responses
            try:
                return response.json()
            except Exception:
                return {"result": response.text}
                
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def analyze_code_snippet(language: str, code_snippet: str) -> dict:
    """
    Analyze a file or code snippet with SonarQube analyzers to identify code quality and security issues
    
    Args:
        language: Language of the code snippet
        code_snippet: Code snippet to analyze
    """
    # Note: This typically requires SonarQube for IDE integration
    # Using a mock implementation as direct snippet analysis requires special setup
    return {
        "message": "Code snippet analysis requires SonarQube for IDE integration",
        "language": language,
        "snippet_length": len(code_snippet)
    }


@mcp.tool()
def analyze_file_list(file_absolute_paths: list[str]) -> dict:
    """
    Analyze files in the current working directory using SonarQube for IDE
    
    Args:
        file_absolute_paths: List of absolute file paths to analyze
    """
    # Note: This requires SonarQube for IDE integration
    return {
        "message": "File analysis requires SonarQube for IDE integration",
        "files_count": len(file_absolute_paths),
        "files": file_absolute_paths
    }


@mcp.tool()
def toggle_automatic_analysis(enabled: bool) -> dict:
    """
    Enable or disable SonarQube for IDE automatic analysis
    
    Args:
        enabled: Enable or disable the automatic analysis
    """
    return {
        "message": "Automatic analysis toggle requires SonarQube for IDE integration",
        "enabled": enabled
    }


@mcp.tool()
def search_sonar_issues_in_projects(
    projects: Optional[list[str]] = None,
    pullRequestId: Optional[str] = None,
    severities: Optional[str] = None,
    page: int = 1,
    pageSize: int = 100
) -> dict:
    """
    Search for SonarQube issues in organization's projects
    
    Args:
        projects: Optional list of Sonar projects to look in
        pullRequestId: The identifier of the Pull Request to look in
        severities: Optional list of severities (INFO, LOW, MEDIUM, HIGH, BLOCKER)
        page: Page number (default: 1)
        pageSize: Page size, max 500 (default: 100)
    """
    params = {
        "p": page,
        "ps": min(pageSize, 500)
    }
    
    if projects:
        params["projects"] = ",".join(projects)
    if pullRequestId:
        params["pullRequest"] = pullRequestId
    if severities:
        params["severities"] = severities
    
    return make_sonar_request("GET", "/issues/search", params=params)


@mcp.tool()
def change_sonar_issue_status(issue_key: str, transition: str) -> dict:
    """
    Change the status of a SonarQube issue
    
    Args:
        issue_key: Key of the issue to modify
        transition: Transition to apply to the issue
    """
    params = {
        "issue": issue_key,
        "transition": transition
    }
    
    return make_sonar_request("POST", "/issues/do_transition", params=params)


@mcp.tool()
def search_my_sonarqube_projects(page: str = "1") -> dict:
    """
    Find SonarQube projects. The response is paginated
    
    Args:
        page: Page number (default: "1")
    """
    params = {"p": page}
    return make_sonar_request("GET", "/projects/search", params=params)


@mcp.tool()
def list_quality_gates() -> dict:
    """List all quality gates in SonarQube"""
    return make_sonar_request("GET", "/qualitygates/list")


@mcp.tool()
def get_project_quality_gate_status(
    analysisId: Optional[str] = None,
    branch: Optional[str] = None,
    projectId: Optional[str] = None,
    projectKey: Optional[str] = None,
    pullRequest: Optional[str] = None
) -> dict:
    """
    Get the quality gate status for a project
    
    Args:
        analysisId: Optional analysis ID
        branch: Optional branch key
        projectId: Optional project ID
        projectKey: Optional project key
        pullRequest: Optional pull request ID
    """
    params = {}
    if analysisId:
        params["analysisId"] = analysisId
    if branch:
        params["branch"] = branch
    if projectId:
        params["projectId"] = projectId
    if projectKey:
        params["projectKey"] = projectKey
    if pullRequest:
        params["pullRequest"] = pullRequest
    
    return make_sonar_request("GET", "/qualitygates/project_status", params=params)


@mcp.tool()
def show_rule(key: str) -> dict:
    """
    Shows detailed information about a SonarQube rule
    
    Args:
        key: Rule key
    """
    params = {"key": key}
    return make_sonar_request("GET", "/rules/show", params=params)


@mcp.tool()
def list_rule_repositories(
    language: Optional[str] = None,
    q: Optional[str] = None
) -> dict:
    """
    List rule repositories available in SonarQube
    
    Args:
        language: Optional language key to filter repositories
        q: Optional search query to filter repositories by name or key
    """
    params = {}
    if language:
        params["language"] = language
    if q:
        params["q"] = q
    
    return make_sonar_request("GET", "/rules/repositories", params=params)


@mcp.tool()
def list_languages(q: Optional[str] = None) -> dict:
    """
    List all programming languages supported in this SonarQube instance
    
    Args:
        q: Optional pattern to match language keys/names against
    """
    params = {}
    if q:
        params["q"] = q
    
    return make_sonar_request("GET", "/languages/list", params=params)


@mcp.tool()
def get_component_measures(
    projectKey: str,
    metricKeys: list[str],
    branch: Optional[str] = None,
    pullRequest: Optional[str] = None
) -> dict:
    """
    Get SonarQube measures for a project (ncloc, complexity, violations, coverage, etc)
    
    Args:
        projectKey: The project key
        metricKeys: The metric keys to retrieve
        branch: Optional branch to analyze
        pullRequest: Optional pull request identifier
    """
    params = {
        "component": projectKey,
        "metricKeys": ",".join(metricKeys)
    }
    
    if branch:
        params["branch"] = branch
    if pullRequest:
        params["pullRequest"] = pullRequest
    
    return make_sonar_request("GET", "/measures/component", params=params)


@mcp.tool()
def search_metrics(page: int = 1, pageSize: int = 100) -> dict:
    """
    Search for SonarQube metrics
    
    Args:
        page: 1-based page number (default: 1)
        pageSize: Page size, max 500 (default: 100)
    """
    params = {
        "p": page,
        "ps": min(pageSize, 500)
    }
    
    return make_sonar_request("GET", "/metrics/search", params=params)


@mcp.tool()
def get_raw_source(
    key: str,
    branch: Optional[str] = None,
    pullRequest: Optional[str] = None
) -> dict:
    """
    Get source code as raw text from SonarQube
    Requires 'See Source Code' permission on file
    
    Args:
        key: File key
        branch: Optional branch key
        pullRequest: Optional pull request id
    """
    params = {"key": key}
    
    if branch:
        params["branch"] = branch
    if pullRequest:
        params["pullRequest"] = pullRequest
    
    return make_sonar_request("GET", "/sources/raw", params=params)


@mcp.tool()
def get_scm_info(
    key: str,
    commitsByLine: bool = False,
    from_line: Optional[int] = None,
    to_line: Optional[int] = None
) -> dict:
    """
    Get SCM information of SonarQube source files
    Requires 'See Source Code' permission on file's project
    
    Args:
        key: File key
        commitsByLine: Group lines by SCM commit if false, else display commits for each line
        from_line: First line to return (starts at 1)
        to_line: Last line to return (inclusive)
    """
    params = {
        "key": key,
        "commits_by_line": str(commitsByLine).lower()
    }
    
    if from_line:
        params["from"] = from_line
    if to_line:
        params["to"] = to_line
    
    return make_sonar_request("GET", "/sources/scm", params=params)


@mcp.tool()
def get_system_health() -> dict:
    """
    Get the health status of SonarQube Server instance
    Returns GREEN, YELLOW, or RED
    """
    return make_sonar_request("GET", "/system/health")


@mcp.tool()
def get_system_status() -> dict:
    """
    Get state information about SonarQube Server
    Returns status, version, and id
    """
    return make_sonar_request("GET", "/system/status")


@mcp.tool()
def get_system_logs(name: str = "app") -> dict:
    """
    Get SonarQube Server system logs in plain-text format
    Requires system administration permission
    
    Args:
        name: Name of the logs (access, app, ce, deprecation, es, web). Default: app
    """
    params = {"name": name}
    return make_sonar_request("GET", "/system/logs", params=params)


@mcp.tool()
def ping_system() -> dict:
    """
    Ping the SonarQube Server system to check if it's alive
    Returns 'pong' as plain text
    """
    return make_sonar_request("GET", "/system/ping")


@mcp.tool()
def get_system_info() -> dict:
    """
    Get detailed information about SonarQube Server system configuration
    Includes JVM state, database, search indexes, and settings
    Requires 'Administer' permissions
    """
    return make_sonar_request("GET", "/system/info")


@mcp.tool()
def create_webhook(
    name: str,
    url: str,
    project: Optional[str] = None,
    secret: Optional[str] = None
) -> dict:
    """
    Create a new webhook for the SonarQube organization or project
    Requires 'Administer' permission
    
    Args:
        name: Name of the webhook
        url: Server endpoint that will receive the webhook payload
        project: Optional project key
        secret: Optional secret for HMAC hex digest generation
    """
    params = {
        "name": name,
        "url": url
    }
    
    if project:
        params["project"] = project
    if secret:
        params["secret"] = secret
    
    return make_sonar_request("POST", "/webhooks/create", params=params)


@mcp.tool()
def list_webhooks(project: Optional[str] = None) -> dict:
    """
    List all webhooks for the SonarQube organization or project
    Requires 'Administer' permission
    
    Args:
        project: Optional project key to list project-specific webhooks
    """
    params = {}
    if project:
        params["project"] = project
    
    return make_sonar_request("GET", "/webhooks/list", params=params)


@mcp.tool()
def list_portfolios(
    enterpriseId: Optional[str] = None,
    q: Optional[str] = None,
    favorite: Optional[bool] = None,
    draft: Optional[bool] = None,
    pageIndex: int = 1,
    pageSize: int = 100
) -> dict:
    """
    List portfolios available in SonarQube with filtering and pagination options
    
    Args:
        enterpriseId: Enterprise uuid (SonarQube Cloud only)
        q: Search query to filter portfolios by name
        favorite: If true, only returns favorite portfolios
        draft: If true, only returns drafts created by logged-in user
        pageIndex: Index of the page to fetch (default: 1)
        pageSize: Size of the page to fetch
    """
    params = {
        "p": pageIndex,
        "ps": pageSize
    }
    
    if enterpriseId:
        params["enterpriseId"] = enterpriseId
    if q:
        params["q"] = q
    if favorite is not None:
        params["favorite"] = str(favorite).lower()
    if draft is not None:
        params["draft"] = str(draft).lower()
    
    return make_sonar_request("GET", "/views/search", params=params)


@mcp.tool()
def list_enterprises(enterpriseKey: Optional[str] = None) -> dict:
    """
    List the enterprises available in SonarQube Cloud that you have access to
    
    Args:
        enterpriseKey: Optional enterprise key to filter results
    """
    params = {}
    if enterpriseKey:
        params["enterpriseKey"] = enterpriseKey
    
    return make_sonar_request("GET", "/enterprises/search", params=params)


@mcp.tool()
def search_dependency_risks(
    projectKey: str,
    branchKey: Optional[str] = None,
    pullRequestKey: Optional[str] = None
) -> dict:
    """
    Search for software composition analysis issues (dependency risks) of a SonarQube project
    
    Args:
        projectKey: Project key
        branchKey: Optional branch key
        pullRequestKey: Optional pull request key
    """
    params = {"projectKey": projectKey}
    
    if branchKey:
        params["branch"] = branchKey
    if pullRequestKey:
        params["pullRequest"] = pullRequestKey
    
    return make_sonar_request("GET", "/dependencies/search", params=params)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
