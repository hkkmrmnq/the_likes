from uuid import UUID

from fastapi import status
from geoalchemy2.shape import to_shape
from httpx import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, db
from src.config import CFG
from src.services.utils import generate_random_personal_values


async def test_get_profile(client, unique_db_user):
    access_token = unique_db_user['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get(
        CFG.PATHS.PRIVATE.PROFILE,
        headers=headers,
    )
    assert response.status_code == 200, f'{response.content}'


async def test_edit_profile(client, unique_db_user, asession_fixture):
    input_data = {
        'longitude': 125,
        'latitude': 29,
        'distance_limit': 1111.11,
        'name': 'test name',
        'languages': ['ru'],
        'recommend_me': False,
    }
    access_token = unique_db_user['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.put(
        CFG.PATHS.PRIVATE.PROFILE,
        json=input_data,
        headers=headers,
    )
    assert response.status_code == 200, f'{response.content}'
    response_data = response.json()
    db_profile = await asession_fixture.scalar(
        select(db.Profile).where(db.Profile.user_id == unique_db_user['id'])
    )
    await asession_fixture.refresh(db_profile)
    assert (
        str(to_shape(db_profile.location))
        == f'POINT ({input_data["longitude"]} {input_data["latitude"]})'
    )
    assert 'data' in response_data
    response_profile = response_data['data']
    assert 'user_id' in response_profile
    assert response_profile['user_id'] == str(unique_db_user['id'])
    assert 'name' in response_profile
    assert response_profile['name'] == input_data['name']
    assert 'languages' in response_profile
    assert response_profile['languages'] == input_data['languages']
    assert 'distance_limit' in response_profile
    assert response_profile['distance_limit'] == input_data['distance_limit']
    assert 'recommend_me' in response_profile
    assert response_profile['recommend_me'] == input_data['recommend_me']
    assert 'longitude' in response_profile
    assert response_profile['longitude'] == input_data['longitude']
    assert 'latitude' in response_profile
    assert response_profile['latitude'] == input_data['latitude']
    assert db_profile.name == input_data['name']
    assert db_profile.languages == input_data['languages']
    assert db_profile.distance_limit == input_data['distance_limit']
    assert db_profile.recommend_me == input_data['recommend_me']


async def check_personal_values(
    *,
    input_data: dict,
    user_id: UUID,
    response: Response,
    asession: AsyncSession,
):
    sent_personal_values = sorted(
        input_data['value_links'], key=lambda x: x['user_order']
    )
    response_payload = response.json()
    assert 'data' in response_payload
    response_data = response_payload['data']
    assert 'initial' in response_data
    assert isinstance(response_data['initial'], bool)
    assert 'attitudes' in response_data
    attitudes = response_data['attitudes']
    for attitude in attitudes:
        assert 'attitude_id' in attitude
        assert 'statement' in attitude
        assert 'chosen' in attitude
    chosen_attitude_ids = [a['attitude_id'] for a in attitudes if a['chosen']]
    assert len(chosen_attitude_ids) == 1, (
        'Exactly one attitude_id expected. '
        f'Got {len(chosen_attitude_ids)}: '
        f'{", ".join([str(i) for i in chosen_attitude_ids])}.'
    )
    chosen_attitude_id = chosen_attitude_ids[0]
    assert chosen_attitude_id == input_data['attitude_id']
    assert 'value_links' in response_data
    returned_personal_values = response_data['value_links']
    for p_v in returned_personal_values:
        assert 'user_order' in p_v
    returned_personal_values = sorted(
        returned_personal_values, key=lambda x: x['user_order']
    )
    assert len(returned_personal_values) == CFG.PERSONAL_VALUE_MAX_ORDER
    db_profile = await asession.scalar(
        select(db.Profile).where(db.Profile.user_id == user_id)
    )
    assert db_profile is not None
    db_personal_values_result = await crud.read_personal_values(
        user_id=user_id, asession=asession
    )
    assert db_personal_values_result is not None
    db_personal_values = list(db_personal_values_result)
    assert len(db_personal_values) == CFG.PERSONAL_VALUE_MAX_ORDER
    for ind in range(CFG.PERSONAL_VALUE_MAX_ORDER):
        sent_pv = sent_personal_values[ind]
        returned_pv = returned_personal_values[ind]
        db_pv = db_personal_values[ind]
        assert 'value_id' in returned_pv
        assert 'value_name' in returned_pv
        assert 'polarity' in returned_pv
        assert sent_pv['value_id'] == returned_pv['value_id'] == db_pv.value_id
        assert returned_pv['value_name'] == db_pv.value.name
        assert sent_pv['polarity'] == returned_pv['polarity'] == db_pv.polarity
        assert (
            sent_pv['user_order']
            == returned_pv['user_order']
            == db_pv.user_order
        )


async def test_create_personal_values(
    unique_db_user,
    client,
    asession_fixture,
    redis_client,
):
    input_data = await generate_random_personal_values(
        asession=asession_fixture
    )
    redis_client.set('create', f'{input_data}')
    access_token = unique_db_user['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.post(
        CFG.PATHS.PRIVATE.VALUES,
        json=input_data,
        headers=headers,
    )
    assert response.status_code == status.HTTP_201_CREATED, (
        f'{response.content}'
    )
    await check_personal_values(
        input_data=input_data,
        user_id=unique_db_user['id'],
        response=response,
        asession=asession_fixture,
    )


async def test_edit_personal_values(
    db_user_with_personal_values,
    client,
    asession_fixture,
    redis_client,
):
    input_data = await generate_random_personal_values(
        asession=asession_fixture
    )
    redis_client.set('edit', f'{input_data}')
    access_token = db_user_with_personal_values['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.put(
        CFG.PATHS.PRIVATE.VALUES,
        json=input_data,
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK, f'{response.content}'
    await check_personal_values(
        input_data=input_data,
        user_id=db_user_with_personal_values['id'],
        response=response,
        asession=asession_fixture,
    )
