import uuid

from fastapi import FastAPI
from fastapi_users import FastAPIUsers

from src import endpoints
from src import exceptions as exc
from src.db import User
from src.dependencies import auth_backend, get_user_manager
from src.lifespan import lifespan
from src.middleware import LanguageMiddleware
from src.models.profile_and_user import UserCreate, UserRead, UserUpdate

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])


app = FastAPI(lifespan=lifespan)

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

app.add_exception_handler(exc.InactiveUser, exc.handle_inactive_user)
app.add_exception_handler(exc.UnverifiedUser, exc.handle_unverified_user)
app.add_exception_handler(exc.NotFound, exc.handle_not_found)
app.add_exception_handler(exc.AlreadyExists, exc.handle_already_exists)
app.add_exception_handler(exc.BadRequest, exc.handle_bad_request)
app.add_exception_handler(exc.ServerError, exc.handle_server_error)
app.add_exception_handler(exc.Forbidden, exc.handle_forbidden)
