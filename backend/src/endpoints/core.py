from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src import schemas as sch
from src import services as srv
from src.config import CFG

router = APIRouter()


@router.get(
    CFG.PATHS.PUBLIC.DEFINITIONS,
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={500: 'Definitions not found.'},
    ),
)
async def get_definitions(
    *,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.DefinitionsRead]:
    definitions_model, msg = await srv.read_definitions(asession=asession)
    return sch.ApiResponse(data=definitions_model, message=msg)
