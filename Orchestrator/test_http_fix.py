#!/usr/bin/env python3
"""Test script to verify nest_asyncio fix for HTTP MCP servers"""

import asyncio
import httpx
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

async def test_http_request():
    """Test HTTP request to docker-engine MCP server"""
    url = "http://0.0.0.0:4000/mcp"
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                url,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

def main():
    """Run the test in a sync context (like the orchestrator does)"""
    print("Testing HTTP communication with nest_asyncio fix...\n")
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(test_http_request())
    print(f"\nResult: {result}")

if __name__ == "__main__":
    main()