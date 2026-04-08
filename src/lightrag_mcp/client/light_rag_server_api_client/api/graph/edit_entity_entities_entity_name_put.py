from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entity_request import EntityRequest
from ...models.entity_response import EntityResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    entity_name: str,
    *,
    body: EntityRequest,
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
        "url": "/graph/entity/edit",
        "params": params,
    }

    # Modern LightRAG (>=1.4.x) replaced `PUT /entities/{name}` with
    # `POST /graph/entity/edit`. The new schema wraps the changeset:
    #   {"entity_name": "...", "updated_data": {...}, "allow_rename": ...}
    _updated_data = body.to_dict()
    _updated_data.pop("source_id", None)
    _body = {
        "entity_name": entity_name,
        "updated_data": _updated_data,
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
    entity_name: str,
    *,
    client: AuthenticatedClient,
    body: EntityRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Response[Union[EntityResponse, HTTPValidationError]]:
    r"""Edit Entity

     Updates entity information in the knowledge graph and re-embeds the entity in the vector database.

    Args:
        entity_name: Name of the entity to edit
        data: Dictionary containing updated attributes, e.g. {\"description\": \"new description\",
    \"entity_type\": \"new type\"}

    Returns:
        Dictionary containing updated entity information

    Args:
        entity_name (str):
        api_key_header_value (Union[None, Unset, str]):
        body (EntityRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntityResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        entity_name=entity_name,
        body=body,
        api_key_header_value=api_key_header_value,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    entity_name: str,
    *,
    client: AuthenticatedClient,
    body: EntityRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Optional[Union[EntityResponse, HTTPValidationError]]:
    r"""Edit Entity

     Updates entity information in the knowledge graph and re-embeds the entity in the vector database.

    Args:
        entity_name: Name of the entity to edit
        data: Dictionary containing updated attributes, e.g. {\"description\": \"new description\",
    \"entity_type\": \"new type\"}

    Returns:
        Dictionary containing updated entity information

    Args:
        entity_name (str):
        api_key_header_value (Union[None, Unset, str]):
        body (EntityRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntityResponse, HTTPValidationError]
    """

    return sync_detailed(
        entity_name=entity_name,
        client=client,
        body=body,
        api_key_header_value=api_key_header_value,
    ).parsed


async def asyncio_detailed(
    entity_name: str,
    *,
    client: AuthenticatedClient,
    body: EntityRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Response[Union[EntityResponse, HTTPValidationError]]:
    r"""Edit Entity

     Updates entity information in the knowledge graph and re-embeds the entity in the vector database.

    Args:
        entity_name: Name of the entity to edit
        data: Dictionary containing updated attributes, e.g. {\"description\": \"new description\",
    \"entity_type\": \"new type\"}

    Returns:
        Dictionary containing updated entity information

    Args:
        entity_name (str):
        api_key_header_value (Union[None, Unset, str]):
        body (EntityRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntityResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        entity_name=entity_name,
        body=body,
        api_key_header_value=api_key_header_value,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    entity_name: str,
    *,
    client: AuthenticatedClient,
    body: EntityRequest,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Optional[Union[EntityResponse, HTTPValidationError]]:
    r"""Edit Entity

     Updates entity information in the knowledge graph and re-embeds the entity in the vector database.

    Args:
        entity_name: Name of the entity to edit
        data: Dictionary containing updated attributes, e.g. {\"description\": \"new description\",
    \"entity_type\": \"new type\"}

    Returns:
        Dictionary containing updated entity information

    Args:
        entity_name (str):
        api_key_header_value (Union[None, Unset, str]):
        body (EntityRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntityResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            entity_name=entity_name,
            client=client,
            body=body,
            api_key_header_value=api_key_header_value,
        )
    ).parsed
