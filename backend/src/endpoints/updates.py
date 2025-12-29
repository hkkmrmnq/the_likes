from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src.db.user_and_profile import User
from src.models.core import ApiResponse
from src.models.update import UpdateRead
from src.services import update as update_srv

router = APIRouter()


@router.get(
    '/update',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_update(
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[UpdateRead]:
    update, message = await update_srv.get_update(
        my_user=my_user, asession=asession
    )
    return ApiResponse(data=update, message=message)
