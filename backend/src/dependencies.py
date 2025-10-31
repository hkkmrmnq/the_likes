from typing import Any, AsyncGenerator

from fastapi import Depends
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.authentication.authenticator import Authenticator
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import CFG
from src.config import constants as CNST
from src.db import User
from src.services.user_manager import FixedSQLAlchemyUserDatabase, UserManager
from src.sessions import a_session_factory


async def get_async_session() -> AsyncGenerator:
    async with a_session_factory() as session:
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


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield FixedSQLAlchemyUserDatabase(session, User)


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
    *,
    common_response_codes: list[int] | None = None,
    extra_responses: dict[int, dict[str, str]] | None = None,
) -> dict[int | str, dict[str, Any]] | None:
    """Dependency that adds common responses to endpoints."""
    common_response_codes = common_response_codes or []
    extra_responses = extra_responses or {}
    needed_responces = {
        k: CNST.COMMON_RESPONSES[k] for k in common_response_codes
    }
    return {**needed_responces, **extra_responses}
