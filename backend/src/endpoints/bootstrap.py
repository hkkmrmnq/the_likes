from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import db
from src import dependencies as dp
from src import schemas as sch
from src import services as srv
from src.config import CFG

router = APIRouter()


@router.get(
    CFG.PATHS.PRIVATE.BOOTSTRAP,
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def bootstrap(
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[sch.Bootstrap]:
    user, asession = user_and_asession
    data, message = await srv.bootstrap(my_user=user, asession=asession)
    return sch.ApiResponse(data=data, message=message)
