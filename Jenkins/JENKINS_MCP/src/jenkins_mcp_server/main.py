"""Main entry point for the Jenkins MCP Server."""

import asyncio
from fastmcp import FastMCP

from .config import JenkinsConfig, ServerConfig
from .utils.logging import get_logger
from .tools import register_all_tools
from .resources import register_all_resources
# from .prompts import register_all_prompts  # TODO: Fix syntax issues
from .client import AsyncJenkinsClient, SyncJenkinsClient


logger = get_logger("main")


async def main():
    """Main entry point for the Jenkins MCP Server."""
    logger.info("Starting Jenkins MCP Server...")
    
    # Load configuration
    server_config = ServerConfig()
    jenkins_config = server_config.jenkins_config
    
    logger.info(f"Jenkins URL: {jenkins_config.url}")
    logger.info(f"Server Host: {server_config.host}:{server_config.port}")
    
    # Create FastMCP server
    mcp = FastMCP("Jenkins MCP Server")
    
    # Create client factory function
    def get_client():
        """Get Jenkins client instance."""
        return SyncJenkinsClient(jenkins_config)
    
    # Add health check tool
    @mcp.tool()
    async def health_check() -> str:
        """
        Check the health status of the Jenkins MCP Server.
        
        Returns:
            Health status information
        """
        try:
            # Test Jenkins connection using sync client
            client = get_client()
            version = client.get_version()
                
            return f"OK - Jenkins MCP Server is healthy. Connected to Jenkins {version}"
        except Exception as e:
            return f"ERROR - Jenkins MCP Server health check failed: {str(e)}"
    
    # Register components
    register_all_tools(mcp, get_client)
    register_all_resources(mcp, get_client) 
    # TODO: Fix prompts module syntax issues
    # register_all_prompts(mcp)
    
    logger.info("Tools and resources registered successfully")
    logger.info("Jenkins MCP Server is ready!")
    
    # Run the server using stdio
    await mcp.run_stdio_async()


def sync_main():
    """Synchronous main entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    sync_main()