#!/usr/bin/env python3
"""
Kubernetes FastMCP Server - Control local Kubernetes cluster via FastMCP
Compatible with mcp dev command
"""

import json
import logging
from typing import Any, Dict, List, Optional
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes import utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Kubernetes clients
core_v1 = None
apps_v1 = None
k8s_client = None

def initialize_k8s_client():
    """Initialize Kubernetes client"""
    global core_v1, apps_v1, k8s_client
    
    try:
        # Try to load in-cluster config first, then local config
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            config.load_kube_config()
            logger.info("Loaded local Kubernetes config")
        
        core_v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        k8s_client = client.ApiClient()
        
        # Test connection
        core_v1.list_namespace()
        logger.info("Successfully connected to Kubernetes cluster")
        
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes client: {e}")
        raise

# Initialize Kubernetes client at module level
try:
    initialize_k8s_client()
except Exception as e:
    logger.error(f"Failed to initialize Kubernetes: {e}")
    # Don't raise here, let individual functions handle the error

# Import FastMCP after K8s initialization
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("Kubernetes Controller")
except ImportError:
    # Fallback to newer FastMCP import
    try:
        from fastmcp import FastMCP
        mcp = FastMCP("Kubernetes Controller")
    except ImportError:
        logger.error("FastMCP not found. Please install with: pip install fastmcp")
        raise

@mcp.tool()
def get_pods(namespace: Optional[str] = None) -> str:
    """
    Get pods in a namespace or all namespaces
    
    Args:
        namespace: Kubernetes namespace (optional, gets all namespaces if not specified)
    
    Returns:
        JSON string with pod information
    """
    if not core_v1:
        return "Kubernetes client not initialized"
        
    try:
        if namespace:
            pods = core_v1.list_namespaced_pod(namespace=namespace)
        else:
            pods = core_v1.list_pod_for_all_namespaces()
        
        pod_info = []
        for pod in pods.items:
            pod_info.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "ready": sum(1 for c in (pod.status.conditions or []) if c.type == "Ready" and c.status == "True"),
                "restarts": sum(c.restart_count for c in (pod.status.container_statuses or [])),
                "node": pod.spec.node_name,
                "age": str(pod.metadata.creation_timestamp)
            })
        
        return json.dumps(pod_info, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e}"
    except Exception as e:
        return f"Error getting pods: {e}"

@mcp.tool()
def get_deployments(namespace: Optional[str] = None) -> str:
    """
    Get deployments in a namespace or all namespaces
    
    Args:
        namespace: Kubernetes namespace (optional, gets all namespaces if not specified)
    
    Returns:
        JSON string with deployment information
    """
    if not apps_v1:
        return "Kubernetes client not initialized"
        
    try:
        if namespace:
            deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
        else:
            deployments = apps_v1.list_deployment_for_all_namespaces()
        
        deployment_info = []
        for dep in deployments.items:
            deployment_info.append({
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "ready_replicas": dep.status.ready_replicas or 0,
                "replicas": dep.status.replicas or 0,
                "available_replicas": dep.status.available_replicas or 0,
                "updated_replicas": dep.status.updated_replicas or 0,
                "strategy": dep.spec.strategy.type if dep.spec.strategy else "Unknown",
                "age": str(dep.metadata.creation_timestamp)
            })
        
        return json.dumps(deployment_info, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e}"
    except Exception as e:
        return f"Error getting deployments: {e}"

@mcp.tool()
def get_services(namespace: Optional[str] = None) -> str:
    """
    Get services in a namespace or all namespaces
    
    Args:
        namespace: Kubernetes namespace (optional, gets all namespaces if not specified)
    
    Returns:
        JSON string with service information
    """
    if not core_v1:
        return "Kubernetes client not initialized"
        
    try:
        if namespace:
            services = core_v1.list_namespaced_service(namespace=namespace)
        else:
            services = core_v1.list_service_for_all_namespaces()
        
        service_info = []
        for svc in services.items:
            ports = []
            if svc.spec.ports:
                for p in svc.spec.ports:
                    ports.append({
                        "name": p.name,
                        "port": p.port,
                        "target_port": str(p.target_port),
                        "protocol": p.protocol
                    })
            
            service_info.append({
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "external_ips": svc.spec.external_i_ps or [],
                "ports": ports,
                "selector": svc.spec.selector or {},
                "age": str(svc.metadata.creation_timestamp)
            })
        
        return json.dumps(service_info, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e}"
    except Exception as e:
        return f"Error getting services: {e}"

@mcp.tool()
def get_namespaces() -> str:
    """
    Get all namespaces in the cluster
    
    Returns:
        JSON string with namespace information
    """
    if not core_v1:
        return "Kubernetes client not initialized"
        
    try:
        namespaces = core_v1.list_namespace()
        
        namespace_info = []
        for ns in namespaces.items:
            namespace_info.append({
                "name": ns.metadata.name,
                "status": ns.status.phase,
                "labels": ns.metadata.labels or {},
                "age": str(ns.metadata.creation_timestamp)
            })
        
        return json.dumps(namespace_info, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e}"
    except Exception as e:
        return f"Error getting namespaces: {e}"

@mcp.tool()
def scale_deployment(name: str, replicas: int, namespace: str = "default") -> str:
    """
    Scale a deployment to specified number of replicas
    
    Args:
        name: Deployment name
        replicas: Number of replicas to scale to
        namespace: Kubernetes namespace (default: "default")
    
    Returns:
        Success or error message
    """
    if not apps_v1:
        return "Kubernetes client not initialized"
        
    try:
        # Update deployment scale
        body = {"spec": {"replicas": replicas}}
        apps_v1.patch_namespaced_deployment_scale(
            name=name,
            namespace=namespace,
            body=body
        )
        
        return f"Successfully scaled deployment '{name}' in namespace '{namespace}' to {replicas} replicas"
    except ApiException as e:
        return f"Failed to scale deployment: {e}"
    except Exception as e:
        return f"Error scaling deployment: {e}"

@mcp.tool()
def delete_pod(name: str, namespace: str = "default") -> str:
    """
    Delete a specific pod
    
    Args:
        name: Pod name
        namespace: Kubernetes namespace (default: "default")
    
    Returns:
        Success or error message
    """
    if not core_v1:
        return "Kubernetes client not initialized"
        
    try:
        core_v1.delete_namespaced_pod(name=name, namespace=namespace)
        return f"Successfully deleted pod '{name}' in namespace '{namespace}'"
    except ApiException as e:
        return f"Failed to delete pod: {e}"
    except Exception as e:
        return f"Error deleting pod: {e}"

@mcp.tool()
def get_pod_logs(name: str, namespace: str = "default", container: Optional[str] = None, tail_lines: int = 100) -> str:
    """
    Get logs from a specific pod
    
    Args:
        name: Pod name
        namespace: Kubernetes namespace (default: "default")
        container: Container name (optional, uses first container if not specified)
        tail_lines: Number of lines to tail (default: 100)
    
    Returns:
        Pod logs or error message
    """
    if not core_v1:
        return "Kubernetes client not initialized"
        
    try:
        logs = core_v1.read_namespaced_pod_log(
            name=name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines
        )
        
        return f"Logs for pod '{name}' in namespace '{namespace}':\n{'-' * 50}\n{logs}"
    except ApiException as e:
        return f"Failed to get pod logs: {e}"
    except Exception as e:
        return f"Error getting pod logs: {e}"

@mcp.tool()
def restart_deployment(name: str, namespace: str = "default") -> str:
    """
    Restart a deployment by updating its restart annotation
    
    Args:
        name: Deployment name
        namespace: Kubernetes namespace (default: "default")
    
    Returns:
        Success or error message
    """
    if not apps_v1:
        return "Kubernetes client not initialized"
        
    try:
        from datetime import datetime
        
        # Add restart annotation to trigger rolling restart
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": datetime.now().isoformat()
                        }
                    }
                }
            }
        }
        
        apps_v1.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=body
        )
        
        return f"Successfully restarted deployment '{name}' in namespace '{namespace}'"
    except ApiException as e:
        return f"Failed to restart deployment: {e}"
    except Exception as e:
        return f"Error restarting deployment: {e}"

@mcp.tool()
def apply_yaml(yaml_content: str) -> str:
    """
    Apply a Kubernetes YAML manifest
    
    Args:
        yaml_content: YAML manifest content as string
    
    Returns:
        Results of applying the manifest
    """
    if not k8s_client:
        return "Kubernetes client not initialized"
        
    try:
        # Parse YAML
        docs = list(yaml.safe_load_all(yaml_content))
        results = []
        
        for doc in docs:
            if doc is None:
                continue
                
            try:
                # Use the dynamic client to apply the resource
                utils.create_from_dict(k8s_client, doc)
                kind = doc.get('kind', 'Unknown')
                name = doc.get('metadata', {}).get('name', 'unnamed')
                results.append(f"✓ Applied {kind} '{name}'")
            except Exception as e:
                kind = doc.get('kind', 'Unknown')
                name = doc.get('metadata', {}).get('name', 'unnamed')
                results.append(f"✗ Failed to apply {kind} '{name}': {e}")
        
        return "\n".join(results)
    except yaml.YAMLError as e:
        return f"YAML parsing error: {e}"
    except Exception as e:
        return f"Error applying YAML: {e}"

@mcp.tool()
def get_cluster_info() -> str:
    """
    Get basic cluster information including nodes and version
    
    Returns:
        JSON string with cluster information
    """
    if not k8s_client or not core_v1:
        return "Kubernetes client not initialized"
        
    try:
        # Get cluster version
        version_info = k8s_client.call_api('/version', 'GET', response_type='object')
        
        # Get node information
        nodes = core_v1.list_node()
        node_info = []
        for node in nodes.items:
            conditions = {c.type: c.status for c in node.status.conditions}
            
            node_info.append({
                "name": node.metadata.name,
                "status": "Ready" if conditions.get("Ready") == "True" else "NotReady",
                "version": node.status.node_info.kubelet_version,
                "os": node.status.node_info.os_image,
                "kernel": node.status.node_info.kernel_version,
                "container_runtime": node.status.node_info.container_runtime_version,
                "architecture": node.status.node_info.architecture,
                "roles": [k.replace('node-role.kubernetes.io/', '') for k in (node.metadata.labels or {}).keys() if k.startswith('node-role.kubernetes.io/')],
                "age": str(node.metadata.creation_timestamp)
            })
        
        cluster_info = {
            "kubernetes_version": version_info[0].get('gitVersion', 'Unknown'),
            "platform": version_info[0].get('platform', 'Unknown'),
            "nodes": node_info,
            "node_count": len(node_info),
            "ready_nodes": sum(1 for n in node_info if n["status"] == "Ready")
        }
        
        return json.dumps(cluster_info, indent=2)
    except Exception as e:
        return f"Error getting cluster info: {e}"

@mcp.tool()
def get_events(namespace: Optional[str] = None, limit: int = 20) -> str:
    """
    Get recent cluster events
    
    Args:
        namespace: Kubernetes namespace (optional, gets all namespaces if not specified)
        limit: Maximum number of events to return (default: 20)
    
    Returns:
        JSON string with event information
    """
    if not core_v1:
        return "Kubernetes client not initialized"
        
    try:
        if namespace:
            events = core_v1.list_namespaced_event(namespace=namespace, limit=limit)
        else:
            events = core_v1.list_event_for_all_namespaces(limit=limit)
        
        # Sort events by timestamp (most recent first)
        sorted_events = sorted(events.items, key=lambda x: x.last_timestamp or x.first_timestamp, reverse=True)
        
        event_info = []
        for event in sorted_events:
            event_info.append({
                "namespace": event.namespace,
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "object": f"{event.involved_object.kind}/{event.involved_object.name}",
                "count": event.count,
                "first_timestamp": str(event.first_timestamp),
                "last_timestamp": str(event.last_timestamp)
            })
        
        return json.dumps(event_info, indent=2)
    except ApiException as e:
        return f"Kubernetes API error: {e}"
    except Exception as e:
        return f"Error getting events: {e}"

@mcp.tool()
def describe_pod(name: str, namespace: str = "default") -> str:
    """
    Get detailed information about a specific pod
    
    Args:
        name: Pod name
        namespace: Kubernetes namespace (default: "default")
    
    Returns:
        Detailed pod information
    """
    if not core_v1:
        return "Kubernetes client not initialized"
        
    try:
        pod = core_v1.read_namespaced_pod(name=name, namespace=namespace)
        
        # Container information
        containers = []
        if pod.spec.containers:
            for container in pod.spec.containers:
                containers.append({
                    "name": container.name,
                    "image": container.image,
                    "ports": [{"containerPort": p.container_port, "protocol": p.protocol} for p in (container.ports or [])],
                    "resources": {
                        "requests": container.resources.requests or {} if container.resources else {},
                        "limits": container.resources.limits or {} if container.resources else {}
                    }
                })
        
        # Container statuses
        container_statuses = []
        if pod.status.container_statuses:
            for status in pod.status.container_statuses:
                container_statuses.append({
                    "name": status.name,
                    "ready": status.ready,
                    "restart_count": status.restart_count,
                    "image": status.image,
                    "state": str(status.state)
                })
        
        pod_details = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "labels": pod.metadata.labels or {},
            "annotations": pod.metadata.annotations or {},
            "phase": pod.status.phase,
            "node": pod.spec.node_name,
            "start_time": str(pod.status.start_time),
            "containers": containers,
            "container_statuses": container_statuses,
            "conditions": [{"type": c.type, "status": c.status, "reason": c.reason} for c in (pod.status.conditions or [])],
            "volumes": [v.name for v in (pod.spec.volumes or [])]
        }
        
        return json.dumps(pod_details, indent=2)
    except ApiException as e:
        return f"Failed to describe pod: {e}"
    except Exception as e:
        return f"Error describing pod: {e}"

# For compatibility with mcp dev command
if __name__ == "__main__":
    mcp.run()