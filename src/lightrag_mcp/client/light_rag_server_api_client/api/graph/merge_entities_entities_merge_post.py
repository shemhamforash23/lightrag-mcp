from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entity_response import EntityResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.merge_entities_request import MergeEntitiesRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: MergeEntitiesRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    json_api_key_header_value: Union[None, Unset, str]
    if isinstance(api_key_header_value, Unset):
        json_api_key_header_value = UNSET
    else:
        json_api_key_header_value = api_key_header_value
    params["api_key_header_value"] = json_api_key_header_value

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/graph/entities/merge",
        "params": params,
    }

    # Modern LightRAG (>=1.4.x) replaced `POST /merge` with
    # `POST /graph/entities/merge`. The new schema also renamed the
    # request fields:
    #   source_entities  -> entities_to_change
    #   target_entity    -> entity_to_change_into
    # `merge_strategy` is no longer accepted server-side and is dropped.
    _src = body.to_dict()
    _body = {
        "entities_to_change": _src.get("source_entities", []),
        "entity_to_change_into": _src.get("target_entity", ""),
    }

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[EntityResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = EntityResponse.from_dict(response.json())

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[EntityResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: MergeEntitiesRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Response[Union[EntityResponse, HTTPValidationError]]:
    r"""Merge Entities

     Merges multiple source entities into a target entity, handling all relationships,
    and updating both the knowledge graph and vector database.

    Args:
        source_entities: List of source entity names to merge
        target_entity: Name of the target entity after merging
        merge_strategy: Merge strategy configuration, e.g. {\"description\": \"concatenate\",
    \"entity_type\": \"keep_first\"}
            Supported strategies:
            - \"concatenate\": Concatenate all values (for text fields)
            - \"keep_first\": Keep the first non-empty value
            - \"keep_last\": Keep the last non-empty value
            - \"join_unique\": Join all unique values (for fields separated by delimiter)
    target_entity_data: Dictionary of specific values to set for the target entity,
            overriding any merged values, e.g. {\"description\": \"custom description\",
    \"entity_type\": \"PERSON\"}

    Returns:
        Dictionary containing the merged entity information

    Args:
        api_key_header_value (Union[None, Unset, str]):
        body (MergeEntitiesRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntityResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
        api_key_header_value=api_key_header_value,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: MergeEntitiesRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Optional[Union[EntityResponse, HTTPValidationError]]:
    r"""Merge Entities

     Merges multiple source entities into a target entity, handling all relationships,
    and updating both the knowledge graph and vector database.

    Args:
        source_entities: List of source entity names to merge
        target_entity: Name of the target entity after merging
        merge_strategy: Merge strategy configuration, e.g. {\"description\": \"concatenate\",
    \"entity_type\": \"keep_first\"}
            Supported strategies:
            - \"concatenate\": Concatenate all values (for text fields)
            - \"keep_first\": Keep the first non-empty value
            - \"keep_last\": Keep the last non-empty value
            - \"join_unique\": Join all unique values (for fields separated by delimiter)
    target_entity_data: Dictionary of specific values to set for the target entity,
            overriding any merged values, e.g. {\"description\": \"custom description\",
    \"entity_type\": \"PERSON\"}

    Returns:
        Dictionary containing the merged entity information

    Args:
        api_key_header_value (Union[None, Unset, str]):
        body (MergeEntitiesRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntityResponse, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        body=body,
        api_key_header_value=api_key_header_value,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: MergeEntitiesRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Response[Union[EntityResponse, HTTPValidationError]]:
    r"""Merge Entities

     Merges multiple source entities into a target entity, handling all relationships,
    and updating both the knowledge graph and vector database.

    Args:
        source_entities: List of source entity names to merge
        target_entity: Name of the target entity after merging
        merge_strategy: Merge strategy configuration, e.g. {\"description\": \"concatenate\",
    \"entity_type\": \"keep_first\"}
            Supported strategies:
            - \"concatenate\": Concatenate all values (for text fields)
            - \"keep_first\": Keep the first non-empty value
            - \"keep_last\": Keep the last non-empty value
            - \"join_unique\": Join all unique values (for fields separated by delimiter)
    target_entity_data: Dictionary of specific values to set for the target entity,
            overriding any merged values, e.g. {\"description\": \"custom description\",
    \"entity_type\": \"PERSON\"}

    Returns:
        Dictionary containing the merged entity information

    Args:
        api_key_header_value (Union[None, Unset, str]):
        body (MergeEntitiesRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntityResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
        api_key_header_value=api_key_header_value,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: MergeEntitiesRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Optional[Union[EntityResponse, HTTPValidationError]]:
    r"""Merge Entities

     Merges multiple source entities into a target entity, handling all relationships,
    and updating both the knowledge graph and vector database.

    Args:
        source_entities: List of source entity names to merge
        target_entity: Name of the target entity after merging
        merge_strategy: Merge strategy configuration, e.g. {\"description\": \"concatenate\",
    \"entity_type\": \"keep_first\"}
            Supported strategies:
            - \"concatenate\": Concatenate all values (for text fields)
            - \"keep_first\": Keep the first non-empty value
            - \"keep_last\": Keep the last non-empty value
            - \"join_unique\": Join all unique values (for fields separated by delimiter)
    target_entity_data: Dictionary of specific values to set for the target entity,
            overriding any merged values, e.g. {\"description\": \"custom description\",
    \"entity_type\": \"PERSON\"}

    Returns:
        Dictionary containing the merged entity information

    Args:
        api_key_header_value (Union[None, Unset, str]):
        body (MergeEntitiesRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntityResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            api_key_header_value=api_key_header_value,
        )
    ).parsed
