from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import dependencies as dp
from .. import models as md
from .. import services as srv
from ..db import User

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
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.DefinitionsRead]:
    definitions_model, msg = await srv.read_definitions(a_session=a_session)
    return md.ApiResponse(data=definitions_model, message=msg)
