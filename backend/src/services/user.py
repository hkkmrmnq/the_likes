from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.exceptions import exc
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
    if utl.verify_password(
        plain_password=password, hashed_password=user.password_hash
    ):
        srv_msg = utl.run_email_verification(email=email)
        return True, srv_msg
    return False, 'Invalid password.'


async def authenticate_user(
    *, email: str, password: str, asession: AsyncSession
) -> tuple[str, str]:
    """Returns token and message or raises."""
    user = await utl.get_user_by_email_or_raise(email=email, asession=asession)
    password_is_valid = utl.verify_password(
        plain_password=password, hashed_password=user.password_hash
    )
    if password_is_valid:
        access_token = utl.create_access_token(user.id)
        return access_token, 'Access token.'
    raise exc.Forbidden('Invalid password.')


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
    user.password_hash = utl.get_password_hash(password=new_password)
    await asession.commit()
    return msg
