#!/usr/bin/env python3
"""
Docker MCP Server
Complete Docker engine control through MCP for Claude Desktop
"""

import json
import subprocess
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Docker Engine Controller")

def run_docker_command(args: List[str], capture_output: bool = True) -> Dict[str, Any]:
    """Execute a docker command and return structured result."""
    try:
        cmd = ["docker"] + args
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=60
        )
        
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout.strip() if result.stdout else "",
            "stderr": result.stderr.strip() if result.stderr else "",
            "command": " ".join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 60 seconds",
            "command": " ".join(["docker"] + args)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": " ".join(["docker"] + args)
        }

@mcp.tool()
def list_containers(all_containers: bool = True, format_output: str = "table") -> str:
    """
    List Docker containers.
    
    Args:
        all_containers: If True, show all containers (default). If False, show only running.
        format_output: Output format - 'table' (default), 'json', or 'simple'
    """
    args = ["ps"]
    if all_containers:
        args.append("-a")
    
    if format_output == "json":
        args.extend(["--format", "json"])
    elif format_output == "simple":
        args.extend(["--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"])
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error listing containers: {result.get('error', result.get('stderr', 'Unknown error'))}"
    
    if format_output == "json" and result["stdout"]:
        try:
            # Docker outputs JSONL (one JSON object per line)
            lines = result["stdout"].strip().split('\n')
            containers = [json.loads(line) for line in lines if line.strip()]
            return json.dumps(containers, indent=2)
        except json.JSONDecodeError:
            return result["stdout"]
    
    return result["stdout"] if result["stdout"] else "No containers found"

@mcp.tool()
def container_info(container_id: str) -> str:
    """Get detailed information about a specific container."""
    result = run_docker_command(["inspect", container_id])
    
    if not result["success"]:
        return f"Error getting container info: {result.get('error', result.get('stderr', 'Container not found'))}"
    
    try:
        info = json.loads(result["stdout"])
        if info:
            container = info[0]
            return json.dumps({
                "Name": container.get("Name", "").lstrip("/"),
                "Image": container.get("Config", {}).get("Image", ""),
                "State": container.get("State", {}),
                "NetworkSettings": container.get("NetworkSettings", {}),
                "Mounts": container.get("Mounts", []),
                "Config": {
                    "Env": container.get("Config", {}).get("Env", []),
                    "Cmd": container.get("Config", {}).get("Cmd", []),
                    "WorkingDir": container.get("Config", {}).get("WorkingDir", ""),
                    "ExposedPorts": container.get("Config", {}).get("ExposedPorts", {})
                }
            }, indent=2)
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        return f"Error parsing container info: {str(e)}"
    
    return "Container not found"

@mcp.tool()
def container_logs(container_id: str, lines: int = 100, follow: bool = False, timestamps: bool = True) -> str:
    """
    Get logs from a container.
    
    Args:
        container_id: Container ID or name
        lines: Number of lines to retrieve (default: 100)
        follow: Whether to follow logs (not recommended for MCP)
        timestamps: Include timestamps in output
    """
    args = ["logs"]
    
    if timestamps:
        args.append("--timestamps")
    
    if not follow:  # For MCP, we don't want to follow logs
        args.extend(["--tail", str(lines)])
    
    args.append(container_id)
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error getting logs: {result.get('error', result.get('stderr', 'Container not found'))}"
    
    return result["stdout"] if result["stdout"] else "No logs available"

@mcp.tool()
def pull_image(image_name: str, tag: str = "latest") -> str:
    """Pull a Docker image from registry."""
    full_image = f"{image_name}:{tag}" if ":" not in image_name else image_name
    
    result = run_docker_command(["pull", full_image])
    
    if not result["success"]:
        return f"Error pulling image: {result.get('error', result.get('stderr', 'Pull failed'))}"
    
    return f"Successfully pulled {full_image}\n{result['stdout']}"

@mcp.tool()
def start_container(container_id: str) -> str:
    """Start a stopped container."""
    result = run_docker_command(["start", container_id])
    
    if not result["success"]:
        return f"Error starting container: {result.get('error', result.get('stderr', 'Start failed'))}"
    
    return f"Container {container_id} started successfully"

@mcp.tool()
def stop_container(container_id: str, force: bool = False) -> str:
    """
    Stop a running container.
    
    Args:
        container_id: Container ID or name
        force: Force stop (kill) the container
    """
    args = ["kill" if force else "stop", container_id]
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error stopping container: {result.get('error', result.get('stderr', 'Stop failed'))}"
    
    action = "killed" if force else "stopped"
    return f"Container {container_id} {action} successfully"

@mcp.tool()
def remove_container(container_id: str, force: bool = False, remove_volumes: bool = False) -> str:
    """
    Remove a container.
    
    Args:
        container_id: Container ID or name
        force: Force removal of running container
        remove_volumes: Remove associated volumes
    """
    args = ["rm"]
    
    if force:
        args.append("-f")
    if remove_volumes:
        args.append("-v")
    
    args.append(container_id)
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error removing container: {result.get('error', result.get('stderr', 'Remove failed'))}"
    
    return f"Container {container_id} removed successfully"

@mcp.tool()
def run_container(
    image: str, 
    name: Optional[str] = None,
    ports: Optional[str] = None,
    environment: Optional[str] = None,
    volumes: Optional[str] = None,
    detach: bool = True,
    remove: bool = False,
    command: Optional[str] = None
) -> str:
    """
    Run a new container.
    
    Args:
        image: Docker image to run
        name: Container name
        ports: Port mapping (e.g., "8080:80")
        environment: Environment variables (e.g., "KEY=value,KEY2=value2")
        volumes: Volume mounts (e.g., "/host/path:/container/path")
        detach: Run in background
        remove: Remove container when it stops
        command: Command to run in container
    """
    args = ["run"]
    
    if detach:
        args.append("-d")
    if remove:
        args.append("--rm")
    if name:
        args.extend(["--name", name])
    if ports:
        for port in ports.split(","):
            args.extend(["-p", port.strip()])
    if environment:
        for env in environment.split(","):
            args.extend(["-e", env.strip()])
    if volumes:
        for volume in volumes.split(","):
            args.extend(["-v", volume.strip()])
    
    args.append(image)
    
    if command:
        args.extend(command.split())
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error running container: {result.get('error', result.get('stderr', 'Run failed'))}"
    
    return f"Container started successfully\n{result['stdout']}"

@mcp.tool()
def list_images(all_images: bool = False) -> str:
    """
    List Docker images.
    
    Args:
        all_images: Show all images including intermediate layers
    """
    args = ["images"]
    if all_images:
        args.append("-a")
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error listing images: {result.get('error', result.get('stderr', 'Unknown error'))}"
    
    return result["stdout"] if result["stdout"] else "No images found"

@mcp.tool()
def remove_image(image_id: str, force: bool = False) -> str:
    """
    Remove a Docker image.
    
    Args:
        image_id: Image ID or name
        force: Force removal
    """
    args = ["rmi"]
    if force:
        args.append("-f")
    args.append(image_id)
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error removing image: {result.get('error', result.get('stderr', 'Remove failed'))}"
    
    return f"Image {image_id} removed successfully"

@mcp.tool()
def docker_stats(container_id: Optional[str] = None, no_stream: bool = True) -> str:
    """
    Get container resource usage statistics.
    
    Args:
        container_id: Specific container to monitor (optional)
        no_stream: Get current stats without streaming
    """
    args = ["stats"]
    if no_stream:
        args.append("--no-stream")
    if container_id:
        args.append(container_id)
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error getting stats: {result.get('error', result.get('stderr', 'Stats failed'))}"
    
    return result["stdout"] if result["stdout"] else "No stats available"

@mcp.tool()
def exec_in_container(container_id: str, command: str, interactive: bool = False) -> str:
    """
    Execute a command inside a running container.
    
    Args:
        container_id: Container ID or name
        command: Command to execute
        interactive: Run in interactive mode
    """
    args = ["exec"]
    if interactive:
        args.append("-it")
    
    args.extend([container_id, "sh", "-c", command])
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error executing command: {result.get('error', result.get('stderr', 'Exec failed'))}"
    
    return result["stdout"] if result["stdout"] else "Command executed (no output)"

@mcp.tool()
def docker_system_info() -> str:
    """Get Docker system information and status."""
    result = run_docker_command(["system", "info", "--format", "json"])
    
    if not result["success"]:
        return f"Error getting system info: {result.get('error', result.get('stderr', 'Info failed'))}"
    
    try:
        info = json.loads(result["stdout"])
        return json.dumps({
            "ServerVersion": info.get("ServerVersion"),
            "Architecture": info.get("Architecture"),
            "OSType": info.get("OSType"),
            "KernelVersion": info.get("KernelVersion"),
            "TotalMemory": info.get("MemTotal"),
            "ContainersRunning": info.get("ContainersRunning"),
            "ContainersStopped": info.get("ContainersStopped"),
            "Images": info.get("Images"),
            "DockerRootDir": info.get("DockerRootDir"),
            "Driver": info.get("Driver")
        }, indent=2)
    except json.JSONDecodeError:
        return result["stdout"]

@mcp.tool()
def docker_system_df() -> str:
    """Show Docker system disk usage."""
    result = run_docker_command(["system", "df", "-v"])
    
    if not result["success"]:
        return f"Error getting disk usage: {result.get('error', result.get('stderr', 'DF failed'))}"
    
    return result["stdout"]

@mcp.tool()
def prune_system(containers: bool = False, images: bool = False, volumes: bool = False, networks: bool = False, all_unused: bool = False) -> str:
    """
    Clean up Docker system by removing unused resources.
    
    Args:
        containers: Remove stopped containers
        images: Remove unused images
        volumes: Remove unused volumes
        networks: Remove unused networks
        all_unused: Remove all unused resources (equivalent to docker system prune -a)
    """
    if all_unused:
        result = run_docker_command(["system", "prune", "-a", "-f"])
        if not result["success"]:
            return f"Error pruning system: {result.get('error', result.get('stderr'))}"
        return f"System cleanup completed:\n{result['stdout']}"
    
    results = []
    
    if containers:
        result = run_docker_command(["container", "prune", "-f"])
        if result["success"]:
            results.append(f"Containers: {result['stdout']}")
        else:
            results.append(f"Container cleanup failed: {result.get('stderr')}")
    
    if images:
        result = run_docker_command(["image", "prune", "-f"])
        if result["success"]:
            results.append(f"Images: {result['stdout']}")
        else:
            results.append(f"Image cleanup failed: {result.get('stderr')}")
    
    if volumes:
        result = run_docker_command(["volume", "prune", "-f"])
        if result["success"]:
            results.append(f"Volumes: {result['stdout']}")
        else:
            results.append(f"Volume cleanup failed: {result.get('stderr')}")
    
    if networks:
        result = run_docker_command(["network", "prune", "-f"])
        if result["success"]:
            results.append(f"Networks: {result['stdout']}")
        else:
            results.append(f"Network cleanup failed: {result.get('stderr')}")
    
    return "\n".join(results) if results else "No cleanup operations specified"

@mcp.tool()
def list_networks() -> str:
    """List Docker networks."""
    result = run_docker_command(["network", "ls"])
    
    if not result["success"]:
        return f"Error listing networks: {result.get('error', result.get('stderr'))}"
    
    return result["stdout"]

@mcp.tool()
def list_volumes() -> str:
    """List Docker volumes."""
    result = run_docker_command(["volume", "ls"])
    
    if not result["success"]:
        return f"Error listing volumes: {result.get('error', result.get('stderr'))}"
    
    return result["stdout"]

@mcp.tool()
def create_volume(volume_name: str, driver: str = "local") -> str:
    """Create a new Docker volume."""
    result = run_docker_command(["volume", "create", "--driver", driver, volume_name])
    
    if not result["success"]:
        return f"Error creating volume: {result.get('error', result.get('stderr'))}"
    
    return f"Volume '{volume_name}' created successfully"

@mcp.tool()
def inspect_volume(volume_name: str) -> str:
    """Inspect a Docker volume."""
    result = run_docker_command(["volume", "inspect", volume_name])
    
    if not result["success"]:
        return f"Error inspecting volume: {result.get('error', result.get('stderr'))}"
    
    try:
        volume_info = json.loads(result["stdout"])
        return json.dumps(volume_info, indent=2)
    except json.JSONDecodeError:
        return result["stdout"]

@mcp.tool()
def copy_from_container(container_id: str, container_path: str, host_path: str) -> str:
    """Copy files/folders from container to host."""
    result = run_docker_command(["cp", f"{container_id}:{container_path}", host_path])
    
    if not result["success"]:
        return f"Error copying from container: {result.get('error', result.get('stderr'))}"
    
    return f"Successfully copied {container_path} from {container_id} to {host_path}"

@mcp.tool()
def copy_to_container(host_path: str, container_id: str, container_path: str) -> str:
    """Copy files/folders from host to container."""
    result = run_docker_command(["cp", host_path, f"{container_id}:{container_path}"])
    
    if not result["success"]:
        return f"Error copying to container: {result.get('error', result.get('stderr'))}"
    
    return f"Successfully copied {host_path} to {container_id}:{container_path}"

@mcp.tool()
def build_image(dockerfile_path: str, tag: str, build_context: str = ".") -> str:
    """
    Build a Docker image from Dockerfile.
    
    Args:
        dockerfile_path: Path to Dockerfile
        tag: Tag for the built image
        build_context: Build context path (default: current directory)
    """
    args = ["build", "-f", dockerfile_path, "-t", tag, build_context]
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error building image: {result.get('error', result.get('stderr'))}"
    
    return f"Image '{tag}' built successfully\n{result['stdout']}"

@mcp.tool()
def docker_compose_up(compose_file: str = "docker-compose.yml", detach: bool = True, build: bool = False) -> str:
    """
    Start services using docker-compose.
    
    Args:
        compose_file: Path to docker-compose file
        detach: Run in background
        build: Build images before starting
    """
    args = ["compose", "-f", compose_file, "up"]
    
    if detach:
        args.append("-d")
    if build:
        args.append("--build")
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error starting compose services: {result.get('error', result.get('stderr'))}"
    
    return f"Compose services started successfully\n{result['stdout']}"

@mcp.tool()
def docker_compose_down(compose_file: str = "docker-compose.yml", remove_volumes: bool = False) -> str:
    """
    Stop and remove compose services.
    
    Args:
        compose_file: Path to docker-compose file
        remove_volumes: Remove named volumes
    """
    args = ["compose", "-f", compose_file, "down"]
    
    if remove_volumes:
        args.append("-v")
    
    result = run_docker_command(args)
    
    if not result["success"]:
        return f"Error stopping compose services: {result.get('error', result.get('stderr'))}"
    
    return f"Compose services stopped successfully\n{result['stdout']}"

@mcp.tool()
def search_images(term: str, limit: int = 10) -> str:
    """Search Docker Hub for images."""
    result = run_docker_command(["search", "--limit", str(limit), term])
    
    if not result["success"]:
        return f"Error searching images: {result.get('error', result.get('stderr'))}"
    
    return result["stdout"]

@mcp.tool()
def container_top(container_id: str) -> str:
    """Show running processes in a container."""
    result = run_docker_command(["top", container_id])
    
    if not result["success"]:
        return f"Error getting container processes: {result.get('error', result.get('stderr'))}"
    
    return result["stdout"]

@mcp.tool()
def restart_container(container_id: str, timeout: int = 10) -> str:
    """
    Restart a container.
    
    Args:
        container_id: Container ID or name
        timeout: Seconds to wait for stop before killing
    """
    result = run_docker_command(["restart", "-t", str(timeout), container_id])
    
    if not result["success"]:
        return f"Error restarting container: {result.get('error', result.get('stderr'))}"
    
    return f"Container {container_id} restarted successfully"

@mcp.resource("docker://status")
def docker_status():
    """Get current Docker engine status and summary."""
    # Get system info
    system_result = run_docker_command(["system", "info", "--format", "json"])
    
    # Get container summary
    containers_result = run_docker_command(["ps", "-a", "--format", "json"])
    
    # Get image summary
    images_result = run_docker_command(["images", "--format", "json"])
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "docker_available": system_result["success"],
    }
    
    if system_result["success"]:
        try:
            system_info = json.loads(system_result["stdout"])
            status.update({
                "version": system_info.get("ServerVersion", "unknown"),
                "containers_running": system_info.get("ContainersRunning", 0),
                "containers_stopped": system_info.get("ContainersStopped", 0),
                "images": system_info.get("Images", 0)
            })
        except json.JSONDecodeError:
            status["system_info_error"] = "Could not parse system info"
    else:
        status["error"] = system_result.get("error", "Docker not available")
    
    return status

@mcp.prompt("docker-help")
def docker_help():
    """Comprehensive help for Docker MCP server commands."""
    return """
# Docker MCP Server Help

This MCP server provides comprehensive Docker engine control through Claude. Here are the available commands:

## Container Management
- **list_containers()** - View all containers (running and stopped)
- **container_info(container_id)** - Get detailed container information
- **container_logs(container_id, lines=100)** - View container logs
- **start_container(container_id)** - Start a stopped container
- **stop_container(container_id, force=False)** - Stop a running container
- **restart_container(container_id)** - Restart a container
- **remove_container(container_id, force=False)** - Remove a container
- **container_top(container_id)** - Show processes running in container
- **exec_in_container(container_id, command)** - Execute command in container

## Image Management
- **list_images()** - List all Docker images
- **pull_image(image_name, tag="latest")** - Pull image from registry
- **remove_image(image_id, force=False)** - Remove an image
- **build_image(dockerfile_path, tag)** - Build image from Dockerfile
- **search_images(term, limit=10)** - Search Docker Hub

## Container Operations
- **run_container(image, name=None, ports=None, ...)** - Run new container
- **copy_from_container(container_id, container_path, host_path)** - Copy files from container
- **copy_to_container(host_path, container_id, container_path)** - Copy files to container

## System Management
- **docker_system_info()** - Get Docker system information
- **docker_system_df()** - Show disk usage
- **docker_stats(container_id=None)** - Get resource usage statistics
- **prune_system(containers=False, images=False, ...)** - Clean up unused resources

## Network & Volume Management
- **list_networks()** - List Docker networks
- **list_volumes()** - List Docker volumes
- **create_volume(volume_name)** - Create a new volume
- **inspect_volume(volume_name)** - Inspect volume details

## Docker Compose
- **docker_compose_up(compose_file)** - Start compose services
- **docker_compose_down(compose_file)** - Stop compose services

## Resources
- **docker://status** - Current Docker engine status and summary

## Example Usage with Claude:
- "Show me all running containers"
- "Pull the nginx:latest image"
- "Get logs for container web-server"
- "Stop the container named my-app"
- "Show me Docker system information"
- "Clean up all unused Docker resources"
"""

if __name__ == "__main__":
    # Run with HTTP transport instead of stdio
    mcp.run(transport="http", host="0.0.0.0", port=4000)