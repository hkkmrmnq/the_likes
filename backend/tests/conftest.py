from uuid import uuid4

import pytest
import pytest_asyncio
import redis
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from src.config.config import CFG
from src.db.core import UniqueValue
from src.db.personal_values import PersonalAspect, PersonalValue
from src.db.user_and_profile import Profile
from src.dependencies import get_jwt_strategy
from src.exceptions.exceptions import ServerError
from src.services._utils import generate_random_personal_values
from src.services.user_manager import _create_user


@pytest_asyncio.fixture
async def asession():
    asession_factory = async_sessionmaker(
        create_async_engine(CFG.ASYNC_DATABASE_URL, echo=True),
        expire_on_commit=False,
    )
    async with asession_factory() as asession:
        yield asession


@pytest_asyncio.fixture
async def second_asession():
    asession_factory = async_sessionmaker(
        create_async_engine(CFG.ASYNC_DATABASE_URL, echo=True),
        expire_on_commit=False,
    )
    async with asession_factory() as asession:
        yield asession


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        base_url=CFG.BACKEND_ORIGIN,
        timeout=15,
    ) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def second_client():
    async with AsyncClient(
        base_url=CFG.BACKEND_ORIGIN,
        timeout=15,
    ) as test_client:
        yield test_client


@pytest.fixture
def unique_user_credentials():
    return {
        'email': f'testuser{uuid4()}@example.com',
        'password': f'{uuid4()}'.replace('-', ''),
    }


@pytest.fixture
def second_unique_user_credentials():
    return {
        'email': f'testuser{uuid4()}@example.com',
        'password': f'{uuid4()}'.replace('-', ''),
    }


@pytest.fixture
def fixed_user_credentials():
    return {
        'email': 'testuser@example.com',
        'password': 'testuserpass33t454l7m90mb37',
    }


async def create_access_token(db_user):
    strategy = get_jwt_strategy()
    token = await strategy.write_token(db_user)
    return token


@pytest_asyncio.fixture
async def unique_db_user(asession, second_unique_user_credentials):
    user = await _create_user(
        email=second_unique_user_credentials['email'],
        password=second_unique_user_credentials['password'],
        is_verified=True,
        asession=asession,
    )
    try:
        yield {
            'id': user.id,
            'username': user.email,
            'password': second_unique_user_credentials['password'],
            'access_token': await create_access_token(user),
        }
    except Exception as e:
        raise e
    finally:
        await asession.delete(user)
        await asession.commit()


@pytest.fixture
def redis_client():
    return redis.Redis(
        host=CFG.REDIS_HOST,
        port=CFG.REDIS_PORT,
        db=CFG.REDIS_DB,
        decode_responses=True,
    )


@pytest_asyncio.fixture
async def db_user_with_personal_values(asession, unique_db_user):
    result = await asession.scalars(select(UniqueValue))
    db_unique_values = list(result.all())
    if not db_unique_values:
        raise ServerError('No UniqueValues in DB.')
    input_data = await generate_random_personal_values(asession=asession)
    await asession.execute(
        update(Profile)
        .where(Profile.user_id == unique_db_user['id'])
        .values({'attitude_id': input_data['attitude_id']})
    )
    personal_values = []
    value_links = input_data['value_links']
    for pv_input in value_links:
        aspect_links = [
            PersonalAspect(**al, user_id=unique_db_user['id'])
            for al in pv_input.pop('aspects')
        ]
        value_link = PersonalValue(
            **pv_input,
            personal_aspects=aspect_links,
            user_id=unique_db_user['id'],
        )
        sorted_aspect_ids = set([a.aspect_id for a in aspect_links])
        for uv in db_unique_values:
            if (
                uv.value_id == pv_input['value_id']
                and set(uv.aspect_ids) == sorted_aspect_ids
            ):
                value_link.unique_value_id = uv.id
                break
        else:
            raise ServerError(
                f'UniqueValue not fount for {value_link.value_id=}, '
                f'aspect_ids={sorted_aspect_ids}'
            )
        personal_values.append(value_link)
    asession.add_all(personal_values)
    await asession.commit()
    return unique_db_user
