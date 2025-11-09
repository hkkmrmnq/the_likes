from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.context import get_current_language
from src.exceptions import exceptions as exc
from src.models.core import AttitudeRead, DefinitionsRead, ValueRead


async def read_definitions(
    *, asession: AsyncSession
) -> tuple[DefinitionsRead, str]:
    """
    Reads Attitudes, Values and Aspects.
    Returns DefinitionsRead schema.
    """
    attitudes = await crud.read_attitudes(
        user_language=get_current_language(), asession=asession
    )
    if not attitudes:
        raise exc.ServerError('Attitudes not found.')
    definitions = await crud.read_definitions(
        user_language=get_current_language(), asession=asession
    )
    if not definitions:
        raise exc.ServerError('Definitions not found.')
    def_model = DefinitionsRead(
        attitudes=[AttitudeRead.model_validate(a) for a in attitudes],
        values=[ValueRead.model_validate(v) for v in definitions],
    )
    return def_model, 'Definitions.'
