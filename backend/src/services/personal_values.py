from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.context import get_current_language
from src.db.user_and_profile import User
from src.exceptions import exceptions as exc
from src.models.personal_values import (
    PersonalValuesCreateUpdate,
    PersonalValuesRead,
)
from src.services import _utils as utl


async def get_personal_values(
    *, user: User, asession: AsyncSession
) -> tuple[PersonalValuesRead, str]:
    """
    Reads personal values.
    exc.NotFound raised if no personal values.
    """
    user_language = get_current_language()
    profile = await crud.read_profile_by_user_id(
        user_id=user.id,
        user_language=user_language,
        asession=asession,
    )
    if not await utl.personal_values_already_set(
        my_user=user, asession=asession
    ):
        raise exc.NotFound('Profile values have not yet been set.')
    personal_values = await crud.read_personal_values(
        user_id=user.id,
        current_language=user_language,
        asession=asession,
    )
    pv_read_model = await utl.personal_values_to_read_model(
        personal_values=personal_values, profile=profile
    )
    message = 'Personal values.'
    if not profile.recommend_me:
        message += " Enable 'recommend me' option in Profile to allow searh."
    return pv_read_model, message


async def create_personal_values(
    *,
    my_user: User,
    pv_model: PersonalValuesCreateUpdate,
    asession: AsyncSession,
) -> tuple[PersonalValuesRead, str]:
    """
    Creates personal values. If aready set - raises AlreadyExists.
    Checks input for consistency.
    Updates UserDynamic accordingly.
    Updates Profile with attitude_id.
    """
    if await utl.personal_values_already_set(
        my_user=my_user, asession=asession
    ):
        raise exc.AlreadyExists('Profile values are already set.')
    await utl.check_personal_values_input(
        personal_values_md=pv_model, asession=asession
    )
    ud = await crud.read_user_dynamics(user_id=my_user.id, asession=asession)
    ud.values_created = datetime.now()
    await crud.create_personal_values(
        user_id=my_user.id, data=pv_model.model_dump(), asession=asession
    )
    await crud.update_profile(
        user_id=my_user.id,
        data={'attitude_id': pv_model.attitude_id},
        asession=asession,
    )
    await asession.commit()
    pv_read_model, message = await get_personal_values(
        user=my_user, asession=asession
    )
    message = message.replace('Personal values.', 'Personal Values set.')
    return pv_read_model, message


async def update_personal_values(
    *,
    my_user: User,
    pv_model: PersonalValuesCreateUpdate,
    asession: AsyncSession,
) -> tuple[PersonalValuesRead, str]:
    """
    Updates personal values. If not yet set - raises NotFound.
    Checks input for consistency.
    Updates UserDynamic accordingly.
    Updates Profile with attitude_id.
    """

    if not await utl.personal_values_already_set(
        my_user=my_user, asession=asession
    ):
        raise exc.NotFound('Personal Values have not yet been set.')
    await utl.check_personal_values_input(
        personal_values_md=pv_model, asession=asession
    )
    ud = await crud.read_user_dynamics(user_id=my_user.id, asession=asession)
    ud.values_changes = ud.values_changes + [datetime.now()]
    await crud.delete_personal_values(user_id=my_user.id, asession=asession)
    await crud.create_personal_values(
        user_id=my_user.id, data=pv_model.model_dump(), asession=asession
    )
    await crud.update_profile(
        user_id=my_user.id,
        data={'attitude_id': pv_model.attitude_id},
        asession=asession,
    )
    await asession.commit()
    pv_read_model, message = await get_personal_values(
        user=my_user, asession=asession
    )
    message = message.replace('Personal values.', 'Personal Values updated.')
    return pv_read_model, message
