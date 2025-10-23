from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, db
from .. import models as md
from ..context import get_current_language
from ..exceptions import exceptions as exc
from . import _utils as utl


async def get_personal_values(
    *, user: db.User, a_session: AsyncSession
) -> tuple[md.PersonalValuesRead, str]:
    profile = await crud.read_profile_by_user_id(
        user_id=user.id, a_session=a_session
    )
    if not await utl.personal_values_already_set(
        my_user=user, a_session=a_session
    ):
        raise exc.NotFound('Profile values have not yet been set.')
    personal_values = await crud.read_personal_values(
        user_id=user.id,
        lan_code=get_current_language(),
        a_session=a_session,
    )
    pv_read_model = await utl.personal_values_to_read_model(
        personal_values=personal_values, profile=profile
    )
    return pv_read_model, 'Personal values.'


async def create_personal_values(
    *,
    my_user: db.User,
    pv_model: md.PersonalValuesCreateUpdate,
    a_session: AsyncSession,
) -> tuple[md.PersonalValuesRead, str]:
    profile = await crud.read_profile_by_user_id(
        user_id=my_user.id, a_session=a_session
    )
    if await utl.personal_values_already_set(
        my_user=my_user, a_session=a_session
    ):
        raise exc.AlreadyExists('Profile values are already set.')
    await utl.check_personal_values_input(
        pv_model=pv_model, a_session=a_session
    )
    ud = await crud.read_user_dynamics(user_id=my_user.id, a_session=a_session)
    ud.values_created = datetime.now()
    await crud.create_personal_values(
        user_id=my_user.id, data=pv_model.model_dump(), a_session=a_session
    )
    await crud.update_profile(
        user_id=my_user.id,
        data={'attitude_id': pv_model.attitude_id},
        a_session=a_session,
    )
    await a_session.commit()
    await a_session.refresh(profile)
    personal_values = await crud.read_personal_values(
        user_id=my_user.id,
        lan_code=get_current_language(),
        a_session=a_session,
    )
    if not personal_values:
        raise exc.ServerError('Personal Values not found after creation.')
    pv_read_model = await utl.personal_values_to_read_model(
        personal_values=personal_values, profile=profile
    )
    message = 'Personal Values set.'
    if not profile.recommend_me:
        message += " Check 'recommend me' option in Profile to enable searh."
    return pv_read_model, message


async def update_personal_values(
    *,
    user: db.User,
    pv_model: md.PersonalValuesCreateUpdate,
    a_session: AsyncSession,
) -> tuple[md.PersonalValuesRead, str]:
    profile = await crud.read_profile_by_user_id(
        user_id=user.id, a_session=a_session
    )
    if not await utl.personal_values_already_set(
        my_user=user, a_session=a_session
    ):
        raise exc.NotFound('Personal Values have not yet been set.')
    await utl.check_personal_values_input(
        pv_model=pv_model, a_session=a_session
    )
    ud = await crud.read_user_dynamics(user_id=user.id, a_session=a_session)
    ud.values_changes = ud.values_changes + [datetime.now()]
    await crud.delete_personal_values(user_id=user.id, a_session=a_session)
    await crud.create_personal_values(
        user_id=user.id, data=pv_model.model_dump(), a_session=a_session
    )
    await crud.update_profile(
        user_id=user.id,
        data={'attitude_id': pv_model.attitude_id},
        a_session=a_session,
    )
    await a_session.commit()
    await a_session.refresh(profile)
    personal_values = await crud.read_personal_values(
        user_id=user.id,
        lan_code=get_current_language(),
        a_session=a_session,
    )
    if not personal_values:
        raise exc.ServerError('Personal Values not found after update.')
    pv_read_model = await utl.personal_values_to_read_model(
        personal_values=personal_values, profile=profile
    )
    message = 'Personal Values updated.'
    if not profile.recommend_me:
        message += " Check 'recommend me' option in Profile to enable searh."
    return pv_read_model, message
