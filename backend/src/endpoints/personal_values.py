from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src.db.user_and_profile import User
from src.models.core import ApiResponse
from src.models.personal_values import (
    PersonalValuesCreateUpdate,
    PersonalValuesRead,
)
from src.services import personal_values as personal_values_srv

router = APIRouter()


@router.get(
    '/my-values',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={
            404: {'description': 'Personal values have not yet been set.'}
        },
    ),
)
async def get_my_values(
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[PersonalValuesRead]:
    user_values, message = await personal_values_srv.get_personal_values(
        user=my_user, asession=asession
    )
    return ApiResponse(data=user_values, message=message)


@router.post(
    '/my-values',
    status_code=status.HTTP_201_CREATED,
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={
            400: {
                'description': (
                    'Inconsistent polarity/user_order. / '
                    'Incorrect attitude_id. / '
                    'Missing/extra values/aspects.'
                )
            },
            409: {'description': 'Personal values are already set.'},
            500: {
                'description': (
                    'Profile not found. / '
                    'Personal values not found after creation.'
                )
            },
        },
    ),
)
async def post_my_values(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    pv_model: PersonalValuesCreateUpdate,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[PersonalValuesRead]:
    pv_read_model, message = await personal_values_srv.create_personal_values(
        my_user=my_user, pv_model=pv_model, asession=asession
    )
    return ApiResponse(data=pv_read_model, message=message)


@router.put(
    '/my-values',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={
            400: {
                'description': (
                    'Inconsistent polarity/user_order. / '
                    'Incorrect attitude_id. / '
                    'Missing/extra values/aspects.'
                )
            },
            404: {'description': 'Personal values have not yet been set.'},
            500: {
                'description': (
                    'Profile not found. / '
                    'Personal values not found after update.'
                )
            },
        },
    ),
)
async def edit_my_values(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    pv_model: PersonalValuesCreateUpdate,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[PersonalValuesRead]:
    pv_read_model, message = await personal_values_srv.update_personal_values(
        my_user=my_user, pv_model=pv_model, asession=asession
    )
    return ApiResponse(data=pv_read_model, message=message)
