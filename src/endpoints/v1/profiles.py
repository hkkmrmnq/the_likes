from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ... import dependencies as dp
from ... import schemas as sch
from ... import services as srv
from ...models import User

router = APIRouter()


@router.get(
    '/profile',
    response_model=sch.ProfileRead,
    responses=dp.with_common_responses(
        [401, 403], {500: {'description': 'Profile not found.'}}
    ),
)
async def get_profile(
    user: User = Depends(dp.current_user),
    lan_code: str = Depends(dp.get_language),
    session: AsyncSession = Depends(dp.get_db),
):
    profile = await srv.read_profile(user, lan_code, session)
    return profile


@router.put(
    '/profile',
    response_model=sch.ProfileRead,
    responses=dp.with_common_responses(
        [401, 403],
        {
            400: {'description': "Can't set distance_limit without location."},
            500: {'description': 'Profile not found.'},
        },
    ),
)
async def edit_profile(
    *,
    current_user: User = Depends(dp.current_user),
    lan_code: str = Depends(dp.get_language),
    update_schema: sch.ProfileUpdate,
    session: AsyncSession = Depends(dp.get_db),
):
    profile = await srv.update_profile(
        current_user, lan_code, update_schema, session
    )
    return profile
