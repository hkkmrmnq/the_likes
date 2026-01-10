from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src import schemas as sch
from src.context import get_current_language
from src.exceptions import exceptions as exc


async def read_definitions(
    *, asession: AsyncSession
) -> tuple[sch.DefinitionsRead, str]:
    """
    Reads Attitudes, Values and Aspects.
    Returns DefinitionsRead schema.
    """
    attitudes = await crud.read_attitudes(
        user_language=get_current_language(), asession=asession
    )
    if not attitudes:
        raise exc.ServerError('Attitudes not found.')
    definitions = await crud.read_values(
        user_language=get_current_language(), asession=asession
    )
    if not definitions:
        raise exc.ServerError('Definitions not found.')
    def_model = sch.DefinitionsRead(
        attitudes=[sch.AttitudeRead.model_validate(a) for a in attitudes],
        values=[sch.ValueRead.model_validate(v) for v in definitions],
    )
    return def_model, 'Definitions.'
