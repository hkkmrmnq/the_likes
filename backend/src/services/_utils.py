import hashlib
from datetime import datetime
from typing import Sequence
from uuid import UUID

import httpx
from async_lru import alru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, db
from src import models as md
from src.config import CFG
from src.exceptions import exceptions as exc
from src.logger import logger


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

    except (
        httpx.RequestError,
        httpx.TimeoutException,
        httpx.HTTPStatusError,
    ) as e:
        logger.error(e)
        return None


async def personal_values_already_set(
    *, my_user: db.User, a_session: AsyncSession
) -> bool:
    pvl_count = await crud.count_personal_values(
        user_id=my_user.id, a_session=a_session
    )
    if pvl_count != 0 and pvl_count != CFG.PERSONAL_VALUE_MAX_ORDER:
        raise exc.ServerError(
            (
                'Found incorrect number of ProfileValues: '
                f'expected {CFG.PERSONAL_VALUE_MAX_ORDER}, found {pvl_count}.'
            )
        )
    return bool(pvl_count)


async def personal_values_to_read_model(
    *, personal_values: Sequence[db.PersonalValue], profile: db.Profile
) -> md.PersonalValuesRead:
    """Prepares PersonalValuesRead schema."""
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
                'value_id': pv.value.id,
                'value_name': pv.value.name,
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


@alru_cache
async def get_schema_for_pesonal_values_input(
    *,
    a_session: AsyncSession,
) -> dict:
    """
    Returns structured sorted available attitudes, values
    and aspect ids for personal values input to compare with.
    Aka:
    {
    'attitude_ids': {1, 2, 3},
    'definitions': {
        1: {1, 2},  # value id: aspect ids
        2: {3, 4},
        ...
        }
    }
    """
    attitudes = await crud.read_attitudes(a_session=a_session)
    schema = {'attitude_ids': set(), 'definitions': {}}
    schema['attitude_ids'] = set([att.id for att in attitudes])
    definitions = await crud.read_definitions(a_session=a_session)
    if not definitions:
        raise exc.ServerError('definitions not found.')
    for v in definitions:
        schema['definitions'][v.id] = set([a.id for a in v.aspects])
    keys = sorted(schema['definitions'].keys())
    result = {}
    for k in keys:
        result[k] = schema['definitions'][k]
    schema['definitions'] = result
    return schema


async def check_personal_values_input(
    *,
    personal_values_md: md.PersonalValuesCreateUpdate,
    a_session: AsyncSession,
) -> None:
    """Performs complex PersonalValuesCreateUpdate validation."""
    personal_values_md.value_links.sort(key=lambda x: x.user_order)
    polarity_order = {'positive': 1, 'neutral': 2, 'negative': 3}
    poalrity_consistent = all(
        polarity_order[a.polarity] <= polarity_order[b.polarity]
        for a, b in zip(
            personal_values_md.value_links, personal_values_md.value_links[1:]
        )
    )
    if not poalrity_consistent:
        raise exc.BadRequest('Inconsistent polarity/user_order.')
    expected_attitudes = await crud.read_attitudes(a_session=a_session)
    if not expected_attitudes:
        raise exc.ServerError('Attitudes not found.')
    expected_attitude_ids = [attitude.id for attitude in expected_attitudes]
    if personal_values_md.attitude_id not in expected_attitude_ids:
        raise exc.BadRequest('Incorrect attitude_id.')
    provided_value_ids = {vl.value_id for vl in personal_values_md.value_links}
    schema = await get_schema_for_pesonal_values_input(a_session=a_session)
    expected_value_ids = set(schema['definitions'].keys())
    message_parts = []
    if provided_value_ids != schema['definitions']:
        missing = expected_value_ids - provided_value_ids
        extra = provided_value_ids - expected_value_ids
        if missing:
            message_parts.append(f'missing values: {missing}')
        if extra:
            message_parts.append(f'extra values: {extra}')
        if message_parts:
            raise exc.BadRequest('; '.join(message_parts))
    for value_link_md in personal_values_md.value_links:
        expected_aspect_ids = schema['definitions'][value_link_md.value_id]
        provided_aspect_ids = set([a.aspect_id for a in value_link_md.aspects])
        if provided_aspect_ids != expected_aspect_ids:
            missing = expected_aspect_ids - provided_aspect_ids
            extra = provided_aspect_ids - expected_aspect_ids
            if missing:
                message_parts.append(f'missing aspects: {missing}')
            if extra:
                message_parts.append(f'extra aspects: {extra}')
            if message_parts:
                raise exc.BadRequest('; '.join(message_parts))


def contact_to_read_model(*, contact: db.Contact) -> md.ContactRead:
    """Prepares ContactRead schema."""
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
    """Prepares ContactRequestRead schema."""
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
    """Reads user recommendations, wraps to OtherProfileRead schema."""
    recommendations = await crud.read_user_recommendations(
        my_user_id=my_user_id,
        other_user_id=other_user_id,
        a_session=a_session,
    )
    if len(recommendations) > CFG.RECOMMENDATIONS_AT_A_TIME:
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
