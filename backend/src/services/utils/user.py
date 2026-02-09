import hashlib
from datetime import datetime, timedelta, timezone
from random import randint
from uuid import UUID

import httpx
import jwt
from jwt.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from zxcvbn import zxcvbn

from src import containers as cnt
from src import crud, db, tasks
from src.config import CFG, CNST, ENM
from src.exceptions import exceptions as exc
from src.logger import logger
from src.redis_client import redis_client

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


async def _is_password_pwned(*, password: str) -> bool | None:
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
    Validates password with pwnedpasswords API.
    Raises if password is weak or leaked.
    Skips if no responce from API.
    """
    result = zxcvbn(
        password,
        user_inputs=[email],
    )

    if result['score'] < CNST.PASSWORD_MIN_SCORE:
        raise exc.Forbidden(
            f'Password too weak: {result["feedback"]["suggestions"]}'
        )
    is_pwned = await _is_password_pwned(password=password)
    if is_pwned:
        raise exc.Forbidden(
            (
                "This password is not secure because it's been "
                'leaked before. Please use different password.'
            )
        )


async def get_user_by_email_or_raise(
    *, email: str, asession: AsyncSession
) -> db.User:
    user = await crud.read_user_by_email(email=email, asession=asession)
    if user is None:
        raise exc.NotFound('User not found.')
    return user


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


async def get_active_user_by_email(
    email: str, asession: AsyncSession
) -> db.User:
    """
    Raises if user not found or deactivated.
    Returns user (ignores is_verified).
    """
    user = await crud.read_user_by_email(email=email, asession=asession)
    if user is None:
        raise exc.NotFound(
            'Requested email not found. You can create an account.'
        )
    if not user.is_active:
        raise exc.Forbidden('Account deactivated.')
    return user


def run_email_verification(email: str) -> str:
    code = ''
    for _ in range(6):
        code += str(randint(1, 9))
    key = f'{CNST.CONFIRM_EMAIL_REDIS_KEY}{email}'
    data = {
        'code': code,
        'email': email,
        'attempts': 0,
    }
    redis_client.hset(key, mapping=data)
    redis_client.expire(
        key, timedelta(seconds=CFG.CONFIRMATION_CODE_LIFETIME_SECONDS)
    )
    tasks.send_email_confirmation_code.delay(email=email, code=code)
    return (
        f'Email confirmation code sent to {email}. '
        'Please enter the code to verify your email.'
    )


def check_verification_code(*, email: str, code: int) -> tuple[bool, str]:
    key = f'{CNST.CONFIRM_EMAIL_REDIS_KEY}{email}'
    data = redis_client.hgetall(key)
    if not data:
        return False, 'Invalid email or expired code.'
    attempts = int(data.get('attempts', 0))  # type: ignore
    if attempts >= 3:
        redis_client.delete(key)
        return False, 'To many attempts.'
    if int(data['code']) != code:  # type: ignore
        redis_client.hincrby(key, 'attempts', 1)
        return False, 'Invalid code.'
    return True, 'Valid code'


async def set_existing_user_to_verified(
    *, email: str, asession: AsyncSession
) -> None:
    """
    Raises if user not found.
    Sets is_verified to True (ignores previous value).
    """
    db_user = await crud.read_user_by_email(email=email, asession=asession)
    if db_user is None:
        raise exc.ServerError('User not found, unexpectedly.')
    db_user.is_verified = True
    await asession.commit()
