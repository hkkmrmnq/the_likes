from fastapi import APIRouter, Depends
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
            406: 'Invalid verification code.',
        },
    ),
)
async def verify_email(
    payload: sch.EmailVerificationCode,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[bool]:
    result, srv_msg = await srv.verify_email_with_code(
        email=payload.email, code=payload.code, asession=asession
    )
    return sch.ApiResponse(data=result, message=srv_msg)


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
            404: 'Requested user not found.',
            406: 'Invalid password.',
        },
    ),
)
async def login(
    creds: sch.UserCredentials,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.AccessToken]:
    access_token, srv_msg = await srv.authenticate_user(
        email=creds.email, password=creds.password, asession=asession
    )
    token_schema = sch.AccessToken(access_token=access_token)
    return sch.ApiResponse(data=token_schema, message=srv_msg)
