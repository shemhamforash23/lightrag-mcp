from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.status_message_response import StatusMessageResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    entity_name: str,
    *,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_api_key_header_value: Union[None, Unset, str]
    if isinstance(api_key_header_value, Unset):
        json_api_key_header_value = UNSET
    else:
        json_api_key_header_value = api_key_header_value
    params["api_key_header_value"] = json_api_key_header_value

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    # Modern LightRAG (>=1.4.x) replaced `DELETE /entities/{name}` with
    # `DELETE /documents/delete_entity` whose body is `{"entity_name": ...}`.
    import json as _json
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/documents/delete_entity",
        "params": params,
        "headers": {"Content-Type": "application/json"},
        "content": _json.dumps({"entity_name": entity_name}).encode("utf-8"),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, StatusMessageResponse]]:
    if response.status_code == 200:
        response_200 = StatusMessageResponse.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, StatusMessageResponse]]:
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
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Response[Union[HTTPValidationError, StatusMessageResponse]]:
    """Delete Entity

     Delete a single entity and its relationships from the graph

    Args:
        entity_name: Name of the entity to delete

    Args:
        entity_name (str):
        api_key_header_value (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, StatusMessageResponse]]
    """

    kwargs = _get_kwargs(
        entity_name=entity_name,
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
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Optional[Union[HTTPValidationError, StatusMessageResponse]]:
    """Delete Entity

     Delete a single entity and its relationships from the graph

    Args:
        entity_name: Name of the entity to delete

    Args:
        entity_name (str):
        api_key_header_value (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, StatusMessageResponse]
    """

    return sync_detailed(
        entity_name=entity_name,
        client=client,
        api_key_header_value=api_key_header_value,
    ).parsed


async def asyncio_detailed(
    entity_name: str,
    *,
    client: AuthenticatedClient,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Response[Union[HTTPValidationError, StatusMessageResponse]]:
    """Delete Entity

     Delete a single entity and its relationships from the graph

    Args:
        entity_name: Name of the entity to delete

    Args:
        entity_name (str):
        api_key_header_value (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, StatusMessageResponse]]
    """

    kwargs = _get_kwargs(
        entity_name=entity_name,
        api_key_header_value=api_key_header_value,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    entity_name: str,
    *,
    client: AuthenticatedClient,
    api_key_header_value: Union[None, Unset, str] = UNSET,
) -> Optional[Union[HTTPValidationError, StatusMessageResponse]]:
    """Delete Entity

     Delete a single entity and its relationships from the graph

    Args:
        entity_name: Name of the entity to delete

    Args:
        entity_name (str):
        api_key_header_value (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, StatusMessageResponse]
    """

    return (
        await asyncio_detailed(
            entity_name=entity_name,
            client=client,
            api_key_header_value=api_key_header_value,
        )
    ).parsed
