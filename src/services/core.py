from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src import models as md


async def read_definitions(
    *, a_session: AsyncSession
) -> tuple[md.DefinitionsRead, str]:
    attitudes = await crud.read_attitudes(a_session=a_session)
    values = await crud.read_definitions(a_session=a_session)
    def_model = md.DefinitionsRead(
        attitudes=[md.AttitudeRead.model_validate(a) for a in attitudes],
        values=[md.ValueTitleRead.model_validate(v) for v in values],
    )
    return def_model, 'Definitions.'
