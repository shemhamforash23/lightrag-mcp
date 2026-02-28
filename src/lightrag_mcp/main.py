"""
Entry point for LightRAG MCP server.
"""

import logging
import sys

from lightrag_mcp import config
from lightrag_mcp.server import mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main():
    """Main function for server startup."""
    try:
        log_level = getattr(logging, "INFO")
        logging.getLogger().setLevel(log_level)

        logger.info("Starting LightRAG MCP server")
        logger.info(
            "LightRAG API server is expected to be already running and available at: "
            f"{config.LIGHTRAG.base_url}"
        )
        logger.info(f"MCP transport: {config.MCP_TRANSPORT}")
        if config.MCP_TRANSPORT == "streamable-http":
            logger.info(f"Streamable HTTP endpoint: {config.MCP_STREAMABLE_HTTP_URL}")
            if config.MCP_STATELESS_HTTP:
                logger.info("Streamable HTTP mode: stateless")
            if config.MCP_JSON_RESPONSE:
                logger.info("Streamable HTTP mode: json_response")

        if config.LIGHTRAG.api_key:
            logger.info("API key is configured")
        else:
            logger.warning("No API key provided")

        mcp.run(transport=config.MCP_TRANSPORT)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Error starting server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
