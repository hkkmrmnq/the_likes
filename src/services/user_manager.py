import uuid
from typing import Any

from fastapi import Request
from fastapi_users import (
    BaseUserManager,
    InvalidPasswordException,
    UUIDIDMixin,
)
from fastapi_users.models import UserProtocol
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from zxcvbn import zxcvbn

from .. import db
from ..config import CFG
from ..config import constants as CNST
from ..config.enums import SearchAllowedStatus
from ..models.profile_and_user import UserCreate
from ..tasks import (
    send_email_confirmation_token,
    send_password_reset_notification,
    send_password_reset_token,
)
from ._utils import is_password_pwned


class FixedSQLAlchemyUserDatabase(SQLAlchemyUserDatabase):
    """
    Makes it so that the User, Profile and UserDynamic
    are created at once.
    """

    async def create(self, create_dict: dict[str, Any]) -> UserProtocol:
        user = self.user_table(**create_dict)
        profile = db.Profile(user=user)
        user_dynamic = db.UserDynamic(
            user=user, search_allowed_status=SearchAllowedStatus.OK.value
        )
        self.session.add_all((user, profile, user_dynamic))
        await self.session.commit()
        await self.session.refresh(user)
        return user


class UserManager(UUIDIDMixin, BaseUserManager[db.User, uuid.UUID]):
    reset_password_token_secret = CFG.RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = CFG.VERIFICATION_TOKEN_SECRET

    async def on_after_register(
        self, user: db.User, request: Request | None = None
    ) -> None:
        if user.is_superuser:
            return
        await self.request_verify(user, request)

    async def on_after_request_verify(
        self, user: db.User, token: str, request: Request | None = None
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
        self, user: db.User, token: str, request: Request | None = None
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
        self, user: db.User, request: Request | None = None
    ) -> None:
        """
        Perform logic after successful password reset.
        :param user: The user that reset its password.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        """
        send_password_reset_notification.delay(email=user.email)

    async def validate_password(self, password: str, user: UserCreate) -> None:
        result = zxcvbn(
            password,
            user_inputs=[user.email],
        )

        if result['score'] < CNST.PASSWORD_MIN_SCORE:
            raise InvalidPasswordException(
                f'Password too weak: {result["feedback"]["suggestions"]}'
            )
        is_pwned = await is_password_pwned(password=password)
        if is_pwned:
            raise InvalidPasswordException(
                (
                    "This password is not secure because it's been "
                    'leaked before. Please use a different one.'
                )
            )
