"""
Main module for LightRAG MCP server.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Union, cast

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from lightrag_mcp import config
from lightrag_mcp.lightrag_client import LightRAGClient

logger = logging.getLogger(__name__)


def format_response(result: Any, is_error: bool = False) -> Dict[str, Any]:
    """
    Formats response in standard format.

    Args:
        result: Operation result
        is_error: Error flag

    Returns:
        Dict[str, Any]: Standardized response
    """
    if is_error:
        if isinstance(result, str):
            return {"status": "error", "error": result}
        return {"status": "error", "error": str(result)}

    # If result is already a dictionary, return it wrapped
    if isinstance(result, dict):
        return {"status": "success", "response": result}

    # If result has dict() method or __dict__, use it
    if hasattr(result, "dict") and callable(getattr(result, "dict")):
        return {"status": "success", "response": result.dict()}
    if hasattr(result, "__dict__"):
        return {"status": "success", "response": result.__dict__}
    if hasattr(result, "to_dict") and callable(getattr(result, "to_dict")):
        return {"status": "success", "response": result.to_dict()}

    # In other cases, convert to string
    return {"status": "success", "response": str(result)}


@dataclass
class AppContext:
    """Application context with typed resources."""

    lightrag_client: LightRAGClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manages application lifecycle with typed context.
    Initializes LightRAG API client at startup and closes it at shutdown.
    """
    lightrag_client = LightRAGClient(
        base_url=config.LIGHTRAG.base_url,
        api_key=config.LIGHTRAG.api_key,
    )

    try:
        yield AppContext(lightrag_client=lightrag_client)
    finally:
        await lightrag_client.close()
        logger.info("LightRAG MCP Server stopped")


mcp = FastMCP(
    "LightRAG MCP Server",
    lifespan=app_lifespan,
    host=config.MCP_HOST,
    port=config.MCP_PORT,
    streamable_http_path=config.MCP_STREAMABLE_HTTP_PATH,
    stateless_http=config.MCP_STATELESS_HTTP,
    json_response=config.MCP_JSON_RESPONSE,
)


async def execute_lightrag_operation(
    operation_name: str, operation_func: Callable, ctx: Context
) -> Dict[str, Any]:
    """
    Universal wrapper function for executing operations with LightRAG API.

    Automatically handles:
    - Getting client from context
    - Type casting
    - Exception handling
    - Response formatting

    Args:
        operation_name: Operation name for logging
        operation_func: Function to execute that takes client as first argument

    Returns:
        Dict[str, Any]: Formatted response
    """
    try:
        if not ctx or not ctx.request_context or not ctx.request_context.lifespan_context:
            return format_response(
                f"Error: Request context is not available for {operation_name}", is_error=True
            )

        app_ctx = cast(AppContext, ctx.request_context.lifespan_context)
        client = app_ctx.lightrag_client

        logger.info(f"Executing operation: {operation_name}")
        result = await operation_func(client)

        return format_response(result)
    except Exception as e:
        logger.exception(f"Error during {operation_name}: {str(e)}")
        return format_response(str(e), is_error=True)


# === MCP Tools ===


@mcp.tool(name="query_document", description="Execute a query to documents through LightRAG API")
async def query_document(
    ctx: Context,
    query: str = Field(description="Query text"),
    mode: str = Field(
        description="Search mode (mix, semantic, keyword, global, hybrid, local, naive)",
        default="mix",
    ),
    top_k: int = Field(description="Number of results", default=60),
    only_need_context: bool = Field(
        description="Return only context without LLM response", default=False
    ),
    only_need_prompt: bool = Field(
        description="If True, returns only generated prompt without creating a response",
        default=False,
    ),
    response_type: str = Field(
        description="Определяет формат ответа. Примеры: 'Multiple Paragraphs', 'Single Paragraph', 'Bullet Points'",
        default="Multiple Paragraphs",
    ),
    max_token_for_text_unit: int = Field(
        description="Maximum tokens for each text fragment", default=4096
    ),
    max_token_for_global_context: int = Field(
        description="Maximum tokens for global context", default=4096
    ),
    max_token_for_local_context: int = Field(
        description="Maximum tokens for local context", default=4096
    ),
    hl_keywords: list[str] = Field(
        description="List of high-level keywords for prioritization", default=[]
    ),
    ll_keywords: list[str] = Field(
        description="List of low-level keywords for search refinement", default=[]
    ),
    history_turns: int = Field(
        description="Number of conversation turns in response context", default=10
    ),
) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.query(
            query_text=query,
            mode=mode,
            top_k=top_k,
            only_need_context=only_need_context,
            only_need_prompt=only_need_prompt,
            response_type=response_type,
            max_token_for_text_unit=max_token_for_text_unit,
            max_token_for_global_context=max_token_for_global_context,
            max_token_for_local_context=max_token_for_local_context,
            hl_keywords=hl_keywords,
            ll_keywords=ll_keywords,
            history_turns=history_turns,
        )

    return await execute_lightrag_operation(
        operation_name=f"query execution: {query[:50]}...",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(name="insert_document", description="Add text directly to LightRAG storage")
async def insert_document(
    ctx: Context,
    text: Union[str, List[str]] = Field(description="Text or list of texts to add"),
) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.insert_text(text=text)

    return await execute_lightrag_operation(
        operation_name="text insertion",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(
    name="upload_document",
    description="Upload document from file to LightRAG's /inputs directory and start indexing",
)
async def upload_document(
    ctx: Context,
    file_path: str = Field(description="Path to file for upload"),
) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.upload_document(file_path=file_path)

    return await execute_lightrag_operation(
        operation_name=f"file upload: {file_path}",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(name="insert_file", description="Add document from file to LightRAG")
async def insert_file(
    ctx: Context,
    file_path: str = Field(description="Path to file for upload"),
) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.insert_file(file_path=file_path)

    return await execute_lightrag_operation(
        operation_name=f"file insertion: {file_path}",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(name="insert_batch", description="Add batch of documents from directory to LightRAG")
async def insert_batch(
    ctx: Context,
    directory_path: str = Field(description="Path to directory with files to add"),
    recursive: bool = Field(description="Recursive addition. Defaults to False", default=False),
    depth: int = Field(description="Recursion depth. Defaults to 1", default=1),
    include_only: list[str] = Field(
        description="""
        List of regexp to specify files to include. 
        Files not matching any regexp will be skipped. 
        Defaults to [] (all files). 
        Either include_only or ignore_files must be specified, not both.
        """,
        default=[],
    ),
    ignore_files: list[str] = Field(
        description="""
        List of regexp to exclude files from batch insertion.
        Defaults to [] (no files are excluded).
        Either ignore_files or include_only must be specified, not both.
        """,
        default=[],
    ),
    ignore_directories: list[str] = Field(
        description="""
        List of regexp to exclude directories from batch insertion.
        Defaults to [] (no directories are excluded).
        """,
        default=[],
    ),
) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.insert_batch(
            directory_path=directory_path,
            recursive=recursive,
            depth=depth,
            include_only=include_only,
            ignore_directories=ignore_directories,
            ignore_files=ignore_files,
        )

    return await execute_lightrag_operation(
        operation_name=f"batch insertion from directory: {directory_path}",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(
    name="scan_for_new_documents",
    description="Start scanning LightRAG /inputs directory for new documents",
)
async def scan_for_new_documents(ctx: Context) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.scan_for_new_documents()

    return await execute_lightrag_operation(
        operation_name="scanning for new documents",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(name="get_documents", description="Get list of all uploaded documents")
async def get_documents(ctx: Context) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.get_documents()

    return await execute_lightrag_operation(
        operation_name="getting documents list",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(name="get_pipeline_status", description="Get status of document processing in pipeline")
async def get_pipeline_status(ctx: Context) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.get_pipeline_status()

    return await execute_lightrag_operation(
        operation_name="getting pipeline status",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(
    name="get_graph_labels",
    description="Get labels (node and relationship types) from knowledge graph",
)
async def get_graph_labels(ctx: Context) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.get_graph_labels()

    return await execute_lightrag_operation(
        operation_name="getting graph labels",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(name="check_lightrag_health", description="Check LightRAG API status")
async def check_lightrag_health(ctx: Context) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        result = await client.get_health()
        if isinstance(result, dict) and "status" in result:
            logger.info(f"LightRAG API returned status: {result['status']}")
        return result

    return await execute_lightrag_operation(
        operation_name="health check",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(
    name="merge_entities",
    description="Merge multiple entities into one with relationship migration",
)
async def merge_entities(
    ctx: Context,
    source_entities: List[str] = Field(description="List of entity names to merge"),
    target_entity: str = Field(description="Target entity name"),
    merge_strategy: Dict[str, str] = Field(
        description="Property merge strategy. Supported strategies: 'concatenate' (concatenate text values), 'keep_first' (keep first non-empty value), 'keep_last' (keep last non-empty value), 'join_unique' (join unique values for delimited fields). Example: {'description': 'concatenate', 'entity_type': 'keep_first'}",
        default_factory=dict,
    ),
) -> Dict[str, Any]:
    async def _operation(client: LightRAGClient) -> Any:
        return await client.merge_entities(
            source_entities=source_entities,
            target_entity=target_entity,
            merge_strategy=merge_strategy,
        )

    return await execute_lightrag_operation(
        operation_name=f"entity merging: {', '.join(source_entities)} -> {target_entity}",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(name="create_entities", description="Create multiple entities in knowledge graph")
async def create_entities(
    ctx: Context,
    entities: List[Dict[str, Any]] = Field(
        description="""
        List of entity dictionaries, each containing:
        - entity_name (str): Name of the entity
        - entity_type (str): Type of the entity
        - description (str): Description of the entity
        - source_id (str): Source ID (document)
        
        Example:
        [
            {
                "entity_name": "Python",
                "entity_type": "PROGRAMMING_LANGUAGE",
                "description": "Python is a high-level programming language",
                "source_id": "doc123"
            },
            {
                "entity_name": "JavaScript",
                "entity_type": "PROGRAMMING_LANGUAGE",
                "description": "JavaScript is a scripting language",
                "source_id": "doc456"
            }
        ]
        """
    ),
) -> Dict[str, Any]:
    """
    Create multiple entities in the knowledge graph in parallel.

    Args:
        entities: List of entity dictionaries with required fields:
                entity_name,
                entity_type,
                description,
                source_id

    Returns:
        Dictionary with creation results for each entity
    """

    async def _create_entity(client: LightRAGClient, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        entity_name = entity_data.get("entity_name")
        entity_type = entity_data.get("entity_type")
        description = entity_data.get("description")
        source_id = entity_data.get("source_id")

        if not all([entity_name, entity_type, description, source_id]):
            return {
                "entity_name": str(entity_name or "unknown"),
                "status": "error",
                "error": "Missing required fields",
            }

        try:
            result = await client.create_entity(
                entity_name=str(entity_name),
                entity_type=str(entity_type),
                description=str(description),
                source_id=str(source_id),
            )
            return {"entity_name": str(entity_name), "status": "success", "result": result}
        except Exception as e:
            return {"entity_name": str(entity_name), "status": "error", "error": str(e)}

    async def _operation(client: LightRAGClient) -> Any:
        entity_names = [entity.get("entity_name", "unknown") for entity in entities]
        entity_names_str = ", ".join(entity_names[:5])
        if len(entity_names) > 5:
            entity_names_str += f" and {len(entity_names) - 5} more"

        # Create tasks for parallel execution
        tasks = [_create_entity(client, entity_data) for entity_data in entities]
        results = await asyncio.gather(*tasks)

        return {
            "total": len(entities),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "error"),
            "results": results,
        }

    return await execute_lightrag_operation(
        operation_name=f"bulk entity creation: {len(entities)} entities",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(
    name="delete_by_entities", description="Delete multiple entities from knowledge graph by name"
)
async def delete_by_entities(
    ctx: Context,
    entity_names: List[str] = Field(
        description="""
        List of entity names to delete.
        
        Example:
        ["Python", "JavaScript", "TypeScript"]
        """
    ),
) -> Dict[str, Any]:
    """
    Delete multiple entities from the knowledge graph in parallel.

    Args:
        entity_names: List of entity names to delete

    Returns:
        Dictionary with deletion results for each entity
    """

    async def _delete_entity(client: LightRAGClient, entity_name: str) -> Dict[str, Any]:
        try:
            result = await client.delete_by_entity(entity_name=entity_name)
            return {"entity_name": entity_name, "status": "success", "result": result}
        except Exception as e:
            return {"entity_name": entity_name, "status": "error", "error": str(e)}

    async def _operation(client: LightRAGClient) -> Any:
        entity_names_str = ", ".join(entity_names[:5])
        if len(entity_names) > 5:
            entity_names_str += f" and {len(entity_names) - 5} more"

        # Create tasks for parallel execution
        tasks = [_delete_entity(client, entity_name) for entity_name in entity_names]
        results = await asyncio.gather(*tasks)

        return {
            "total": len(entity_names),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "error"),
            "results": results,
        }

    return await execute_lightrag_operation(
        operation_name=f"bulk entity deletion: {len(entity_names)} entities",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(
    name="delete_by_doc_ids",
    description="Delete all entities and relationships associated with multiple documents",
)
async def delete_by_doc_ids(
    ctx: Context,
    doc_ids: List[str] = Field(
        description="""
        List of document IDs to delete entities from.
        
        Example:
        ["doc123", "doc456", "doc789"]
        """
    ),
) -> Dict[str, Any]:
    """
    Delete entities and relationships associated with multiple documents in parallel.

    Args:
        doc_ids: List of document IDs to delete entities from

    Returns:
        Dictionary with deletion results for each document ID
    """

    async def _delete_by_doc_id(client: LightRAGClient, doc_id: str) -> Dict[str, Any]:
        try:
            result = await client.delete_by_doc_id(doc_id=doc_id)
            return {"doc_id": doc_id, "status": "success", "result": result}
        except Exception as e:
            return {"doc_id": doc_id, "status": "error", "error": str(e)}

    async def _operation(client: LightRAGClient) -> Any:
        doc_ids_str = ", ".join(doc_ids[:5])
        if len(doc_ids) > 5:
            doc_ids_str += f" and {len(doc_ids) - 5} more"

        # Create tasks for parallel execution
        tasks = [_delete_by_doc_id(client, doc_id) for doc_id in doc_ids]
        results = await asyncio.gather(*tasks)

        return {
            "total": len(doc_ids),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "error"),
            "results": results,
        }

    return await execute_lightrag_operation(
        operation_name=f"bulk deletion by document IDs: {len(doc_ids)} documents",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(name="edit_entities", description="Edit multiple existing entities in knowledge graph")
async def edit_entities(
    ctx: Context,
    entities: List[Dict[str, Any]] = Field(
        description="""
        List of entity dictionaries to edit, each containing:
        - entity_name (str): Name of the entity to edit
        - entity_type (str): New entity type
        - description (str): New entity description
        - source_id (str): Source ID (document)
        
        Example:
        [
            {
                "entity_name": "Python",
                "entity_type": "PROGRAMMING_LANGUAGE",
                "description": "Updated description for Python",
                "source_id": "doc123"
            },
            {
                "entity_name": "JavaScript",
                "entity_type": "PROGRAMMING_LANGUAGE",
                "description": "Updated description for JavaScript",
                "source_id": "doc456"
            }
        ]
        """
    ),
) -> Dict[str, Any]:
    """
    Edit multiple entities in the knowledge graph in parallel.

    Args:
        entities: List of entity dictionaries with required fields:
                entity_name,
                entity_type,
                description,
                source_id

    Returns:
        Dictionary with edit results for each entity
    """

    async def _edit_entity(client: LightRAGClient, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        entity_name = entity_data.get("entity_name")
        entity_type = entity_data.get("entity_type")
        description = entity_data.get("description")
        source_id = entity_data.get("source_id")

        if not all([entity_name, entity_type, description, source_id]):
            return {
                "entity_name": str(entity_name or "unknown"),
                "status": "error",
                "error": "Missing required fields",
            }

        try:
            result = await client.edit_entity(
                entity_name=str(entity_name),
                entity_type=str(entity_type),
                description=str(description),
                source_id=str(source_id),
            )
            return {"entity_name": str(entity_name), "status": "success", "result": result}
        except Exception as e:
            return {"entity_name": str(entity_name), "status": "error", "error": str(e)}

    async def _operation(client: LightRAGClient) -> Any:
        entity_names = [entity.get("entity_name", "unknown") for entity in entities]
        entity_names_str = ", ".join(entity_names[:5])
        if len(entity_names) > 5:
            entity_names_str += f" and {len(entity_names) - 5} more"

        # Create tasks for parallel execution
        tasks = [_edit_entity(client, entity_data) for entity_data in entities]
        results = await asyncio.gather(*tasks)

        return {
            "total": len(entities),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "error"),
            "results": results,
        }

    return await execute_lightrag_operation(
        operation_name=f"bulk entity editing: {len(entities)} entities",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(
    name="create_relations",
    description="Create multiple relationships between entities in knowledge graph",
)
async def create_relations(
    ctx: Context,
    relations: List[Dict[str, Any]] = Field(
        description="""
        List of relation dictionaries to create, each containing:
        - source (str): Source entity name
        - target (str): Target entity name
        - description (str): Relationship description
        - keywords (str): Keywords for relationship
        - source_id (str, optional): Source ID (document)
        - weight (float, optional): Relationship weight
        
        Example:
        [
            {
                "source": "Python",
                "target": "Django",
                "description": "Python is used to build Django",
                "keywords": "framework, web development",
                "source_id": "doc123",
                "weight": 0.8
            },
            {
                "source": "JavaScript",
                "target": "React",
                "description": "JavaScript is used to build React",
                "keywords": "framework, frontend",
                "source_id": "doc456",
                "weight": 0.9
            }
        ]
        """
    ),
) -> Dict[str, Any]:
    """
    Create multiple relationships between entities in the knowledge graph in parallel.

    Args:
        relations: List of relation dictionaries with required fields:
                source, target, description, keywords
                and optional fields: source_id, weight

    Returns:
        Dictionary with creation results for each relationship
    """

    async def _create_relation(
        client: LightRAGClient, relation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        source = relation_data.get("source")
        target = relation_data.get("target")
        description = relation_data.get("description")
        keywords = relation_data.get("keywords")
        source_id = relation_data.get("source_id")
        weight = relation_data.get("weight")

        if not all([source, target, description, keywords]):
            return {
                "relation": f"{str(source or 'unknown')} -> {str(target or 'unknown')}",
                "status": "error",
                "error": "Missing required fields",
            }

        try:
            result = await client.create_relation(
                source=str(source),
                target=str(target),
                description=str(description),
                keywords=str(keywords),
                source_id=str(source_id) if source_id else None,
                weight=float(weight) if weight is not None else None,
            )
            return {"relation": f"{source} -> {target}", "status": "success", "result": result}
        except Exception as e:
            return {"relation": f"{source} -> {target}", "status": "error", "error": str(e)}

    async def _operation(client: LightRAGClient) -> Any:
        relation_strs = [
            f"{r.get('source', 'unknown')} -> {r.get('target', 'unknown')}" for r in relations
        ]
        relation_strs_sample = ", ".join(relation_strs[:5])
        if len(relation_strs) > 5:
            relation_strs_sample += f" and {len(relation_strs) - 5} more"

        # Create tasks for parallel execution
        tasks = [_create_relation(client, relation_data) for relation_data in relations]
        results = await asyncio.gather(*tasks)

        return {
            "total": len(relations),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "error"),
            "results": results,
        }

    return await execute_lightrag_operation(
        operation_name=f"bulk relationship creation: {len(relations)} relationships",
        operation_func=_operation,
        ctx=ctx,
    )


@mcp.tool(
    name="edit_relations",
    description="Edit multiple relationships between entities in knowledge graph",
)
async def edit_relations(
    ctx: Context,
    relations: List[Dict[str, Any]] = Field(
        description="""
        List of relation dictionaries to edit, each containing:
        - source (str): Source entity name
        - target (str): Target entity name
        - description (str): New relationship description
        - keywords (str): New keywords for relationship
        - relation_type (str): Relationship type
        - source_id (str, optional): Source ID (document)
        - weight (float, optional): New relationship weight
        
        Example:
        [
            {
                "source": "Python",
                "target": "Django",
                "description": "Updated description for Python-Django relation",
                "keywords": "framework, web development, updated",
                "relation_type": "USES",
                "source_id": "doc123",
                "weight": 0.85
            },
            {
                "source": "JavaScript",
                "target": "React",
                "description": "Updated description for JavaScript-React relation",
                "keywords": "framework, frontend, updated",
                "relation_type": "USES",
                "source_id": "doc456",
                "weight": 0.95
            }
        ]
        """
    ),
) -> Dict[str, Any]:
    """
    Edit multiple relationships between entities in the knowledge graph in parallel.

    Args:
        relations: List of relation dictionaries with required fields:
                source, target, description, keywords, relation_type
                and optional fields: source_id, weight

    Returns:
        Dictionary with edit results for each relationship
    """

    async def _edit_relation(
        client: LightRAGClient, relation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        source = relation_data.get("source")
        target = relation_data.get("target")
        description = relation_data.get("description")
        keywords = relation_data.get("keywords")
        relation_type = relation_data.get("relation_type")
        source_id = relation_data.get("source_id")
        weight = relation_data.get("weight")

        if not all([source, target, description, keywords, relation_type]):
            return {
                "relation": f"{str(source or 'unknown')} -> {str(target or 'unknown')}",
                "status": "error",
                "error": "Missing required fields",
            }

        try:
            result = await client.edit_relation(
                source=str(source),
                target=str(target),
                description=str(description),
                keywords=str(keywords),
                relation_type=str(relation_type),
                source_id=str(source_id) if source_id else None,
                weight=float(weight) if weight is not None else None,
            )
            return {"relation": f"{source} -> {target}", "status": "success", "result": result}
        except Exception as e:
            return {"relation": f"{source} -> {target}", "status": "error", "error": str(e)}

    async def _operation(client: LightRAGClient) -> Any:
        relation_strs = [
            f"{r.get('source', 'unknown')} -> {r.get('target', 'unknown')}" for r in relations
        ]
        relation_strs_sample = ", ".join(relation_strs[:5])
        if len(relation_strs) > 5:
            relation_strs_sample += f" and {len(relation_strs) - 5} more"

        # Create tasks for parallel execution
        tasks = [_edit_relation(client, relation_data) for relation_data in relations]
        results = await asyncio.gather(*tasks)

        return {
            "total": len(relations),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "error"),
            "results": results,
        }

    return await execute_lightrag_operation(
        operation_name=f"bulk relationship editing: {len(relations)} relationships",
        operation_func=_operation,
        ctx=ctx,
    )
