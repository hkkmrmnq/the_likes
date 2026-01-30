import pytest
from sqlalchemy import select

from src import db
from src.config import CNST


@pytest.mark.order(1)
async def test_registration(*, client, fixed_user_credentials):
    response = await client.post('/auth/register', json=fixed_user_credentials)
    assert response.status_code == 201
    response_data = response.json()
    assert 'id' in response_data
    assert 'email' in response_data
    assert response_data['email'] == fixed_user_credentials['email']
    assert 'is_active' in response_data
    assert response_data['is_active']
    assert 'is_verified' in response_data
    assert not response_data['is_verified']
    assert 'is_superuser' in response_data
    assert not response_data['is_superuser']


@pytest.mark.order(after='test_registration')
async def test_verification(redis_client, client, fixed_user_credentials):
    msg_content = redis_client.get(
        f'email_to_{fixed_user_credentials["email"]}'
    )
    if not msg_content:
        raise ValueError(
            f'email_to_{fixed_user_credentials["email"]} not found in redis db'
        )
    token = msg_content.split()[-1]
    response = await client.post('/auth/verify', json={'token': token})
    assert response.status_code == 200


@pytest.mark.order(after='test_verification')
async def test_db_user_is_verified(asession, fixed_user_credentials):
    user = await asession.scalar(
        select(db.User).where(db.User.email == fixed_user_credentials['email'])
    )
    assert user is not None
    assert user.is_verified


@pytest.mark.order(after='test_registration')
async def test_login(*, client, fixed_user_credentials) -> str:
    response = await client.post(
        '/auth/jwt/login',
        data={
            'username': fixed_user_credentials['email'],
            'password': fixed_user_credentials['password'],
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert 'access_token' in response_data
    return response_data['access_token']


@pytest.mark.order(-1)
async def test_cleanup(asession, redis_client):
    test_users = await asession.scalars(
        select(db.User).where(db.User.email.startswith('testuser'))
    )
    for user in test_users:
        await asession.delete(user)
    await asession.commit()
    redis_client.delete('celery')
    redis_client.delete(CNST.MATCH_NOTIFIED_REDIS_KEY)
    keys_to_delete = redis_client.keys('email_to_*')
    for k in keys_to_delete:
        redis_client.delete(k)
