"""
Configuration module for LightRAG MCP server.
"""

import argparse
from dataclasses import dataclass

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9621
DEFAULT_SSL_PORT = 443
DEFAULT_API_KEY = ""

DEFAULT_MCP_TRANSPORT = "stdio"
DEFAULT_MCP_HOST = "127.0.0.1"
DEFAULT_MCP_PORT = 8000
DEFAULT_MCP_STREAMABLE_HTTP_PATH = "/mcp"


@dataclass(frozen=True)
class LightRAGSettings:
    """Settings for connecting to the LightRAG API server."""

    host: str
    port: int
    api_key: str
    ssl: bool = False

    @property
    def base_url(self) -> str:
        scheme = "https" if self.ssl else "http"
        # Omit the port when it is the scheme's default (https -> 443, http -> 80).
        default_port = 443 if self.ssl else 80
        port_suffix = "" if self.port == default_port else f":{self.port}"
        return f"{scheme}://{self.host}{port_suffix}"


@dataclass(frozen=True)
class MCPSettings:
    """Settings for MCP transport and HTTP server."""

    transport: str
    host: str
    port: int
    streamable_http_path: str
    stateless_http: bool
    json_response: bool

    @property
    def streamable_http_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.streamable_http_path}"


def _normalize_path(path: str) -> str:
    if not path.startswith("/"):
        return f"/{path}"
    return path


def parse_args():
    """Parse command line arguments for LightRAG MCP server."""
    parser = argparse.ArgumentParser(description="LightRAG MCP Server")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"LightRAG API host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=(
            "LightRAG API port "
            f"(default: {DEFAULT_PORT}, or {DEFAULT_SSL_PORT} when --ssl is set)"
        ),
    )
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="LightRAG API key (optional)")
    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Use HTTPS instead of HTTP (default: False)",
    )
    parser.add_argument(
        "--mcp-transport",
        choices=["stdio", "streamable-http"],
        default=DEFAULT_MCP_TRANSPORT,
        help=f"MCP transport (default: {DEFAULT_MCP_TRANSPORT})",
    )
    parser.add_argument(
        "--mcp-host",
        default=DEFAULT_MCP_HOST,
        help=f"MCP HTTP host (default: {DEFAULT_MCP_HOST})",
    )
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=DEFAULT_MCP_PORT,
        help=f"MCP HTTP port (default: {DEFAULT_MCP_PORT})",
    )
    parser.add_argument(
        "--mcp-streamable-http-path",
        default=DEFAULT_MCP_STREAMABLE_HTTP_PATH,
        help=(
            "Streamable HTTP path for MCP endpoint "
            f"(default: {DEFAULT_MCP_STREAMABLE_HTTP_PATH})"
        ),
    )
    parser.add_argument(
        "--mcp-stateless-http",
        action="store_true",
        help="Enable stateless Streamable HTTP mode (new session per request)",
    )
    parser.add_argument(
        "--mcp-json-response",
        action="store_true",
        help="Return JSON responses instead of SSE for Streamable HTTP",
    )
    return parser.parse_args()


args = parse_args()

# Resolve the API port: an explicit --port always wins, otherwise pick the
# default for the scheme (443 for HTTPS, 9621 for plain HTTP).
if args.port is not None:
    _lightrag_port = args.port
else:
    _lightrag_port = DEFAULT_SSL_PORT if args.ssl else DEFAULT_PORT

LIGHTRAG = LightRAGSettings(
    host=args.host,
    port=_lightrag_port,
    api_key=args.api_key,
    ssl=args.ssl,
)
MCP = MCPSettings(
    transport=args.mcp_transport,
    host=args.mcp_host,
    port=args.mcp_port,
    streamable_http_path=_normalize_path(args.mcp_streamable_http_path),
    stateless_http=args.mcp_stateless_http,
    json_response=args.mcp_json_response,
)

LIGHTRAG_API_HOST = LIGHTRAG.host
LIGHTRAG_API_PORT = LIGHTRAG.port
LIGHTRAG_API_KEY = LIGHTRAG.api_key
LIGHTRAG_API_SSL = LIGHTRAG.ssl
LIGHTRAG_API_BASE_URL = LIGHTRAG.base_url

MCP_TRANSPORT = MCP.transport
MCP_HOST = MCP.host
MCP_PORT = MCP.port
MCP_STREAMABLE_HTTP_PATH = MCP.streamable_http_path
MCP_STATELESS_HTTP = MCP.stateless_http
MCP_JSON_RESPONSE = MCP.json_response
MCP_STREAMABLE_HTTP_URL = MCP.streamable_http_url
