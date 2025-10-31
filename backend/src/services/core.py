from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src import exceptions as exc
from src import models as md


async def read_definitions(
    *, a_session: AsyncSession
) -> tuple[md.DefinitionsRead, str]:
    """
    Reads Attitudes, Values and Aspects.
    Returns DefinitionsRead schema.
    """
    attitudes = await crud.read_attitudes(a_session=a_session)
    if not attitudes:
        raise exc.ServerError('Attitudes not found.')
    definitions = await crud.read_definitions(a_session=a_session)
    if not definitions:
        raise exc.ServerError('Definitions not found.')
    def_model = md.DefinitionsRead(
        attitudes=[md.AttitudeRead.model_validate(a) for a in attitudes],
        values=[md.ValueRead.model_validate(v) for v in definitions],
    )
    return def_model, 'Definitions.'
