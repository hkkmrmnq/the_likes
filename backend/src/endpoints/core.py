from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src.db.user_and_profile import User
from src.models.core import ApiResponse, DefinitionsRead
from src.services import core as core_srv

router = APIRouter()


@router.get(
    '/definitions',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={500: {'description': 'Definitions not found.'}},
    ),
)
async def get_definitions(
    *,
    user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[DefinitionsRead]:
    definitions_model, msg = await core_srv.read_definitions(asession=asession)
    return ApiResponse(data=definitions_model, message=msg)
