import uuid

from fastapi import FastAPI
from fastapi_users import FastAPIUsers

from . import exceptions as exc
from .dependencies import auth_backend, get_user_manager
from .endpoints import v1 as endpoints_v1
from .lifespan import lifespan
from .models import User
from .schemas.user_n_profile import UserCreate, UserRead, UserUpdate

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])


app = FastAPI(lifespan=lifespan)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix='/auth/jwt',
    tags=['auth'],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix='/auth',
    tags=['auth'],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead), prefix='/auth', tags=['auth']
)
app.include_router(
    fastapi_users.get_reset_password_router(), prefix='/auth', tags=['auth']
)
app.include_router(
    fastapi_users.get_users_router(
        UserRead, UserUpdate, requires_verification=True
    ),
    prefix='/users',
    tags=['users'],
)
app.include_router(endpoints_v1.profile_router, tags=['profile'])
app.include_router(endpoints_v1.values_router, tags=['values'])
app.include_router(endpoints_v1.contacts_router, tags=['contacts'])

app.add_exception_handler(exc.InactiveUser, exc.handle_inactive_user)
app.add_exception_handler(exc.UnverifiedUser, exc.handle_unverified_user)
app.add_exception_handler(exc.NotFound, exc.handle_not_found)
app.add_exception_handler(exc.AlreadyExists, exc.handle_already_exists)
app.add_exception_handler(
    exc.IncorrectBodyStructure, exc.handle_incorrect_body_structure
)
app.add_exception_handler(exc.ServerError, exc.handle_server_error)
