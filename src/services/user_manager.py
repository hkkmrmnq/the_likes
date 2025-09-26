import hashlib
import uuid

import httpx
from fastapi import Request
from fastapi_users import (
    BaseUserManager,
    InvalidPasswordException,
    UUIDIDMixin,
)
from sqlalchemy.ext.asyncio import AsyncSession
from zxcvbn import zxcvbn

from .. import models as md
from .. import schemas as sch
from .. import services as srv
from ..config import CFG
from ..config import constants as CNST


async def send_email(email_to: str, subject: str, content: str) -> None:
    print(f'TO: {email_to}\nSUBJECT: {subject}\nCONTENT: {content}')


# async def send_email(email_to: str, subject: str, content: str) -> None:
#     message = EmailMessage()
#     message['From'] = CNF.EMAIL_APP_EMAIL
#     message['To'] = email_to
#     message['Subject'] = subject
#     message.set_content(content)

#     await aiosmtplib.send(
#         message,
#         hostname=SMTP_SERVER,
#         port=SMTP_PORT,
#         username=CNF.EMAIL_APP_EMAIL,
#         password=CNF.EMAIL_APP_PASSWORD,
#     )


async def is_password_pwned(password: str) -> bool | None:
    """
    Returns:
        True if password was pwned.
        False if not pwned.
        None if request failed (timeout, network, etc.).
    """
    try:
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f'https://api.pwnedpasswords.com/range/{prefix}'
            )
            response.raise_for_status()

        for line in response.text.splitlines():
            h, _ = line.split(':')
            if h == suffix:
                return True
        return False

    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError):
        return None


class UserManager(UUIDIDMixin, BaseUserManager[md.User, uuid.UUID]):
    reset_password_token_secret = CFG.RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = CFG.VERIFICATION_TOKEN_SECRET

    async def on_after_register(
        self, user: md.User, request: Request | None = None
    ) -> None:
        session: AsyncSession = self.user_db.session  # type: ignore
        await srv.create_profile(user, session)
        if user.is_superuser:
            return
        await self.request_verify(user, request)

    async def on_after_request_verify(
        self, user: md.User, token: str, request: Request | None = None
    ) -> None:
        """
        Perform logic after successful verification request.
        :param user: The user to verify.
        :param token: The verification token.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        """
        link = f'https://{CNST.APP_DOMAIN}/verify-email?token={token}'
        await send_email(
            user.email,
            'Welcome to APPNAME!',
            (
                'Someone registered with this email.\n'
                'If it was not you - ignore this message!\n'
                'If was you - click to verify your email:\n'
                f'{link}'
            ),
        )

    async def on_after_forgot_password(
        self, user: md.User, token: str, request: Request | None = None
    ) -> None:
        """
        Perform logic after successful forgot password request.
        :param user: The user that forgot its password.
        :param token: The forgot password token.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        """
        link = f'https://{CNST.APP_DOMAIN}/reset-password?token={token}'
        await send_email(
            user.email,
            'Password reset requested.',
            (
                'Someone requested password reset for account, '
                'that registered with this email.\n'
                'If it was not you - ignore this message!\n'
                'If you did request password reset - click the link:\n'
                f'{link}. '
            ),
        )

    async def on_after_reset_password(
        self, user: md.User, request: Request | None = None
    ) -> None:
        """
        Perform logic after successful password reset.
        :param user: The user that reset its password.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        """
        await send_email(
            user.email,
            'Password changed.',
            'Password for your APPNAME account have been changed.',
        )

    async def validate_password(
        self, password: str, user: sch.UserCreate
    ) -> None:
        result = zxcvbn(
            password,
            user_inputs=[user.email],
        )

        if result['score'] < CNST.PASSWORD_MIN_SCORE:
            raise InvalidPasswordException(
                f'Password too weak: {result["feedback"]["suggestions"]}'
            )
        is_pwned = await is_password_pwned(password)
        if is_pwned:
            raise InvalidPasswordException(
                (
                    "This password is not secure because it's been "
                    'leaked before. Please use a different one.'
                )
            )
