#!/usr/bin/env python3
"""
Jenkins MCP Server Connection Test

This script tests the connection between the MCP server and Jenkins.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jenkins_mcp_server.config import ServerConfig
from jenkins_mcp_server.client import AsyncJenkinsClient


async def test_jenkins_connection():
    """Test the Jenkins connection and display diagnostics."""
    print("🔧 Jenkins MCP Server Connection Test")
    print("=" * 50)
    
    try:
        # Load configuration
        config = ServerConfig()
        jenkins_config = config.jenkins_config
        
        print(f"📡 Jenkins URL: {jenkins_config.url}")
        print(f"👤 Username: {jenkins_config.username}")
        print(f"🔑 Token: {'*' * len(jenkins_config.token) if jenkins_config.token else 'Not set'}")
        print(f"🔒 SSL Verify: {jenkins_config.verify_ssl}")
        print(f"⏱️  Timeout: {jenkins_config.timeout}s")
        print()
        
        # Test connection using the sync client (which has the high-level methods)
        print("🧪 Testing Jenkins connection...")
        from jenkins_mcp_server.client import SyncJenkinsClient
        
        client = SyncJenkinsClient(jenkins_config)
        
        # Test basic connectivity
        version = client.get_version()
        
        print("✅ Connection successful!")
        print(f"   Jenkins Version: {version}")
        print()
        
        # Test listing jobs
        print("📋 Testing job listing...")
        try:
            jobs = client.get_jobs()
            print(f"✅ Found {len(jobs)} jobs")
            if jobs:
                print("   Sample jobs:")
                for job in jobs[:3]:  # Show first 3 jobs
                    print(f"   - {job.get('name', 'Unnamed')}")
            else:
                print("   No jobs found (this is normal for a new Jenkins instance)")
            print()
        except Exception as e:
            print(f"⚠️  Job listing failed: {e}")
            print()
        
        # Test async client basic functionality
        print("🔧 Testing async client...")
        async with AsyncJenkinsClient(jenkins_config) as async_client:
            try:
                # Test getting Jenkins API root
                api_data = await async_client.get_json("api/json")
                print(f"✅ Async client working - Jenkins mode: {api_data.get('mode', 'Unknown')}")
            except Exception as e:
                print(f"⚠️  Async client test failed: {e}")
        print()
            
        return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("🛠️  Troubleshooting tips:")
        print("   1. Verify Jenkins is running at the configured URL")
        print("   2. Check username and API token are correct")
        print("   3. Ensure the API token has appropriate permissions")
        print("   4. Check if Jenkins requires CSRF protection")
        print("   5. Verify network connectivity")
        return False


async def test_mcp_server_startup():
    """Test if the MCP server can start up properly."""
    print("🚀 Testing MCP Server Startup")
    print("=" * 50)
    
    try:
        from jenkins_mcp_server.main import main
        from fastmcp import FastMCP
        
        # Create a basic server to test initialization
        mcp = FastMCP("Test Jenkins MCP Server")
        print("✅ FastMCP instance created successfully")
        
        # Test configuration loading
        config = ServerConfig()
        print("✅ Configuration loaded successfully")
        
        print("✅ MCP server components initialized successfully")
        print()
        return True
        
    except Exception as e:
        print(f"❌ MCP server startup failed: {e}")
        print()
        return False


async def main():
    """Run all tests."""
    print("Jenkins MCP Server Diagnostic Tool")
    print("=" * 60)
    print()
    
    # Test Jenkins connection
    jenkins_ok = await test_jenkins_connection()
    
    # Test MCP server startup
    mcp_ok = await test_mcp_server_startup()
    
    print("📊 Test Summary")
    print("=" * 50)
    print(f"Jenkins Connection: {'✅ PASS' if jenkins_ok else '❌ FAIL'}")
    print(f"MCP Server Startup: {'✅ PASS' if mcp_ok else '❌ FAIL'}")
    print()
    
    if jenkins_ok and mcp_ok:
        print("🎉 All tests passed! Your Jenkins MCP server should work properly.")
        print()
        print("📋 Next steps:")
        print("   1. Copy the claude_desktop_config.json to your Claude Desktop config")
        print("   2. Restart Claude Desktop")
        print("   3. Test the connection by asking Claude about Jenkins")
    else:
        print("⚠️  Some tests failed. Please address the issues above.")
        
    return jenkins_ok and mcp_ok


if __name__ == "__main__":
    import asyncio
    exit_code = 0 if asyncio.run(main()) else 1
    sys.exit(exit_code)