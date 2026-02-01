import pytest
from sqlalchemy import select

from src import db
from src.config import CFG, CNST


@pytest.mark.order(1)
async def test_registration(*, client, fixed_user_credentials):
    response = await client.post(
        CFG.PATHS.PUBLIC.REGISTER, json=fixed_user_credentials
    )
    assert response.status_code == 200
    response_data = response.json()
    assert 'data' in response_data
    assert response_data['data']
    assert isinstance(response_data['data'], str)
    assert response_data['data'] == fixed_user_credentials['email']


@pytest.mark.order(after='test_registration')
async def test_verification(redis_client, client, fixed_user_credentials):
    email = fixed_user_credentials['email']
    redis_key = f'{CNST.CONFIRM_EMAIL_REDIS_KEY}{email}'
    redis_data = redis_client.hgetall(redis_key)
    assert redis_data, f'{email} validation data not found in redis.'
    assert 'code' in redis_data, 'Unexpected email validation data structure.'
    code = redis_data['code']
    response = await client.post(
        CFG.PATHS.PUBLIC.VERIFY_EMAIL, json={'email': email, 'code': int(code)}
    )
    assert response.status_code == 200


@pytest.mark.order(after='test_verification')
async def test_db_user_is_verified(asession_fixture, fixed_user_credentials):
    user = await asession_fixture.scalar(
        select(db.User).where(db.User.email == fixed_user_credentials['email'])
    )
    assert user is not None
    assert user.is_verified


@pytest.mark.order(after='test_registration')
async def test_login(*, client, fixed_user_credentials):
    response = await client.post(
        CFG.PATHS.PUBLIC.LOGIN,
        json={
            'email': fixed_user_credentials['email'],
            'password': fixed_user_credentials['password'],
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert 'data' in response_data
    assert 'access_token' in response_data['data']


@pytest.mark.order(-1)
async def test_cleanup(asession_fixture, redis_client):
    test_users = await asession_fixture.scalars(
        select(db.User).where(db.User.email.startswith('testuser'))
    )
    for user in test_users:
        await asession_fixture.delete(user)
    await asession_fixture.commit()
    redis_client.delete('celery')
    redis_client.delete(CNST.MATCH_NOTIFIED_REDIS_KEY)
    keys_to_delete = redis_client.keys('email_to_*')
    for k in keys_to_delete:
        redis_client.delete(k)
