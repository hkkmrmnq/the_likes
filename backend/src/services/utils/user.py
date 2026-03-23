import hashlib
from datetime import datetime, timedelta, timezone
from random import randint
from uuid import UUID, uuid4

import httpx
import jwt
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from zxcvbn import zxcvbn

from src import containers as cnt
from src import crud, db, tasks
from src import exceptions as exc
from src.config import CFG, CNST
from src.logger import logger
from src.redis_client import redis_client

value_hash = PasswordHash.recommended()


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


def verify_value_with_hash(*, plain: str, hashed: str) -> bool:
    return value_hash.verify(plain, hashed)


def get_value_hash(password: str) -> str:
    return value_hash.hash(password)


def decode_access_token(token: str) -> UUID:
    """Returns user token subject (user id)."""
    decoded = jwt.decode(token, CFG.JWT_SECRET, algorithms=[CFG.JWT_ALGORITHM])
    raw_subject = decoded.get('sub')
    if not raw_subject:
        raise exc.BadRequest('sub not found in token.')
    try:
        subject = UUID(raw_subject)
    except Exception:
        raise exc.ServerError('invalid token sub format.')
    return subject


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
        error_msg = exc.get_error_msg(e)
        logger.error(error_msg)
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
    hashed_password = get_value_hash(password)
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


def create_refresh_token(
    *, user_id: UUID, now: datetime
) -> tuple[str, db.RefreshToken]:
    """Creates new refresh token, returns token and db.RefreshToken."""
    expires_at = now + timedelta(seconds=CFG.REFRESH_TOKEN_LIFETIME_SECONDS)
    jti = str(uuid4())
    payload = {
        'jti': jti,
        'sub': str(user_id),
        'type': 'refresh',
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(days=30)).timestamp()),
    }
    token = jwt.encode(payload, CFG.JWT_SECRET, algorithm=CFG.JWT_ALGORITHM)
    token_hash = get_value_hash(token)
    new_token = db.RefreshToken(
        user_id=user_id,
        jti=jti,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked_at=None,
    )
    return token, new_token


def decode_refresh_token(token: str) -> cnt.DecodedRefreshToken:
    decoded = jwt.decode(token, CFG.JWT_SECRET, algorithms=[CFG.JWT_ALGORITHM])
    subject = decoded.get('sub')
    if not subject:
        raise exc.ServerError('Incorrect decoded subject format.')
    raw_jti = decoded.get('jti')
    if not raw_jti:
        raise exc.ServerError('Incorrect decoded jti format.')
    jti = UUID(raw_jti)
    return cnt.DecodedRefreshToken(subject=subject, jti=jti)


async def get_current_valid_refresh_token_for_user(
    user_id: UUID, asession: AsyncSession
) -> db.RefreshToken | None:
    current_refresh_tokens = await crud.get_all_valid_refresh_tokens_for_user(
        user_id=user_id, asession=asession
    )
    if not current_refresh_tokens:
        return None
    if len(current_refresh_tokens) > 1:
        raise exc.ServerError(f'> 1 valid refresh token for {user_id=}')
    return current_refresh_tokens[0]


async def validate_db_refresh_token_for_user(
    *, user_id: UUID, jti: UUID, asession: AsyncSession
) -> db.RefreshToken:
    current_valid_refresh_token = (
        await get_current_valid_refresh_token_for_user(
            user_id=user_id, asession=asession
        )
    )
    if current_valid_refresh_token:
        return current_valid_refresh_token
    found = await crud.get_specific_refresh_token(jti=jti, asession=asession)
    if not found:
        raise exc.ServerError('Invalid refresh token.')  # TODO FAKE?
    if found.user_id != user_id:
        raise exc.ServerError('Invalid refresh token.')  # TODO STOLEN?
    if found.revoked_at:
        exc.Forbidden('Invalid refresh token.')  # TODO REUSE?
    found.revoked_at = datetime.now(timezone.utc)
    raise exc.Forbidden(
        'Refresh token expired. Please sign in with your email and password.'
    )
