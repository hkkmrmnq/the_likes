import hashlib
import json
import random
from datetime import datetime, timezone
from uuid import UUID

import httpx
from async_lru import alru_cache
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.config.config import CFG
from src.config.enums import Polarity
from src.containers import RichContact
from src.db.contact_n_message import Contact
from src.db.core import Attitude
from src.db.personal_values import PersonalValue
from src.db.user_and_profile import Profile, User
from src.exceptions import exceptions as exc
from src.logger import logger
from src.models.contact_n_message import (
    ContactRead,
    ContactRequestRead,
    ContactRichRead,
    OtherProfileRead,
)
from src.models.core import DefinitionsRead
from src.models.personal_values import (
    PersonalAspectRead,
    PersonalAttitude,
    PersonalValueRead,
    PersonalValuesCreateUpdate,
    PersonalValuesRead,
)
from src.models.user_and_profile import ProfileRead, ProfileUpdate


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
    *, my_user: User, asession: AsyncSession
) -> bool:
    pvl_count = await crud.count_personal_values(
        user_id=my_user.id, asession=asession
    )
    if pvl_count != 0 and pvl_count != CFG.PERSONAL_VALUE_MAX_ORDER:
        raise exc.ServerError(
            (
                'Found incorrect number of ProfileValues: '
                f'expected {CFG.PERSONAL_VALUE_MAX_ORDER}, found {pvl_count}.'
            )
        )
    return bool(pvl_count)


def profile_to_read_model(profile: Profile) -> ProfileRead:
    longitude: float | None = None
    latitude: float | None = None
    if profile.location is not None:
        if not isinstance(profile.location, WKBElement):
            raise exc.ServerError(
                'profile.location: expected WKBElement, '
                f'got {profile.location} type {type(profile.location)}'
            )
        geom = to_shape(profile.location)
        if not isinstance(geom, Point):
            raise exc.ServerError(
                'Point instance expected after to_shape(profile.location), '
                f'got {profile.location} type {type(profile.location)}'
            )
        longitude = geom.x
        latitude = geom.y
    return ProfileRead.model_validate(
        {
            'name': profile.name,
            'languages': profile.languages,
            'distance_limit': profile.distance_limit,
            'recommend_me': profile.recommend_me,
            'latitude': latitude,
            'longitude': longitude,
        }
    )


def profile_model_to_write_data(model: ProfileUpdate) -> dict:
    location: str | None = None

    if all((model.longitude, model.latitude)):
        location = f'POINT({model.longitude} {model.latitude})'

    return {
        'name': model.name,
        'languages': model.languages,
        'distance_limit': model.distance_limit,
        'recommend_me': model.recommend_me,
        'location': location,
    }


async def personal_values_to_read_model(
    *,
    value_links: list[PersonalValue],
    attitudes: list[Attitude],
    profile: Profile,
) -> PersonalValuesRead:
    """Prepares PersonalValuesRead schema based on existing personal values."""
    personal_value_models = []
    for pv in sorted(value_links, key=lambda x: x.user_order):
        personal_aspect_models = [
            PersonalAspectRead.model_validate(
                {
                    'aspect_id': pa.aspect_id,
                    'aspect_key_phrase': pa.aspect.key_phrase,
                    'aspect_statement': pa.aspect.statement,
                    'included': pa.included,
                }
            )
            for pa in pv.personal_aspects
        ]
        pv_model = PersonalValueRead.model_validate(
            {
                'value_id': pv.value.id,
                'value_name': pv.value.name,
                'polarity': pv.polarity,
                'user_order': pv.user_order,
                'aspects': personal_aspect_models,
            }
        )
        personal_value_models.append(pv_model)

    personal_attitudes = [
        PersonalAttitude(
            attitude_id=a.id,
            statement=a.statement,
            chosen=a.id == profile.attitude_id,
        )
        for a in attitudes
    ]

    moral_profile_model = PersonalValuesRead.model_validate(
        {
            'initial': False,
            'attitudes': personal_attitudes,
            'value_links': personal_value_models,
        }
    )
    return moral_profile_model


async def values_to_p_v_read_model(
    definitions: DefinitionsRead,
) -> PersonalValuesRead:
    """
    Prepares PersonalValuesRead schema for user to choose initially.
    Intended to use in sutuation when a user creates Personal Values.
    values:  Values with prefetched Aspects;
    attitudes: db Attitudes.
    """
    personal_value_models = []
    dummy_order = 0
    for value in definitions.values:
        dummy_order += 1
        personal_aspect_models = [
            PersonalAspectRead.model_validate(
                {
                    'aspect_id': aspect.id,
                    'aspect_key_phrase': aspect.key_phrase,
                    'aspect_statement': aspect.statement,
                    'included': False,
                }
            )
            for aspect in value.aspects
        ]
        pv_model = PersonalValueRead.model_validate(
            {
                'value_id': value.id,
                'value_name': value.name,
                'polarity': Polarity.NEUTRAL,
                'user_order': dummy_order,
                'aspects': personal_aspect_models,
            }
        )
        personal_value_models.append(pv_model)

    attitudes = [
        PersonalAttitude(attitude_id=a.id, statement=a.statement, chosen=False)
        for a in definitions.attitudes
    ]
    personal_values_model = PersonalValuesRead.model_validate(
        {
            'initial': True,
            'attitudes': attitudes,
            'value_links': personal_value_models,
        }
    )
    return personal_values_model


@alru_cache(maxsize=512)
async def get_schema_for_pesonal_values_input(
    *,
    asession: AsyncSession,
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
    attitudes = await crud.read_attitudes(asession=asession)
    if not attitudes:
        raise exc.ServerError('Attitudes not found.')
    schema = {'attitude_ids': set(), 'definitions': {}}
    schema['attitude_ids'] = set([att.id for att in attitudes])
    definitions = await crud.read_values(asession=asession)
    if not definitions:
        raise exc.ServerError('Definitions not found.')
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
    p_v_model: PersonalValuesCreateUpdate,
    asession: AsyncSession,
):
    """Checks PersonalValuesCreateUpdate on consistency."""
    p_v_model.value_links.sort(key=lambda x: x.user_order)
    polarity_order = {'positive': 1, 'neutral': 2, 'negative': 3}
    poalrity_consistent = all(
        polarity_order[a.polarity] <= polarity_order[b.polarity]
        for a, b in zip(p_v_model.value_links, p_v_model.value_links[1:])
    )
    if not poalrity_consistent:
        raise exc.BadRequest('Inconsistent polarity/user_order.')
    provided_value_ids = {vl.value_id for vl in p_v_model.value_links}
    schema = await get_schema_for_pesonal_values_input(asession=asession)
    # chosen_attitude_ids = [
    #     a.attitude_id for a in p_v_model.attitudes if a.chosen
    # ]
    # if len(chosen_attitude_ids) != 1:
    #     raise exc.BadRequest(
    #         'Exactly one attitude_id expected. Got attitude_ids: '
    #         f'{", ".join([str(i) for i in chosen_attitude_ids])}.'
    #     )
    # chosen_attitude_id = chosen_attitude_ids[0]
    if p_v_model.attitude_id not in schema['attitude_ids']:
        raise exc.BadRequest(
            f'Incorrect attitude_id: {p_v_model.attitude_id}.'
        )
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
    for value_link_md in p_v_model.value_links:
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


def contact_to_read_model(
    *, contact: Contact, unread_msg_count: int | None = None
) -> ContactRead:
    """Prepares ContactRead schema."""
    data = {
        'user_id': contact.other_user_id,
        'status': contact.status,
        'unread_messages': unread_msg_count,
        'created_at': contact.created_at,
        'name': contact.other_user.profile.name,
    }
    return ContactRead.model_validate(data)


def rich_contact_to_read_model(*, contact: RichContact) -> ContactRichRead:
    """Prepares ContactRichRead schema."""
    data = {
        'user_id': contact.other_user_id,
        'name': contact.my_name,
        'status': contact.status,
        'created_at': contact.created_at,
        'distance': contact.distance,
        'similarity': contact.similarity,
        'unread_messages': contact.unread_msg,
    }

    return ContactRichRead.model_validate(data)


def contact_request_to_read_model(
    *,
    contact: Contact,
) -> ContactRequestRead:
    """Prepares ContactRequestRead schema."""
    data = {
        'user_id': contact.other_user_id,
        'name': contact.other_user.profile.name,
        'status': contact.status,
        'created_at': contact.created_at,
        'time_waiting': datetime.now(timezone.utc) - contact.created_at,
    }
    return ContactRequestRead.model_validate(data)


async def get_recommendations(
    *,
    my_user_id: UUID,
    other_user_id: UUID | None = None,
    asession: AsyncSession,
) -> list[OtherProfileRead]:
    """Reads user recommendations, returns as OtherProfileRead schema."""
    recommendations = await crud.read_user_recommendations(
        my_user_id=my_user_id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if len(recommendations) > CFG.RECOMMENDATIONS_AT_A_TIME:
        raise exc.ServerError(
            (
                'Inconsistent number of recommendations found for'
                f'{my_user_id}, {other_user_id}.'
            )
        )
    rec_models = [
        OtherProfileRead(
            user_id=r.user_id,
            name=r.name,
            similarity=r.similarity_score,
            distance=r.distance,
        )
        for r in recommendations
    ]
    return rec_models


def _randomize_personal_values(*, schema: dict):
    order_choices = [n for n in range(1, CFG.PERSONAL_VALUE_MAX_ORDER + 1)]
    input = {
        'attitude_id': random.choice(list(schema['attitude_ids'])),
        'value_links': [],
    }
    polarity = 'positive'
    polarity_change_options = [0] + order_choices + [(order_choices[-1] + 1)]
    two_choices = [
        random.choice(polarity_change_options),
        random.choice(polarity_change_options),
    ]
    switch_to_neutral, switch_to_negative = sorted(two_choices)
    value_ids = list(schema['definitions'])
    random.shuffle(value_ids)
    for order in order_choices:
        value_id = value_ids[order - 1]
        aspect_ids = schema['definitions'][value_id]
        input_aspects = [
            {'aspect_id': a_id, 'included': random.choice((True, False))}
            for a_id in aspect_ids
        ]
        if order == switch_to_neutral:
            polarity = 'neutral'
        if order == switch_to_negative:
            polarity = 'negative'
        input['value_links'].append(
            {
                'value_id': value_id,
                'polarity': polarity,
                'user_order': order,
                'aspects': input_aspects,
            }
        )
        order += 1
    return input


async def generate_random_personal_values(*, asession: AsyncSession) -> dict:
    """
    Generates random personal values input.
    Displays as JSON formatted str.
    Returns as dict.
    """
    schema = await get_schema_for_pesonal_values_input(asession=asession)
    pv_dict = _randomize_personal_values(schema=schema)
    pv_str = json.dumps(pv_dict)
    print(pv_str)
    return pv_dict
