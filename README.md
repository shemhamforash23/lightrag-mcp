[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/shemhamforash23-lightrag-mcp-badge.png)](https://mseep.ai/app/shemhamforash23-lightrag-mcp)

# LightRAG MCP Server

MCP server for integrating LightRAG with AI tools. Provides a unified interface for interacting with LightRAG API through the MCP protocol.

## Description

LightRAG MCP Server is a bridge between LightRAG API and MCP-compatible clients. It allows using LightRAG (Retrieval-Augmented Generation) capabilities in various AI tools that support the MCP protocol.

### Key Features

- **Information Retrieval**: Execute semantic and keyword queries to documents
- **Document Management**: Upload, index, and track document status
- **Knowledge Graph Operations**: Manage entities and relationships in the knowledge graph
- **Monitoring**: Check LightRAG API status and document processing

## Installation

This server is designed to be used as an MCP server and should be installed in a virtual environment using uv, not as a system-wide package.

### Development Installation

```bash
# Create a virtual environment
uv venv --python 3.11

# Install the package in development mode
uv pip install -e .
```

## Requirements

- Python 3.11+
- Running LightRAG API server

## Usage

**Important**: LightRAG MCP server should only be run as an MCP server through an MCP client configuration file (mcp-config.json).

### Command Line Options

The following arguments are available when configuring the server in mcp-config.json:

- `--host`: LightRAG API host (default: localhost)
- `--port`: LightRAG API port (default: 9621)
- `--api-key`: LightRAG API key (optional)
- `--ssl`: Use HTTPS instead of HTTP (default: False)

### Integration with LightRAG API

The MCP server requires a running LightRAG API server. Start it as follows:

```bash
# Create virtual environment
uv venv --python 3.11

# Install dependencies
uv pip install -r LightRAG/lightrag/api/requirements.txt

# Start LightRAG API
uv run LightRAG/lightrag/api/lightrag_server.py --host localhost --port 9621 --working-dir ./rag_storage --input-dir ./input --llm-binding openai --embedding-binding openai --log-level DEBUG
```

### Setting up as MCP server

To set up LightRAG MCP as an MCP server, add the following configuration to your MCP client configuration file (e.g., `mcp-config.json`):

#### Using uvenv (uvx):

```json
{
  "mcpServers": {
    "lightrag-mcp": {
      "command": "uvx",
      "args": [
        "lightrag_mcp",
        "--host",
        "localhost",
        "--port",
        "9621",
        "--api-key",
        "your_api_key"
      ]
    }
  }
}
```

#### Using HTTPS (SSL):

```json
{
  "mcpServers": {
    "lightrag-mcp": {
      "command": "uvx",
      "args": [
        "lightrag_mcp",
        "--host",
        "lightrag.example.com",
        "--ssl"
      ]
    }
  }
}
```

#### Development

```json
{
  "mcpServers": {
    "lightrag-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/lightrag_mcp",
        "run",
        "src/lightrag_mcp/main.py",
        "--host",
        "localhost",
        "--port",
        "9621",
        "--api-key",
        "your_api_key"
      ]
    }
  }
}
```

Replace `/path/to/lightrag_mcp` with the actual path to your lightrag-mcp directory.

## Available MCP Tools

### Document Queries
- `query_document`: Execute a query to documents through LightRAG API

### Document Management
- `insert_document`: Add text directly to LightRAG storage
- `upload_document`: Upload document from file to the /input directory
- `insert_file`: Add document from file directly to storage
- `insert_batch`: Add batch of documents from directory
- `scan_for_new_documents`: Start scanning the /input directory for new documents
- `get_documents`: Get list of all uploaded documents
- `get_pipeline_status`: Get status of document processing in pipeline

### Knowledge Graph Operations
- `get_graph_labels`: Get labels (node and relationship types) from knowledge graph
- `create_entities`: Create multiple entities in knowledge graph
- `edit_entities`: Edit multiple existing entities in knowledge graph
- `delete_by_entities`: Delete multiple entities from knowledge graph by name
- `delete_by_doc_ids`: Delete all entities and relationships associated with multiple documents
- `create_relations`: Create multiple relationships between entities in knowledge graph
- `edit_relations`: Edit multiple relationships between entities in knowledge graph
- `merge_entities`: Merge multiple entities into one with relationship migration

### Monitoring
- `check_lightrag_health`: Check LightRAG API status

## Development

### Installing development dependencies

```bash
uv pip install -e ".[dev]"
```

### Running linters

```bash
ruff check src/
mypy src/
```

## License

MIT
