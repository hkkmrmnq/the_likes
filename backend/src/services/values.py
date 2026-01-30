from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, db
from src import schemas as sch
from src.context import get_current_language
from src.exceptions import exc
from src.services.utils import other

from .core import read_definitions


async def get_personal_values(
    *, current_user: db.User, asession: AsyncSession
) -> tuple[sch.PersonalValuesRead, str]:
    """
    Reads personal values.
    exc.NotFound raised if no personal values.
    """
    user_language = get_current_language()
    profile = await crud.read_profile_by_user_id(
        user_id=current_user.id,
        user_language=user_language,
        asession=asession,
    )
    attitudes = await crud.read_attitudes(
        user_language=user_language, asession=asession
    )
    message = 'Your values.'
    if not await other.personal_values_already_set(
        my_user=current_user, asession=asession
    ):
        definitions, _ = await read_definitions(asession=asession)
        pv_read_model = await other.values_to_p_v_read_model(
            definitions=definitions
        )
        return (
            pv_read_model,
            'Personal values have not been created yet. '
            'This is initial data to create Personal Values.',
        )

    personal_values = await crud.read_personal_values(
        user_id=current_user.id,
        current_language=user_language,
        asession=asession,
    )
    pv_read_model = await other.personal_values_to_read_model(
        value_links=personal_values, profile=profile, attitudes=attitudes
    )

    if not profile.recommend_me:
        message += " Enable 'recommend me' option in Profile to allow searh."
    return pv_read_model, message


async def create_personal_values(
    *,
    current_user: db.User,
    p_v_model: sch.PersonalValuesCreateUpdate,
    asession: AsyncSession,
) -> tuple[sch.PersonalValuesRead, str]:
    """
    Creates personal values. If aready set - raises AlreadyExists.
    Checks input for consistency.
    Updates UserDynamic accordingly.
    Updates Profile with attitude_id.
    """
    if await other.personal_values_already_set(
        my_user=current_user, asession=asession
    ):
        raise exc.AlreadyExists('Profile values are already set.')
    await other.check_personal_values_input(
        p_v_model=p_v_model, asession=asession
    )
    ud = await crud.read_user_dynamics(
        user_id=current_user.id, asession=asession
    )
    ud.values_created = datetime.now()
    await crud.create_personal_values(
        user_id=current_user.id, data=p_v_model.model_dump(), asession=asession
    )
    await crud.update_profile(
        user_id=current_user.id,
        data={'attitude_id': p_v_model.attitude_id},
        asession=asession,
    )
    await asession.commit()
    pv_read_model, _ = await get_personal_values(
        current_user=current_user, asession=asession
    )
    return pv_read_model, 'Personal Values set.'


async def update_personal_values(
    *,
    current_user: db.User,
    p_v_model: sch.PersonalValuesCreateUpdate,
    asession: AsyncSession,
) -> tuple[sch.PersonalValuesRead, str]:
    """
    Updates personal values. If not yet set - raises NotFound.
    Checks input for consistency.
    Updates UserDynamic accordingly.
    Updates Profile with attitude_id.
    """

    if not await other.personal_values_already_set(
        my_user=current_user, asession=asession
    ):
        raise exc.NotFound('Personal Values have not yet been set.')
    await other.check_personal_values_input(
        p_v_model=p_v_model, asession=asession
    )
    ud = await crud.read_user_dynamics(
        user_id=current_user.id, asession=asession
    )
    ud.values_changes = ud.values_changes + [datetime.now()]
    await crud.delete_personal_values(
        user_id=current_user.id, asession=asession
    )
    await crud.create_personal_values(
        user_id=current_user.id, data=p_v_model.model_dump(), asession=asession
    )
    await crud.update_profile(
        user_id=current_user.id,
        data={'attitude_id': p_v_model.attitude_id},
        asession=asession,
    )
    await asession.commit()
    pv_read_model, message = await get_personal_values(
        current_user=current_user, asession=asession
    )
    message = message.replace('Your values.', 'Personal Values updated.')
    return pv_read_model, message
