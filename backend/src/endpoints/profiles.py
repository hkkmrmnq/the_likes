from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src.db.user_and_profile import User
from src.models.core import ApiResponse
from src.models.user_and_profile import ProfileRead, ProfileUpdate
from src.services import profile as profile_srv

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
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[ProfileRead]:
    profile_model, message = await profile_srv.get_profile(
        my_user=my_user, asession=asession
    )
    return ApiResponse(data=profile_model, message=message)


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
    profile_model_update: ProfileUpdate,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[ProfileRead]:
    profile_model_read, message = await profile_srv.edit_profile(
        my_user=my_user, update_model=profile_model_update, asession=asession
    )
    return ApiResponse(data=profile_model_read, message=message)
