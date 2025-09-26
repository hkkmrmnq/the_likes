from typing import Annotated, Any

from fastapi import Depends, Header
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.authentication.authenticator import Authenticator
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from .config import CFG
from .config import constants as CNST
from .db import session_factory
from .models import User
from .services.user_manager import UserManager


async def get_db():
    async with session_factory() as session:
        yield session


bearer_transport = BearerTransport(tokenUrl='auth/jwt/login')


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=CFG.JWT_SECRET,
        lifetime_seconds=CFG.JWT_ACCESS_LIFETIME,
    )


auth_backend = AuthenticationBackend(
    name='jwt', transport=bearer_transport, get_strategy=get_jwt_strategy
)


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


authenticatior = Authenticator(
    backends=[auth_backend], get_user_manager=get_user_manager
)

current_user = authenticatior.current_user()
current_active_verified_user = authenticatior.current_user(
    active=True, verified=True
)


def with_common_responses(
    codes: list[int],
    extra_responses: dict[int, dict[str, str]] = {},
) -> dict[int | str, dict[str, Any]] | None:
    """Dependency that adds common responses to endpoints."""
    needed_responces = {k: CNST.COMMON_RESPONSES[k] for k in codes}
    return {**needed_responces, **extra_responses}


def get_language(
    accept_language: Annotated[
        str | None, Header(alias='Accept-Language')
    ] = None,
) -> str:
    """Dependency to extract and validate language."""
    if not accept_language:
        return CNST.LANGUAGE_DEFAULT
    language = accept_language.split(',')[0][:2].lower()
    return (
        language
        if language in CNST.SUPPORTED_LANGUAGES
        else CNST.LANGUAGE_DEFAULT
    )
