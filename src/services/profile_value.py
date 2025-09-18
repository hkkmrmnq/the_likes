from async_lru import alru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from .. import constants as cnst
from .. import crud
from .. import models as md
from .. import schemas as sch
from ..context import set_current_language
from ..exceptions import exceptions as exc
from .core_n_profile import is_active_verified, read_profile


async def profile_values_exist(
    profile: md.Profile, session: AsyncSession
) -> bool:
    pvl_count = await crud.count_profile_value_links(profile, session)
    pv_onelines_count = await crud.count_pv_onelines(profile, session)
    return bool(pvl_count + pv_onelines_count)


async def read_profile_values(
    user: md.User, lan_code: str, session: AsyncSession
) -> sch.ProfileValuesRead:
    is_active_verified(user)
    set_current_language(lan_code)
    profile = await read_profile(user, lan_code, session)
    if not await profile_values_exist(profile, session):
        raise exc.NotFound('Profile values have not yet been set.')
    profile_values = await crud.read_profile_value_links(
        profile, lan_code, session
    )
    return profile_values


@alru_cache
async def get_structure_for_profile_values_input(
    session: AsyncSession,
) -> dict[int, set]:
    expected_structure = {}
    definitions = await crud.read_definitions(cnst.LANGUAGE_DEFAULT, session)
    for vn in definitions:
        expected_structure[vn.id] = set([a.id for a in vn.aspects])
    return expected_structure


async def check_profile_values_input(
    data: sch.ProfileValuesCreateUpdate, session: AsyncSession
) -> None:
    data.value_links.sort(key=lambda x: x.user_order)
    polarity_order = {'positive': 1, 'neutral': 2, 'negative': 3}
    poalrity_consistent = all(
        polarity_order[a.polarity] <= polarity_order[b.polarity]
        for a, b in zip(data.value_links, data.value_links[1:])
    )
    if not poalrity_consistent:
        raise exc.IncorrectBodyStructure('Inconsistent polarity/user_order.')
    expected_attitudes = await crud.read_attitudes(
        cnst.LANGUAGE_DEFAULT, session
    )
    expected_attitude_ids = [attitude.id for attitude in expected_attitudes]
    if data.attitude_id not in expected_attitude_ids:
        raise exc.IncorrectBodyStructure('Incorrect attitude_id.')
    provided_vn_ids = {vl.value_title_id for vl in data.value_links}
    expected_structure = await get_structure_for_profile_values_input(session)
    expected_vn_ids = set(expected_structure.keys())
    msg_parts = []
    if provided_vn_ids != expected_vn_ids:
        missing = expected_vn_ids - provided_vn_ids
        extra = provided_vn_ids - expected_vn_ids
        if missing:
            msg_parts.append(f'missing values: {missing}')
        if extra:
            msg_parts.append(f'extra values: {extra}')
        if msg_parts:
            raise exc.IncorrectBodyStructure('; '.join(msg_parts))
    for vl_schema in data.value_links:
        expected_aspect_ids = expected_structure[vl_schema.value_title_id]
        provided_aspect_ids = set([a.aspect_id for a in vl_schema.aspects])
        if provided_aspect_ids and provided_aspect_ids != expected_aspect_ids:
            missing = expected_aspect_ids - provided_aspect_ids
            extra = provided_aspect_ids - expected_aspect_ids
            if missing:
                msg_parts.append(f'missing aspects: {missing}')
            if extra:
                msg_parts.append(f'extra aspects: {extra}')
            if msg_parts:
                raise exc.IncorrectBodyStructure('; '.join(msg_parts))


async def create_profile_values(
    user: md.User,
    lan_code: str,
    data: sch.ProfileValuesCreateUpdate,
    session: AsyncSession,
) -> sch.ProfileValuesRead:
    is_active_verified(user)
    profile = await read_profile(user, lan_code, session)
    if await profile_values_exist(profile, session):
        raise exc.AlreadyExists('Profile values are already set.')
    await check_profile_values_input(data, session)
    new_value_links = await crud.create_profile_value_links(
        profile, data, session
    )
    await crud.add_pv_oneline(
        attitude_id=data.attitude_id,
        distance_limit=profile.distance_limit,
        profile_values_links=new_value_links,
        session=session,
    )
    await crud.update_profile(user, {'attitude_id': data.attitude_id}, session)
    await session.commit()
    await session.refresh(profile)
    set_current_language(lan_code)
    profile_values = await crud.read_profile_value_links(
        profile, lan_code, session
    )
    if not profile_values.value_links:
        raise exc.ServerError('Profile values not found after creation.')
    return profile_values


async def update_profile_values(
    user: md.User,
    lan_code: str,
    data: sch.ProfileValuesCreateUpdate,
    session: AsyncSession,
) -> sch.ProfileValuesRead:
    is_active_verified(user)
    profile = await read_profile(user, lan_code, session)
    if not await profile_values_exist(profile, session):
        raise exc.NotFound('Profile values have not yet been set.')
    await check_profile_values_input(data, session)
    await crud.delete_profile_value_links(profile, session)
    await crud.delete_pv_oneline(profile.id, session)
    new_value_links = await crud.create_profile_value_links(
        profile, data, session
    )
    await crud.add_pv_oneline(
        attitude_id=data.attitude_id,
        distance_limit=profile.distance_limit,
        profile_values_links=new_value_links,
        session=session,
    )
    await crud.update_profile(user, {'attitude_id': data.attitude_id}, session)
    await session.commit()
    await session.refresh(profile)
    set_current_language(lan_code)
    profile_values = await crud.read_profile_value_links(
        profile, lan_code, session
    )
    if not profile_values.value_links:
        raise exc.ServerError('Profile values not found after update.')
    return profile_values
