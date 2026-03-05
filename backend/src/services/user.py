from datetime import datetime, timezone

from jwt.exceptions import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src import exceptions as exc
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
    srv_msg = utl.run_email_verification(email)
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


async def verify_email(
    *, email: str, code: int, asession: AsyncSession
) -> str:
    success, msg = utl.check_verification_code(email=email, code=code)
    if not success:
        raise exc.Unauthorized(msg)
    await utl.set_existing_user_to_verified(email=email, asession=asession)
    return 'Email verified. Use your email and password to sign in.'


async def process_verify_email_request(
    *, email: str, password: str, asession: AsyncSession
) -> tuple[bool, str]:
    user = await crud.read_user_by_email(email=email, asession=asession)
    if user is None:
        raise exc.NotFound('User not found.')
    if utl.verify_value_with_hash(plain=password, hashed=user.password_hash):
        srv_msg = utl.run_email_verification(email=email)
        return True, srv_msg
    return False, 'Invalid password.'


async def authenticate_user(
    *, email: str, password: str, asession: AsyncSession
) -> tuple[str, str, str]:
    """
    Invalidates this user's valid refresh token.
    Creates new access token, new refresh token.
    Returns access token, refresh token and message.
    Raises if password is invalid.
    """
    user = await utl.get_user_by_email_or_raise(email=email, asession=asession)
    password_is_valid = utl.verify_value_with_hash(
        plain=password, hashed=user.password_hash
    )
    if not password_is_valid:
        raise exc.Forbidden('Invalid password.')

    access_token = utl.create_access_token(user.id)
    now = datetime.now(timezone.utc)
    current_valid_refresh_token = (
        await utl.get_current_valid_refresh_token_for_user(
            user_id=user.id, asession=asession
        )
    )
    if current_valid_refresh_token:
        current_valid_refresh_token.revoked_at = now
    refresh_token, refresh_token_model = utl.create_refresh_token(
        user_id=user.id, now=now
    )
    asession.add(refresh_token_model)
    await asession.commit()
    return access_token, refresh_token, 'Access token.'


async def refresh_access(
    *, token: str | None, asession: AsyncSession
) -> tuple[str, str, str]:
    """Returns new access token, new refresh token and message."""
    if not token:
        raise exc.BadRequest('Refresh token cookie missing.')
    try:
        result = utl.decode_refresh_token(token)
    except ExpiredSignatureError:
        raise exc.Forbidden(
            'Refresh token expired. '
            'Please sign in with your email and password.'
        )
    except Exception:
        raise exc.Forbidden('Invalid refresh token.')  # TODO

    current_refresh_token = await utl.validate_db_refresh_token_for_user(
        user_id=result.subject, jti=result.jti, asession=asession
    )
    now = datetime.now(timezone.utc)
    current_refresh_token.revoked_at = now
    refresh_token, db_refresh_token = utl.create_refresh_token(
        user_id=current_refresh_token.user_id, now=now
    )
    asession.add(db_refresh_token)
    await asession.commit()
    access_token = utl.create_access_token(current_refresh_token.user_id)
    return access_token, refresh_token, 'Access token.'


async def run_forgot_password_steps(email: str, asession: AsyncSession) -> str:
    await utl.get_active_user_by_email(email=email, asession=asession)
    srv_msg = utl.run_email_verification(email)
    return srv_msg


async def set_new_password(
    email: str, new_password: str, code: int, asession: AsyncSession
) -> str:
    user = await utl.get_active_user_by_email(email=email, asession=asession)
    await utl.validate_password(password=new_password, email=email)
    msg = await verify_email(email=email, code=code, asession=asession)
    user.password_hash = utl.get_value_hash(password=new_password)
    await asession.commit()
    return msg
