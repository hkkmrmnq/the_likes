from typing import Annotated, Any, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Query, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, db
from src import services as srv
from src.config import ENM
from src.logger import logger
from src.schemas.descriptions import (
    COMMON_RESPONSES,
    ErrorResponseSchema,
)
from src.sessions import asession_factory, sync_session_factory


def get_sync_session():
    with sync_session_factory() as session:
        yield session


async def get_async_session() -> AsyncGenerator:
    async with asession_factory() as session:
        yield session


def with_common_responses(
    *,
    common_response_codes: list[int] | None = None,
    extra_responses_to_iclude: dict[int, str] | None = None,
) -> dict[int | str, dict[str, Any]] | None:
    """Dependency that adds common responses to endpoints."""
    common_response_codes = common_response_codes or []
    common_responces = {k: COMMON_RESPONSES[k] for k in common_response_codes}
    extra_responses_to_iclude = extra_responses_to_iclude or {}
    extra_responses = {}
    for er_key in extra_responses_to_iclude:
        extra_responses[er_key] = {
            'model': ErrorResponseSchema,
            'content': {
                'application/json': {
                    'example': {'detail': extra_responses_to_iclude[er_key]}
                }
            },
        }

    return {**common_responces, **extra_responses}


security = HTTPBearer()


async def get_current_user_with_asession(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    asession: AsyncSession = Depends(get_async_session),
) -> tuple[db.User, AsyncSession]:
    token = credentials.credentials
    result = srv.validate_token(token)
    if result.detail == ENM.AuthResultDetail.ERROR:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token.',
        )
    elif result.detail == ENM.AuthResultDetail.EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Expired token.',
        )
    user = await crud.read_user_by_id(
        user_id=UUID(result.subject), asession=asession
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found',
        )
    return user, asession


async def get_current_active_and_virified_user_with_asession(
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        get_current_user_with_asession
    ),
) -> tuple[db.User, AsyncSession]:
    user, asession = user_and_asession
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User deactivated.',
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Email is not verified. Try request email verification.',
        )
    return user, asession


async def get_current_active_and_virified_websocket_user(
    token: Annotated[str | None, Query()] = None,
) -> db.User:
    if token is None:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason='Access token not provided.',
        )
    result = srv.validate_token(token)
    if result.detail == ENM.AuthResultDetail.ERROR:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason='Invalid authentication credentials.',
        )
    if result == ENM.AuthResultDetail.EXPIRED:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason='Expired token.'
        )
    async with asession_factory() as asession:
        user = await crud.read_user_by_id(
            user_id=UUID(result.subject), asession=asession
        )
    if user is None:
        logger.error(f'User ({result.subject=}) not found.')
        raise WebSocketException(
            code=status.WS_1011_INTERNAL_ERROR, reason='User not found.'
        )
    if not user.is_active:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason='Inactive user.'
        )
    if not user.is_verified:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason='Email is not verified.',
        )
    return user
