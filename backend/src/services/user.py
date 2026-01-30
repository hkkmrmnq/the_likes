from random import randint

from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, db, tasks
from src.config import CNST
from src.exceptions import exc
from src.redis_client import redis_client
from src.services import utils as utl


async def register_user(
    *, email: str, password: str, asession: AsyncSession
) -> tuple[str, str]:
    await utl.user.create_user(
        email=email, password=password, is_superuser=False, asession=asession
    )
    await asession.commit()
    created_user = await crud.read_user_by_email(
        email=email, asession=asession
    )
    if created_user is None:
        raise exc.ServerError('User not found in DB after creation.')
    srv_msg = run_email_verification(email)
    return created_user.email, srv_msg


async def create_superuser(
    *, email: str, password: str, asession: AsyncSession
) -> None:
    await utl.user.create_user(
        email=email,
        password=password,
        is_superuser=True,
        is_verified=True,
        asession=asession,
    )


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
    redis_client.expire(key, 15 * 60)
    tasks.send_email_confirmation_code.delay(email=email, code=code)
    return (
        f'Email confirmation code sent to {email}. '
        'Please enter the code to verify your email.'
    )


async def verify_email_with_code(
    *, email: str, code: int, asession: AsyncSession
) -> tuple[bool, str]:
    key = f'{CNST.CONFIRM_EMAIL_REDIS_KEY}{email}'
    data = redis_client.hgetall(key)
    if not data:
        return False, 'Invalid email or expired code.'
    attempts = int(data.get('attempts', 0))  # type: ignore
    if attempts >= 3:
        redis_client.delete(key)
        return False, 'To many attempts.'
    if int(data['code']) == code:  # type: ignore
        db_user = await crud.read_user_by_email(email=email, asession=asession)
        if db_user is None:
            raise exc.ServerError('User not found, unexpectedly.')
        db_user.is_verified = True
        await asession.commit()
        redis_client.delete(key)
        return (
            True,
            'Email verified. Use your email and password to sign in.',
        )
    redis_client.hincrby(key, 'attempts', 1)
    return False, 'Invalid code.'


async def process_verify_email_request(
    *, email: str, password: str, asession: AsyncSession
) -> tuple[bool, str]:
    user = await crud.read_user_by_email(email=email, asession=asession)
    if user is None:
        raise exc.NotFound('User not found.')
    if utl.verify_password(
        plain_password=password, hashed_password=user.password_hash
    ):
        srv_msg = run_email_verification(email=email)
        return True, srv_msg
    return False, 'Invalid password.'


async def authenticate_user(
    *, email: str, password: str, asession: AsyncSession
) -> tuple[str, str]:
    """Returns token and message or raises."""
    user = await get_user_by_email_or_raise(email=email, asession=asession)
    password_is_valid = utl.verify_password(
        plain_password=password, hashed_password=user.password_hash
    )
    if password_is_valid:
        access_token = utl.create_access_token(user.id)
        return access_token, 'Access token.'
    raise exc.NotAcceptable('Invalid password.')


async def get_user_by_email_or_raise(
    *, email: str, asession: AsyncSession
) -> db.User:
    user = await crud.read_user_by_email(email=email, asession=asession)
    if user is None:
        raise exc.NotFound('User not found.')
    return user


# TODO , reset_password, forgot_password
