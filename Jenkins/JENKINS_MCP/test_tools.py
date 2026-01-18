#!/usr/bin/env python3
"""
Test the Jenkins MCP tools directly
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jenkins_mcp_server.config import ServerConfig
from jenkins_mcp_server.client import SyncJenkinsClient


def test_jenkins_tools():
    """Test the Jenkins tools functionality."""
    print("🔧 Testing Jenkins MCP Tools")
    print("=" * 50)
    
    try:
        # Load configuration
        config = ServerConfig()
        jenkins_config = config.jenkins_config
        
        print(f"📡 Jenkins URL: {jenkins_config.url}")
        print(f"👤 Username: {jenkins_config.username}")
        print()
        
        # Create client (same as in main.py)
        def get_client():
            return SyncJenkinsClient(jenkins_config)
        
        # Test client creation
        print("🧪 Testing client creation...")
        client = get_client()
        print("✅ SyncJenkinsClient created successfully")
        
        # Test get_jobs method
        print("📋 Testing get_jobs method...")
        jobs = client.get_jobs()
        print(f"✅ Found {len(jobs)} jobs")
        
        # Test jenkins attribute access (for tools that use client.jenkins)
        print("🔧 Testing jenkins attribute access...")
        version = client.jenkins.get_version()
        print(f"✅ Jenkins version via client.jenkins: {version}")
        
        # Test a more complex operation like tools would use
        print("🏗️ Testing tool-like operation...")
        if jobs:
            first_job = jobs[0]
            job_name = first_job.get("name")
            job_info = client.jenkins.get_job_info(job_name)
            print(f"✅ Successfully got info for job: {job_name}")
        else:
            print("ℹ️ No jobs to test with, but that's OK")
        
        print()
        print("🎉 All tool tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_jenkins_tools()
    sys.exit(0 if success else 1)