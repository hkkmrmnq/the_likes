from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src import schemas as sch
from src import services as srv
from src.config import CFG

router = APIRouter()


@router.post(
    CFG.PATHS.PUBLIC.REGISTER,
    responses=dp.with_common_responses(
        common_response_codes=[400],
        extra_responses_to_iclude={
            409: 'User already exists.',
        },
    ),
)
async def register(
    creds: sch.UserCredentials,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[str]:
    email, srv_msg = await srv.register_user(
        email=creds.email, password=creds.password, asession=asession
    )
    return sch.ApiResponse(data=email, message=srv_msg)


@router.post(
    CFG.PATHS.PUBLIC.VERIFY_EMAIL,
    responses=dp.with_common_responses(
        common_response_codes=[400],
        extra_responses_to_iclude={
            401: 'Invalid/expired code or to many attempts.',
        },
    ),
)
async def verify_email(
    payload: sch.EmailVerificationData,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[None]:
    srv_msg = await srv.verify_email(
        email=payload.email, code=payload.code, asession=asession
    )
    return sch.ApiResponse(message=srv_msg)


@router.post(
    CFG.PATHS.PUBLIC.REQUEST_EMAIL_VERIFICATION,
    responses=dp.with_common_responses(
        common_response_codes=[400],
        extra_responses_to_iclude={
            404: 'User not found.',
        },
    ),
)
async def request_email_verification(
    creds: sch.UserCredentials,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[bool]:
    result, srv_msg = await srv.process_verify_email_request(
        email=creds.email, password=creds.password, asession=asession
    )
    return sch.ApiResponse(data=result, message=srv_msg)


@router.post(
    CFG.PATHS.PUBLIC.LOGIN,
    responses=dp.with_common_responses(
        common_response_codes=[400],
        extra_responses_to_iclude={
            401: 'Invalid password.',
            404: 'Requested user not found.',
        },
    ),
)
async def login(
    response: Response,
    creds: sch.UserCredentials,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.AccessToken]:
    access_token, refresh_token, srv_msg = await srv.authenticate_user(
        email=creds.email, password=creds.password, asession=asession
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        # secure=True,  # HTTPS only
        samesite='strict',
        max_age=CFG.REFRESH_TOKEN_LIFETIME_SECONDS,
    )
    token_schema = sch.AccessToken(access_token=access_token)
    return sch.ApiResponse(data=token_schema, message=srv_msg)


@router.post(
    CFG.PATHS.PUBLIC.REFRESH_ACCESS,
    responses=dp.with_common_responses(
        extra_responses_to_iclude={
            400: 'Refresh token cookie missing.',
            403: 'Expired / revoked refresh token.',
        },
    ),
    description="""
    Token rotation.
    Refresh token is read from the 'refresh_token' HttpOnly cookie.
    New refresh token will be set in the response cookie
    and new access token will be returned in response.
    """,
)
async def refresh_access(
    request: Request,
    response: Response,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.AccessToken]:
    refresh_token = request.cookies.get('refresh_token')
    access_token, refresh_token, srv_msg = await srv.refresh_access(
        token=refresh_token, asession=asession
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        # secure=True,  # HTTPS only
        samesite='strict',
        max_age=CFG.REFRESH_TOKEN_LIFETIME_SECONDS,
    )
    token_schema = sch.AccessToken(access_token=access_token)
    return sch.ApiResponse(data=token_schema, message=srv_msg)


@router.post(
    CFG.PATHS.PUBLIC.FORGOT_PASSWORD,
    responses=dp.with_common_responses(
        common_response_codes=[400],
        extra_responses_to_iclude={
            403: 'Account deactivated.',
            404: 'Requested email not found. You can create an account.',
        },
    ),
)
async def forgot_password(
    data: sch.EmailSchema,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[None]:
    message = await srv.run_forgot_password_steps(
        email=data.email, asession=asession
    )
    return sch.ApiResponse(message=message)


@router.post(
    CFG.PATHS.PUBLIC.SET_NEW_PASSWORD,
    responses=dp.with_common_responses(
        common_response_codes=[400],
        extra_responses_to_iclude={
            401: 'Invalid code.',
            403: 'Account deactivated.',
            404: 'Requested email not found. You can create an account.',
        },
    ),
)
async def set_new_password(
    payload: sch.ChangePasswordSchema,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[None]:
    msg = await srv.set_new_password(
        email=payload.email,
        new_password=payload.password,
        code=payload.code,
        asession=asession,
    )
    return sch.ApiResponse(message=msg)
