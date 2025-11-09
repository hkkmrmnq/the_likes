import uuid

from fastapi import FastAPI
from fastapi_users import FastAPIUsers

from src import endpoints
from src.db.user_and_profile import User
from src.dependencies import auth_backend, get_user_manager
from src.exceptions import exceptions as exc
from src.exceptions import handlers
from src.middleware import LanguageMiddleware
from src.models.user_and_profile import (
    UserCreate,
    UserRead,
    UserUpdate,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])


app = FastAPI()

app.add_middleware(LanguageMiddleware)

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
app.include_router(endpoints.core_router, tags=['definitions'])
app.include_router(endpoints.profiles_router, tags=['profile'])
app.include_router(endpoints.values_router, tags=['values'])
app.include_router(endpoints.contacts_router, tags=['contacts'])
app.include_router(endpoints.messages_router, tags=['messages'])
app.include_router(endpoints.updates_router, tags=['updates'])

app.add_exception_handler(exc.InactiveUser, handlers.handle_inactive_user)
app.add_exception_handler(exc.UnverifiedUser, handlers.handle_unverified_user)
app.add_exception_handler(exc.NotFound, handlers.handle_not_found)
app.add_exception_handler(exc.AlreadyExists, handlers.handle_already_exists)
app.add_exception_handler(exc.BadRequest, handlers.handle_bad_request)
app.add_exception_handler(exc.ServerError, handlers.handle_server_error)
app.add_exception_handler(exc.Forbidden, handlers.handle_forbidden)
