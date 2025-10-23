import hashlib
from datetime import datetime
from typing import Sequence
from uuid import UUID

import httpx
from async_lru import alru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, db
from .. import models as md
from ..config import constants as CNST
from ..exceptions import exceptions as exc


async def is_password_pwned(*, password: str) -> bool | None:
    """
    Returns:
        True if password was pwned.
        False if not pwned.
        None if request failed (timeout, network, etc.).
    """
    try:
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f'https://api.pwnedpasswords.com/range/{prefix}'
            )
            response.raise_for_status()

        for line in response.text.splitlines():
            h, _ = line.split(':')
            if h == suffix:
                return True
        return False

    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError):
        return None


async def personal_values_already_set(
    *, my_user: db.User, a_session: AsyncSession
) -> bool:
    pvl_count = await crud.count_personal_values(
        user_id=my_user.id, a_session=a_session
    )
    if pvl_count != 0 and pvl_count != CNST.PERSONAL_VALUE_MAX_ORDER:
        raise exc.ServerError(
            (
                'Found incorrect number of ProfileValues: '
                f'expected {CNST.PERSONAL_VALUE_MAX_ORDER}, found {pvl_count}.'
            )
        )
    return bool(pvl_count)


async def personal_values_to_read_model(
    *, personal_values: Sequence[db.PersonalValue], profile: db.Profile
) -> md.PersonalValuesRead:
    personal_value_models = []
    for pv in sorted(personal_values, key=lambda x: x.user_order):
        personal_aspect_models = [
            md.PersonalAspectRead.model_validate(
                {
                    'aspect_id': pa.aspect_id,
                    'aspect_key_phrase': pa.aspect.key_phrase,
                    'aspect_statement': pa.aspect.statement,
                    'included': pa.included,
                }
            )
            for pa in pv.personal_aspects
        ]
        pv_model = md.PersonalValueRead.model_validate(
            {
                'value_title_id': pv.value_title.id,
                'value_title_name': pv.value_title.name,
                'polarity': pv.polarity,
                'user_order': pv.user_order,
                'aspects': personal_aspect_models,
            }
        )
        personal_value_models.append(pv_model)

    moral_profile_model = md.PersonalValuesRead.model_validate(
        {
            'attitude_id': profile.attitude_id,
            'attitude_statement': profile.attitude.statement,
            'value_links': personal_value_models,
        }
    )
    return moral_profile_model


async def get_uniquevalue_id_by_valuetitle_id_and_aspect_ids(
    *,
    value_title_id: int,
    aspect_ids: list[int],
    a_session: AsyncSession,
) -> int:
    uvs = await crud.read_unique_values(a_session=a_session)
    for uv in uvs:
        if uv.value_title_id == value_title_id and sorted(
            uv.aspect_ids
        ) == sorted(aspect_ids):
            return uv.id
    raise exc.ServerError(
        f'UniqueValue not fount for {value_title_id=}, aspect_ids={aspect_ids}'
    )


@alru_cache
async def get_structure_for_personal_values_input(
    *,
    a_session: AsyncSession,
) -> dict[int, set]:
    expected_structure = {}
    definitions = await crud.read_definitions(a_session=a_session)
    for vt in definitions:
        expected_structure[vt.id] = set([a.id for a in vt.aspects])
    return expected_structure


async def check_personal_values_input(
    *, pv_model: md.PersonalValuesCreateUpdate, a_session: AsyncSession
) -> None:
    pv_model.value_links.sort(key=lambda x: x.user_order)
    polarity_order = {'positive': 1, 'neutral': 2, 'negative': 3}
    poalrity_consistent = all(
        polarity_order[a.polarity] <= polarity_order[b.polarity]
        for a, b in zip(pv_model.value_links, pv_model.value_links[1:])
    )
    if not poalrity_consistent:
        raise exc.BadRequest('Inconsistent polarity/user_order.')
    expected_attitudes = await crud.read_attitudes(a_session=a_session)
    expected_attitude_ids = [attitude.id for attitude in expected_attitudes]
    if pv_model.attitude_id not in expected_attitude_ids:
        raise exc.BadRequest('Incorrect attitude_id.')
    provided_vt_ids = {vl.value_title_id for vl in pv_model.value_links}
    expected_structure = await get_structure_for_personal_values_input(
        a_session=a_session
    )
    expected_vt_ids = set(expected_structure.keys())
    msg_parts = []
    if provided_vt_ids != expected_vt_ids:
        missing = expected_vt_ids - provided_vt_ids
        extra = provided_vt_ids - expected_vt_ids
        if missing:
            msg_parts.append(f'missing values: {missing}')
        if extra:
            msg_parts.append(f'extra values: {extra}')
        if msg_parts:
            raise exc.BadRequest('; '.join(msg_parts))
    for vl_model in pv_model.value_links:
        expected_aspect_ids = expected_structure[vl_model.value_title_id]
        provided_aspect_ids = set([a.aspect_id for a in vl_model.aspects])
        if provided_aspect_ids and provided_aspect_ids != expected_aspect_ids:
            missing = expected_aspect_ids - provided_aspect_ids
            extra = provided_aspect_ids - expected_aspect_ids
            if missing:
                msg_parts.append(f'missing aspects: {missing}')
            if extra:
                msg_parts.append(f'extra aspects: {extra}')
            if msg_parts:
                raise exc.BadRequest('; '.join(msg_parts))


def contact_to_read_model(*, contact: db.Contact) -> md.ContactRead:
    data = {
        'user_id': contact.other_user_id,
        'name': contact.other_user.profile.name,
        'status': contact.status,
        'created_at': contact.created_at,
    }
    return md.ContactRead.model_validate(data)


def contact_request_to_read_model(
    contact: db.Contact,
) -> md.ContactRequestRead:
    data = {
        'user_id': contact.other_user_id,
        'name': contact.other_user.profile.name,
        'status': contact.status,
        'created_at': contact.created_at,
        'time_waiting': datetime.now() - contact.created_at,
    }
    return md.ContactRequestRead.model_validate(data)


async def get_recommendations(
    *,
    my_user_id: UUID,
    other_user_id: UUID | None = None,
    a_session: AsyncSession,
) -> list[md.OtherProfileRead]:
    """Reads user recommendations, wraps to md.OtherProfileRead."""
    recommendations = await crud.read_user_recommendations(
        my_user_id=my_user_id,
        other_user_id=other_user_id,
        a_session=a_session,
    )
    if len(recommendations) > CNST.RECOMMENDATIONS_AT_A_TIME:
        raise exc.ServerError(
            (
                'Inconsistent number of recommendations found for'
                f'{my_user_id}, {other_user_id}.'
            )
        )
    rec_models = [
        md.OtherProfileRead(
            user_id=r.user_id,
            name=r.name,
            similarity_score=r.similarity_score,
            distance_meters=r.distance_meters,
        )
        for r in recommendations
    ]
    return rec_models
