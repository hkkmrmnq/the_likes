from typing import Any
from uuid import UUID

from fastapi import Request
from fastapi_users import (
    BaseUserManager,
    InvalidPasswordException,
    UUIDIDMixin,
)
from fastapi_users.models import UserProtocol
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from zxcvbn import zxcvbn

from src import schemas as sch
from src.config import constants as CNST
from src.config.config import CFG
from src.config.enums import SearchAllowedStatus
from src.db.user_and_profile import Profile, User, UserDynamic
from src.services._utils import is_password_pwned
from src.tasks import (
    send_email_confirmation_token,
    send_password_reset_notification,
    send_password_reset_token,
)


class FixedSQLAlchemyUserDatabase(SQLAlchemyUserDatabase):
    """
    Replaces fastapi_users manager create method
    in order to make it create Profile and UserDynamic at once with User.
    """

    async def create(self, create_dict: dict[str, Any]) -> UserProtocol:
        user = self.user_table(**create_dict)
        profile = Profile(user=user)
        user_dynamic = UserDynamic(
            user=user, search_allowed_status=SearchAllowedStatus.OK.value
        )
        self.session.add_all((user, profile, user_dynamic))
        await self.session.commit()
        await self.session.refresh(user)
        return user


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """
    Fastapi_users manager.
    Responsible for users creation, authorization and authentication.
    """

    reset_password_token_secret = CFG.RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = CFG.VERIFICATION_TOKEN_SECRET

    async def on_after_register(
        self, user: User, request: Request | None = None
    ) -> None:
        """
        Triggered bu Fastapi Users every time a user is created.
        Probably should've been called 'on_after_creation'.
        Triggers request_verify if user is not a superuser.
        """
        if user.is_superuser or user.is_verified:
            return
        await self.request_verify(user, request)

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        """
        Perform logic after successful verification request.
        :param user: The user to verify.
        :param token: The verification token.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        """
        send_email_confirmation_token.delay(email=user.email, token=token)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        """
        Perform logic after successful forgot password request.
        :param user: The user that forgot its password.
        :param token: The forgot password token.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        """
        send_password_reset_token.delay(email=user.email, token=token)

    async def on_after_reset_password(
        self, user: User, request: Request | None = None
    ) -> None:
        """
        Perform logic after successful password reset.
        :param user: The user that reset its password.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        """
        send_password_reset_notification.delay(email=user.email)

    async def validate_password(
        self,
        password: str,
        user: sch.UserCreate,
        password_checker=is_password_pwned,
    ) -> None:
        """
        Validates password with pwnedpasswords API. Waek passwords rejected.
        Skips if no responce from API.
        """
        result = zxcvbn(
            password,
            user_inputs=[user.email],
        )

        if result['score'] < CNST.PASSWORD_MIN_SCORE:
            raise InvalidPasswordException(
                f'Password too weak: {result["feedback"]["suggestions"]}'
            )
        is_pwned = await password_checker(password=password)
        if is_pwned:
            raise InvalidPasswordException(
                (
                    "This password is not secure because it's been "
                    'leaked before. Please use a different one.'
                )
            )


async def _create_user(
    *,
    email: str,
    password: str,
    is_superuser: bool = False,
    is_active: bool = True,
    is_verified: bool = True,
    asession: AsyncSession,
) -> User:
    user_manager = UserManager(FixedSQLAlchemyUserDatabase(asession, User))
    user_data = sch.UserCreate(
        email=email,
        password=password,
        is_superuser=is_superuser,
        is_active=is_active,
        is_verified=is_verified,
    )
    user = await user_manager.create(user_create=user_data, safe=False)
    return user
