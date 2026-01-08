from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src.db.user_and_profile import User
from src.models.bootstrap import Bootstrap
from src.models.core import ApiResponse
from src.services import bootstrap as bootstrap_srv

router = APIRouter()


@router.get(
    '/bootstrap',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def bootstrap(
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[Bootstrap]:
    update, message = await bootstrap_srv.bootstrap(
        my_user=my_user, asession=asession
    )
    return ApiResponse(data=update, message=message)
