"""
Client for interacting with LightRAG API.
"""

import logging
import re
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, TypeVar, Union

from lightrag_mcp.client.light_rag_server_api_client.api.default import async_get_health
from lightrag_mcp.client.light_rag_server_api_client.api.documents import (
    async_get_documents,
    async_get_pipeline_status,
    async_insert_document,
    async_insert_file,
    async_insert_texts,
    async_scan_for_new_documents,
    async_upload_document,
)
from lightrag_mcp.client.light_rag_server_api_client.api.graph import (
    async_create_entity,
    async_create_relation,
    async_delete_by_doc_id,
    async_delete_entity,
    async_edit_entity,
    async_edit_relation,
    async_get_graph_labels,
    async_merge_entities,
)
from lightrag_mcp.client.light_rag_server_api_client.api.query import (
    async_query_document,
)
from lightrag_mcp.client.light_rag_server_api_client.client import AuthenticatedClient
from lightrag_mcp.client.light_rag_server_api_client.models import (
    BodyInsertFileDocumentsFilePost,
    BodyUploadToInputDirDocumentsUploadPost,
    DocsStatusesResponse,
    HTTPValidationError,
    InsertResponse,
    InsertTextRequest,
    InsertTextsRequest,
    PipelineStatusResponse,
    QueryRequest,
    QueryRequestMode,
    QueryResponse,
    relation_request,
    relation_response,
)
from lightrag_mcp.client.light_rag_server_api_client.models.entity_request import EntityRequest
from lightrag_mcp.client.light_rag_server_api_client.models.entity_response import EntityResponse
from lightrag_mcp.client.light_rag_server_api_client.models.merge_entities_request import (
    MergeEntitiesRequest,
)
from lightrag_mcp.client.light_rag_server_api_client.models.merge_entities_request_merge_strategy_type_0 import (
    MergeEntitiesRequestMergeStrategyType0,
)
from lightrag_mcp.client.light_rag_server_api_client.models.status_message_response import (
    StatusMessageResponse,
)
from lightrag_mcp.client.light_rag_server_api_client.types import File

from .client.light_rag_server_api_client.errors import UnexpectedStatus

logger = logging.getLogger(__name__)

T = TypeVar("T", covariant=True)
ApiFunc = Callable[..., Awaitable[Union[T, HTTPValidationError, None]]]


class LightRAGClient:
    """
    Client for interacting with LightRAG API.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
    ):
        """
        Initialize LightRAG API client.

        Args:
            base_url (str): Base API URL.
            api_key (str): API key (token).
        """
        self.base_url = base_url
        self.api_key = api_key
        # LightRAG server expects API key via "X-API-Key" header (not "Authorization: Bearer").
        # See: lightrag/api/utils_api.py:get_combined_auth_dependency uses APIKeyHeader(name="X-API-Key").
        self.client = AuthenticatedClient(
            base_url=base_url,
            token=api_key,
            verify_ssl=False,
            prefix="",
            auth_header_name="X-API-Key",
        )
        logger.info(f"Initialized LightRAG API client: {base_url}")

    async def _handle_exception(self, e: Exception, operation_name: str) -> None:
        """
        Handle exceptions when calling API.

        Args:
            e: Exception
            operation_name: Operation name for logging

        Raises:
            Exception: Re-raises the exception
        """
        if isinstance(e, UnexpectedStatus):
            logger.error(f"HTTP error during {operation_name}: {e.status_code} - {e.content!r}")
        else:
            logger.error(f"Error during {operation_name}: {str(e)}")

    async def _call_api(
        self,
        api_func: Callable[..., Awaitable[Union[T, HTTPValidationError, None]]],
        operation_name: str,
        **kwargs,
    ) -> Union[T, HTTPValidationError, None]:
        """
        Universal method for calling API functions.

        Args:
            api_func: API function to call
            operation_name: Operation name for logging
            **kwargs: Additional arguments for the API function

        Returns:
            Union[T, HTTPValidationError, None]: API call result
        """
        try:
            logger.debug(f"Calling API: {operation_name}")
            result = await api_func(**kwargs)
            logger.debug(f"API call successful: {operation_name}")
            return result
        except Exception as e:
            await self._handle_exception(e, operation_name)
            raise

    async def query(
        self,
        query_text: str,
        mode: str = "mix",
        top_k: int = 10,
        only_need_context: bool = False,
        only_need_prompt: bool = False,
        response_type: str = "Multiple Paragraphs",
        max_token_for_text_unit: int = 1000,
        max_token_for_global_context: int = 1000,
        max_token_for_local_context: int = 1000,
        hl_keywords: list[str] = [],
        ll_keywords: list[str] = [],
        history_turns: int = 10,
    ) -> Union[QueryResponse, HTTPValidationError, None]:
        """
        Execute a query to LightRAG API.

        Args:
            query_text (str): Query text
            mode (str, optional): Search mode (global, hybrid, local, mix, naive). Default is "mix".
            response_type (str, optional): Response format. Default is "Multiple Paragraphs".
            top_k (int, optional): Number of results. Default is 10.
            only_need_context (bool, optional): Return only context without LLM response. Default is False.
            only_need_prompt (bool, optional): Return only generated prompt without creating a response. Default is False.
            max_token_for_text_unit (int, optional): Maximum tokens for each text fragment. Default is 1000.
            max_token_for_global_context (int, optional): Maximum tokens for global context. Default is 1000.
            max_token_for_local_context (int, optional): Maximum tokens for local context. Default is 1000.
            hl_keywords (list[str], optional): List of high-level keywords for prioritization. Default is [].
            ll_keywords (list[str], optional): List of low-level keywords for search refinement. Default is [].
            history_turns (int, optional): Number of conversation turns in response context. Default is 10.

        Returns:
            Union[QueryResponse, HTTPValidationError, None]: Query result
        """
        logger.debug(f"Executing query: {query_text[:100]}...")

        request = QueryRequest(
            query=query_text,
            mode=QueryRequestMode(mode),
            response_type=response_type,
            top_k=top_k,
            only_need_context=only_need_context,
            only_need_prompt=only_need_prompt,
            max_token_for_text_unit=max_token_for_text_unit,
            max_token_for_global_context=max_token_for_global_context,
            max_token_for_local_context=max_token_for_local_context,
            hl_keywords=hl_keywords,
            ll_keywords=ll_keywords,
            history_turns=history_turns,
        )

        return await self._call_api(
            api_func=async_query_document,
            operation_name="query execution",
            client=self.client,
            body=request,
        )

    async def insert_text(
        self,
        text: Union[str, List[str]],
    ) -> Union[InsertResponse, HTTPValidationError, None]:
        """
        Add text to LightRAG.

        Args:
            text (Union[str, List[str]]): Text or list of texts to add

        Returns:
            Union[InsertResponse, HTTPValidationError]: Operation result
        """
        logger.debug(f"Adding text: {str(text)[:100]}...")

        request: InsertTextRequest | InsertTextsRequest
        if isinstance(text, str):
            request = InsertTextRequest(text=text)
            return await self._call_api(
                api_func=async_insert_document,
                operation_name="text insertion",
                client=self.client,
                body=request,
            )
        else:
            request = InsertTextsRequest(texts=text)
            return await self._call_api(
                api_func=async_insert_texts,
                operation_name="multiple texts insertion",
                client=self.client,
                body=request,
            )

    async def upload_document(self, file_path: str) -> Union[Any, HTTPValidationError, None]:
        """
        Upload document from file to LightRAG's /input directory and start indexing.

        Args:
            file_path (str): Path to file.

        Returns:
            Union[Any, HTTPValidationError]: Operation result.
        """
        logger.debug(f"Uploading document: {file_path}")

        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "rb") as f:
                file_name = path.name
                upload_request = BodyUploadToInputDirDocumentsUploadPost(
                    file=File(payload=f, file_name=file_name)
                )

                return await self._call_api(
                    api_func=async_upload_document,
                    operation_name=f"file upload {file_path}",
                    client=self.client,
                    body=upload_request,
                )
        except FileNotFoundError:
            logger.error(f"Файл не найден: {file_path}")
            raise
        except Exception as e:
            await self._handle_exception(e, f"загрузке файла {file_path}")
            raise

    async def insert_file(self, file_path: str) -> Union[InsertResponse, HTTPValidationError, None]:
        """
        Add document from a file_path directly to LightRAG storage, without uploading to /input directory.

        Args:
            file_path (str): Path to file.

        Returns:
            Union[InsertResponse, HTTPValidationError]: Operation result.
        """
        logger.debug(f"Adding file: {file_path}")

        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "rb") as f:
                file_name = path.name
                insert_file_request = BodyInsertFileDocumentsFilePost(
                    file=File(payload=f, file_name=file_name)
                )

                return await self._call_api(
                    api_func=async_insert_file,
                    operation_name=f"file insertion {file_path}",
                    client=self.client,
                    body=insert_file_request,
                )
        except FileNotFoundError:
            logger.error(f"Файл не найден: {file_path}")
            raise
        except Exception as e:
            await self._handle_exception(e, f"добавлении файла {file_path}")
            raise

    async def insert_batch(
        self,
        directory_path: str,
        recursive: bool = False,
        depth: int = 1,
        include_only: list[str] = [],
        ignore_directories: list[str] = [],
        ignore_files: list[str] = [],
    ) -> Union[InsertResponse, HTTPValidationError, None]:
        """
        Add batch of documents from directory.

        Args:
            directory_path (str): Path to directory.
            recursive (bool, optional): Recursive addition. Defaults to False.
            depth (int, optional): Recursion depth. Defaults to 1.
            ignore_directories (list[str], optional): List of regexp to exclude directories from batch insertion. Defaults to [].
            ignore_files (list[str], optional): List of regexp to exclude files from batch insertion. Defaults to []. Either ignore_files or include_only must be specified, not both.
            include_only (list[str], optional): List of regexp to specify files to include. Defaults to []. Either include_only or ignore_files must be specified, not both.

        Returns:
            Union[InsertResponse, HTTPValidationError]: Operation result.
        """
        logger.debug(
            f"Adding batch of documents from directory: {directory_path} (recursive={recursive}, depth={depth})"
        )

        if include_only and ignore_files:
            error_message = "Cannot specify both include_only and ignore_files parameters"
            logger.error(error_message)
            raise ValueError(error_message)

        dir_path = Path(directory_path)
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        include_patterns = [re.compile(pattern) for pattern in include_only] if include_only else []
        ignore_dir_patterns = (
            [re.compile(pattern) for pattern in ignore_directories] if ignore_directories else []
        )
        ignore_file_patterns = (
            [re.compile(pattern) for pattern in ignore_files] if ignore_files else []
        )

        def collect_file_paths(dir_path: Path, current_depth: int = 0) -> List[Path]:
            """Recursively collect file paths from directory"""
            file_paths = []
            try:
                for item in dir_path.iterdir():
                    if item.is_dir() and recursive and current_depth < depth:
                        # Check if directory should be ignored
                        dir_name = item.name
                        if any(pattern.search(dir_name) for pattern in ignore_dir_patterns):
                            logger.debug(f"Ignoring directory: {item} (matched ignore pattern)")
                            continue

                        # Process subdirectory
                        file_paths.extend(collect_file_paths(item, current_depth + 1))
                    elif item.is_file():
                        file_name = item.name

                        # Apply include_only filter if specified
                        if include_patterns:
                            if any(pattern.search(file_name) for pattern in include_patterns):
                                file_paths.append(item)
                                logger.debug(f"Including file: {item} (matched include pattern)")
                            else:
                                logger.debug(
                                    f"Skipping file: {item} (did not match any include pattern)"
                                )
                            continue

                        # Apply ignore_files filter if specified
                        if ignore_file_patterns:
                            if any(pattern.search(file_name) for pattern in ignore_file_patterns):
                                logger.debug(f"Ignoring file: {item} (matched ignore pattern)")
                                continue

                        # If we got here, the file is not filtered out
                        file_paths.append(item)
            except Exception as e:
                logger.error(f"Error collecting files from {dir_path}: {str(e)}")
            return file_paths

        try:
            file_paths = collect_file_paths(dir_path)
            logger.info(f"Found {len(file_paths)} files for processing after applying filters")

            success_count = 0
            failed_files = []

            for file_path in file_paths:
                try:
                    await self.insert_file(str(file_path))
                    success_count += 1
                    logger.debug(f"Successfully inserted file: {file_path}")
                except Exception as e:
                    logger.error(f"Error inserting file {file_path}: {str(e)}")
                    failed_files.append(str(file_path))

            if success_count == len(file_paths):
                status = "success"
                message = f"All {success_count} documents inserted successfully"
            elif success_count > 0:
                status = "partial_success"
                message = (
                    f"Successfully inserted {success_count} out of {len(file_paths)} documents"
                )
                if failed_files:
                    message += f". Failed files: {', '.join(failed_files)}"
            else:
                status = "failure"
                message = "No documents were successfully inserted"
                if failed_files:
                    message += f". Failed files: {', '.join(failed_files)}"

            return InsertResponse(status=status, message=message)
        except Exception as e:
            await self._handle_exception(e, f"inserting batch from {directory_path}")
            raise

    async def scan_for_new_documents(self) -> Union[Any, HTTPValidationError]:
        """
        Start scanning LightRAG's /input directory for new documents.

        Returns:
            Union[Any, HTTPValidationError]: Operation result.
        """
        logger.debug("Starting scan for new documents...")
        return await self._call_api(
            api_func=async_scan_for_new_documents,
            operation_name="scanning for new documents",
            client=self.client,
        )

    async def get_documents(
        self,
    ) -> Union[DocsStatusesResponse, HTTPValidationError, None]:
        """
        Get list of all documents in LightRAG.

        Returns:
            Union[DocsStatusesResponse, HTTPValidationError]: List of documents.
        """
        logger.debug("Getting list of documents...")
        return await self._call_api(
            api_func=async_get_documents,
            operation_name="getting documents list",
            client=self.client,
        )

    async def get_pipeline_status(
        self,
    ) -> Union[PipelineStatusResponse, HTTPValidationError, None]:
        """
        Get status of document processing in pipeline.

        Returns:
            Union[PipelineStatusResponse, HTTPValidationError]: Pipeline status.
        """
        logger.debug("Getting pipeline status...")
        return await self._call_api(
            api_func=async_get_pipeline_status,
            operation_name="getting pipeline status",
            client=self.client,
        )

    async def get_graph_labels(self) -> Union[Dict[str, List[str]], HTTPValidationError, None]:
        """
        Get graph labels from knowledge graph.

        Returns:
            Union[Dict[str, List[str]], HTTPValidationError]: Graph labels.
        """
        logger.debug("Getting graph labels...")
        return await self._call_api(
            api_func=async_get_graph_labels,
            operation_name="getting graph labels",
            client=self.client,
        )

    async def delete_by_entity(
        self, entity_name: str
    ) -> Union[StatusMessageResponse, HTTPValidationError, None]:
        """
        Delete entity from knowledge graph by name.

        Args:
            entity_name (str): Entity name

        Returns:
            Union[StatusMessageResponse, HTTPValidationError]: Operation result.
        """
        logger.debug(f"Deleting entity by name: {entity_name}")

        return await self._call_api(
            api_func=async_delete_entity,
            operation_name=f"deletion by entity name: {entity_name}",
            client=self.client,
            entity_name=entity_name,
        )

    async def delete_by_doc_id(
        self, doc_id: str
    ) -> Union[StatusMessageResponse, HTTPValidationError, None]:
        """
        Delete all entities and relationships associated with a document.

        Args:
            doc_id (str): Document ID

        Returns:
            Union[StatusMessageResponse, HTTPValidationError]: Operation result.
        """
        logger.debug(f"Deleting entities by document ID: {doc_id}")

        return await self._call_api(
            api_func=async_delete_by_doc_id,
            operation_name=f"deletion by document ID: {doc_id}",
            client=self.client,
            doc_id=doc_id,
        )

    async def create_entity(
        self, entity_name: str, entity_type: str, description: str, source_id: str
    ) -> Union[EntityResponse, HTTPValidationError, None]:
        """
        Create new entity in knowledge graph.

        Args:
            entity_name (str): Entity name.
            entity_type (str): Entity type.
            description (str): Entity description.
            source_id (str): Source ID (document).

        Returns:
            Union[EntityResponse, HTTPValidationError]: Created entity.
        """
        logger.debug(f"Creating entity: {entity_name} (type={entity_type})")

        request = EntityRequest(
            entity_type=entity_type,
            description=description,
            source_id=source_id,
        )

        return await self._call_api(
            api_func=async_create_entity,
            operation_name="entity creation",
            client=self.client,
            entity_name=entity_name,
            body=request,
        )

    async def edit_entity(
        self, entity_name: str, entity_type: str, description: str, source_id: str
    ) -> Union[EntityResponse, HTTPValidationError, None]:
        """
        Edit existing entity in knowledge graph.

        Args:
            entity_name (str): Entity name.
            entity_type (str): New entity type.
            description (str): New entity description.
            source_id (str): Source ID (document).

        Returns:
            Union[EntityResponse, HTTPValidationError]: Updated entity.
        """
        logger.debug(f"Editing entity: {entity_name}")

        request = EntityRequest(
            entity_type=entity_type,
            description=description,
            source_id=source_id,
        )

        return await self._call_api(
            api_func=async_edit_entity,
            operation_name="entity editing",
            client=self.client,
            entity_name=entity_name,
            body=request,
        )

    async def create_relation(
        self,
        source: str,
        target: str,
        description: str,
        keywords: str,
        source_id: str | None,
        weight: float | None,
    ) -> Union[relation_response.RelationResponse, HTTPValidationError, None]:
        """
        Create relationship between entities in knowledge graph.

        Args:
            source (str): Source entity name.
            target (str): Target entity name.
            description (str): Relationship description.
            keywords (str): Keywords for relationship.
            source_id (str | None): Source ID (document).
            weight (float | None): Relationship weight.

        Returns:
            Union[relation_response.RelationResponse, HTTPValidationError]: Created relationship.
        """
        logger.debug(f"Creating relationship: {source} -> {target}")

        request = relation_request.RelationRequest(
            description=description,
            keywords=keywords,
            source_id=source_id,
            weight=weight,
        )

        return await self._call_api(
            api_func=async_create_relation,
            operation_name="relationship creation",
            client=self.client,
            source=source,
            target=target,
            body=request,
        )

    async def edit_relation(
        self,
        source: str,
        target: str,
        description: str,
        keywords: str,
        source_id: str | None,
        weight: float | None,
        relation_type: str,
    ) -> Union[relation_response.RelationResponse, HTTPValidationError, None]:
        """
        Edit relationship between entities.

        Args:
            source (str): Source entity name.
            target (str): Target entity name.
            properties (Dict[str, Any]): New relationship properties.

        Returns:
            Union[Dict, HTTPValidationError]: Updated relationship.
        """
        logger.debug(f"Editing relationship: {source} -> {target}")

        request = relation_request.RelationRequest(
            description=description,
            keywords=keywords,
            source_id=source_id,
            weight=weight,
        )

        return await self._call_api(
            api_func=async_edit_relation,
            operation_name="relationship editing",
            client=self.client,
            source=source,
            target=target,
            body=request,
            relation_type=relation_type,
        )

    async def merge_entities(
        self,
        source_entities: List[str],
        target_entity: str,
        merge_strategy: Dict[str, str],
    ) -> Union[EntityResponse, HTTPValidationError, None]:
        """
        Merge multiple entities into one with relationship migration.

        Args:
            source_entities (List[str]): List of entity names to merge.
            target_entity (str): Target entity name.
            merge_strategy (Dict[str, str], optional): Property merge strategy.
                Possible values for strategies: 'max', 'min', 'concat', 'first', 'last'
                Example: {"description": "concat", "weight": "max"}

        Returns:
            Union[Dict, HTTPValidationError]: Merge operation result.
        """
        logger.debug(f"Merging entities: {', '.join(source_entities)} -> {target_entity}")

        request = MergeEntitiesRequest(
            source_entities=source_entities,
            target_entity=target_entity,
            merge_strategy=MergeEntitiesRequestMergeStrategyType0.from_dict(merge_strategy),
        )

        return await self._call_api(
            api_func=async_merge_entities,
            operation_name="entity merging",
            client=self.client,
            body=request,
        )

    async def get_health(self) -> Union[Any, HTTPValidationError]:
        """
        Check health status of LightRAG service.

        Returns:
            Union[Any, HTTPValidationError]: Health status.
        """
        logger.debug("Checking service health status...")
        return await self._call_api(
            api_func=async_get_health,
            operation_name="health check",
            client=self.client,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.get_async_httpx_client().aclose()
        logger.info("LightRAG API client closed.")
