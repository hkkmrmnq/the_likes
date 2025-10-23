from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import dependencies as dp
from .. import models as md
from .. import services as srv
from ..db import User

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
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.PersonalValuesRead]:
    user_values, message = await srv.get_personal_values(
        user=my_user, a_session=a_session
    )
    return md.ApiResponse(data=user_values, message=message)


@router.post(
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
    pv_model: md.PersonalValuesCreateUpdate,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.PersonalValuesRead]:
    pv_read_model, message = await srv.create_personal_values(
        my_user=my_user, pv_model=pv_model, a_session=a_session
    )
    return md.ApiResponse(data=pv_read_model, message=message)


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
    pv_model: md.PersonalValuesCreateUpdate,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.PersonalValuesRead]:
    pv_read_model, message = await srv.update_personal_values(
        user=my_user, pv_model=pv_model, a_session=a_session
    )
    return md.ApiResponse(data=pv_read_model, message=message)
