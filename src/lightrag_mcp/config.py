"""
Configuration module for LightRAG MCP server.
"""

import argparse

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9621
DEFAULT_API_KEY = ""


def parse_args():
    """Parse command line arguments for LightRAG MCP server."""
    parser = argparse.ArgumentParser(description="LightRAG MCP Server")
    parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"LightRAG API host (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"LightRAG API port (default: {DEFAULT_PORT})",
    )
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="LightRAG API key (optional)")
    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Use HTTPS instead of HTTP (default: False)",
    )
    return parser.parse_args()


args = parse_args()

LIGHTRAG_API_HOST = args.host
LIGHTRAG_API_PORT = args.port
LIGHTRAG_API_KEY = args.api_key
LIGHTRAG_API_SSL = args.ssl

_scheme = "https" if LIGHTRAG_API_SSL else "http"
_port_suffix = "" if (LIGHTRAG_API_SSL and LIGHTRAG_API_PORT == 443) or (not LIGHTRAG_API_SSL and LIGHTRAG_API_PORT == 9621) else f":{LIGHTRAG_API_PORT}"
LIGHTRAG_API_BASE_URL = f"{_scheme}://{LIGHTRAG_API_HOST}{_port_suffix}"
