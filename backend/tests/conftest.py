from uuid import uuid4

import pytest
import pytest_asyncio
import redis
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from src import crud, db
from src import services as srv
from src.config import CFG
from src.exceptions import exc
from src.services.utils import create_access_token


@pytest_asyncio.fixture
async def asession_fixture():
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


@pytest_asyncio.fixture
async def unique_db_user(asession_fixture, second_unique_user_credentials):
    email = second_unique_user_credentials['email']
    await srv.utl.user.create_user(
        email=email,
        password=second_unique_user_credentials['password'],
        is_verified=True,
        asession=asession_fixture,
    )
    user = await crud.read_user_by_email(
        email=email, asession=asession_fixture
    )
    if user is None:
        raise
    try:
        yield {
            'id': user.id,
            'email': user.email,
            'password': second_unique_user_credentials['password'],
            'access_token': create_access_token(user.id),
        }
    except Exception:
        raise exc.ServerError(
            'unique_db_user fixture: test user not found after creation.'
        )
    finally:
        await asession_fixture.delete(user)
        await asession_fixture.commit()


@pytest.fixture
def redis_client():
    return redis.Redis(
        host=CFG.REDIS_HOST,
        port=CFG.REDIS_PORT,
        db=CFG.REDIS_DB,
        decode_responses=True,
    )


@pytest_asyncio.fixture
async def db_user_with_personal_values(asession_fixture, unique_db_user):
    result = await asession_fixture.scalars(select(db.UniqueValue))
    db_unique_values = list(result.all())
    if not db_unique_values:
        raise exc.ServerError('No UniqueValues in DB.')
    input_data = await srv.utils.generate_random_personal_values(
        asession=asession_fixture
    )
    await asession_fixture.execute(
        update(db.Profile)
        .where(db.Profile.user_id == unique_db_user['id'])
        .values({'attitude_id': input_data['attitude_id']})
    )
    personal_values = []
    value_links = input_data['value_links']
    for pv_input in value_links:
        aspect_links = [
            db.PersonalAspect(**al, user_id=unique_db_user['id'])
            for al in pv_input.pop('aspects')
        ]
        value_link = db.PersonalValue(
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
            raise exc.ServerError(
                f'UniqueValue not fount for {value_link.value_id=}, '
                f'aspect_ids={sorted_aspect_ids}'
            )
        personal_values.append(value_link)
    asession_fixture.add_all(personal_values)
    await asession_fixture.commit()
    return unique_db_user
