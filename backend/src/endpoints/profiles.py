from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src import models as md
from src import services as srv
from src.db import User

router = APIRouter()


@router.get(
    '/profile',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={500: {'description': 'Profile not found.'}},
    ),
)
async def get_profile(
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.ProfileRead]:
    profile_model, message = await srv.get_profile(
        my_user=my_user, a_session=a_session
    )
    return md.ApiResponse(data=profile_model, message=message)


@router.put(
    '/profile',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={
            400: {'description': "Can't set distance_limit without location."},
            500: {'description': 'Profile not found.'},
        },
    ),
)
async def edit_profile(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    profile_model_update: md.ProfileUpdate,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.ProfileRead]:
    profile_model_read, message = await srv.edit_profile(
        my_user=my_user, update_model=profile_model_update, a_session=a_session
    )
    return md.ApiResponse(data=profile_model_read, message=message)
