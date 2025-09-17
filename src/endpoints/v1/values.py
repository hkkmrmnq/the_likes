from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ... import dependencies as dp
from ... import schemas as sch
from ... import services as srv
from ...models import User

router = APIRouter()


@router.get(
    '/definitions',
    response_model=list[sch.ValueTitleRead],
    responses=dp.with_common_responses(
        [401, 403], {500: {'description': 'Definitions not found.'}}
    ),
)
async def get_definitions(
    *,
    user: User = Depends(dp.current_user),
    lan_code: str = Depends(dp.get_language),
    session: AsyncSession = Depends(dp.get_db),
):
    values = await srv.read_definitions(user, lan_code, session)
    return values


@router.get(
    '/attitudes',
    response_model=list[sch.AttitudeRead],
    responses=dp.with_common_responses(
        [401, 403], {500: {'description': 'Attitudes not found.'}}
    ),
)
async def get_attitudes(
    user: User = Depends(dp.current_user),
    lan_code: str = Depends(dp.get_language),
    session: AsyncSession = Depends(dp.get_db),
):
    attitudes = await srv.read_attitudes(user, lan_code, session)
    return attitudes


@router.get(
    '/my_values',
    response_model=sch.ProfileValuesRead,
    responses=dp.with_common_responses(
        [401, 403],
        {404: {'description': 'Profile values have not yet been set.'}},
    ),
)
async def get_profile_values(
    user: User = Depends(dp.current_user),
    lan_code: str = Depends(dp.get_language),
    session: AsyncSession = Depends(dp.get_db),
):
    user_values = await srv.read_profile_values(user, lan_code, session)
    return user_values


@router.post(
    '/my_values',
    response_model=sch.ProfileValuesRead,
    responses=dp.with_common_responses(
        [401, 403],
        {
            400: {
                'description': (
                    'Inconsistent polarity/user_order. / '
                    'Incorrect attitude_id. / '
                    'Missing/extra values/aspects.'
                )
            },
            409: {'description': 'Profile values are already set.'},
            500: {
                'description': (
                    'Profile not found. / '
                    'Profile values not found after creation.'
                )
            },
        },
    ),
)
async def post_profile_values(
    *,
    user: User = Depends(dp.current_user),
    lan_code: str = Depends(dp.get_language),
    data: sch.ProfileValuesCreateUpdate,
    session: AsyncSession = Depends(dp.get_db),
):
    await srv.create_profile_values(user, lan_code, data, session)
    return await srv.read_profile_values(user, lan_code, session)


@router.put(
    '/my_values',
    response_model=sch.ProfileValuesRead,
    responses=dp.with_common_responses(
        [401, 403],
        {
            400: {
                'description': (
                    'Inconsistent polarity/user_order. / '
                    'Incorrect attitude_id. / '
                    'Missing/extra values/aspects.'
                )
            },
            404: {'description': 'Profile values have not yet been set.'},
            500: {
                'description': (
                    'Profile not found. / '
                    'Profile values not found after update.'
                )
            },
        },
    ),
)
async def edit_profile_values(
    *,
    user: User = Depends(dp.current_user),
    lan_code: str = Depends(dp.get_language),
    data: sch.ProfileValuesCreateUpdate,
    session: AsyncSession = Depends(dp.get_db),
):
    updated_profile_values = await srv.update_profile_values(
        user, lan_code, data, session
    )
    return updated_profile_values
