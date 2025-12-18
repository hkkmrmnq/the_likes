from typing import Any

from fastapi import Depends
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.authentication.authenticator import Authenticator
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import CFG
from src.db.user_and_profile import User
from src.exceptions.descriptions import COMMON_RESPONSES, ErrorResponse
from src.services.user_manager import FixedSQLAlchemyUserDatabase, UserManager
from src.sessions import get_async_session

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


# 500: {
#     'model': ErrorResponse,
#     'content': {
#         'application/json': {
#             'example': {'detail': extra_responses[k]}
#         }
#     },
# }


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
            'model': ErrorResponse,
            'content': {
                'application/json': {
                    'example': {'detail': extra_responses_to_iclude[er_key]}
                }
            },
        }

    return {**common_responces, **extra_responses}
