from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src import models as md
from src import services as srv
from src.db import User

router = APIRouter()


@router.get(
    '/update',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_update(
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.Update]:
    update, message = await srv.get_update(
        my_user=my_user, a_session=a_session
    )
    return md.ApiResponse(data=update, message=message)


@router.get(
    '/full_update',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_full_update(
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.FullUpdate]:
    update, message = await srv.get_full_update(
        my_user=my_user, a_session=a_session
    )
    return md.ApiResponse(data=update, message=message)
