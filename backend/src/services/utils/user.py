import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
import jwt
from jwt.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from zxcvbn import zxcvbn

from src import containers as cnt
from src import crud
from src.config import CFG, CNST, ENM
from src.exceptions import exceptions as exc
from src.logger import logger

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def create_access_token(
    user_id: UUID, expires_delta: timedelta | None = None
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=CFG.JWT_ACCESS_LIFETIME_MINUTES)
    to_encode = {'sub': str(user_id), 'exp': expire}
    return jwt.encode(to_encode, CFG.JWT_SECRET, algorithm=CFG.JWT_ALGORITHM)


def verify_password(*, plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_token(token: str) -> cnt.AuthResult:
    try:
        decoded = jwt.decode(
            token, CFG.JWT_SECRET, algorithms=[CFG.JWT_ALGORITHM]
        )
        subject = decoded.get('sub')
        if not subject:
            raise exc.ServerError('Incorrect decoded subject format.')
        return cnt.AuthResult(subject=subject, detail=ENM.AuthResultDetail.OK)
    except ExpiredSignatureError:
        return cnt.AuthResult(
            subject='error', detail=ENM.AuthResultDetail.EXPIRED
        )
    except Exception:
        return cnt.AuthResult(
            subject='error', detail=ENM.AuthResultDetail.ERROR
        )


async def is_password_pwned(*, password: str) -> bool | None:
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

    except (
        httpx.RequestError,
        httpx.TimeoutException,
        httpx.HTTPStatusError,
    ) as e:
        logger.error(e)
        return None


async def validate_password(
    *,
    password: str,
    email: str,
) -> None:
    """
    Validates password with pwnedpasswords API. Waek passwords rejected.
    Skips if no responce from API.
    """
    result = zxcvbn(
        password,
        user_inputs=[email],
    )

    if result['score'] < CNST.PASSWORD_MIN_SCORE:
        raise exc.NotAcceptable(
            f'Password too weak: {result["feedback"]["suggestions"]}'
        )
    is_pwned = await is_password_pwned(password=password)
    if is_pwned:
        raise exc.NotAcceptable(
            (
                "This password is not secure because it's been "
                'leaked before. Please use different password.'
            )
        )


async def create_user(
    *,
    email: str,
    password: str,
    is_superuser: bool = False,
    is_verified: bool = False,
    asession: AsyncSession,
) -> None:
    existing_user = await crud.read_user_by_email(
        email=email, asession=asession
    )
    if existing_user is not None:
        raise exc.AlreadyExists('User already exists.')
    await validate_password(password=password, email=email)
    hashed_password = get_password_hash(password)
    crud.create_user(
        email=email,
        hashed_password=hashed_password,
        is_superuser=is_superuser,
        is_verified=is_verified,
        asession=asession,
    )
    await asession.commit()
